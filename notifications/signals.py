from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Notification
from users.models import Follow
from chat.models import ChatMessage, GroupMessage
from posts.models import Post, Comment, Reaction
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
import re

User = get_user_model()

@receiver(post_save, sender=ChatMessage)
def notify_private_message(sender, instance, created, **kwargs):
    if created and instance.receiver:
        Notification.objects.bulk_create([
            Notification(
                recipient=instance.receiver,
                sender=instance.sender,
                notification_type="chat",
                related_content_type=ContentType.objects.get_for_model(instance),
                related_object_id=instance.id
            )
        ])

@receiver(post_save, sender=GroupMessage)
def notify_group_message(sender, instance, created, **kwargs):
    if created:
        group_members = instance.group.members.all()
        group_supervisors = instance.group.supervisors.all()
        
        print("👥 Group Members:", [u.username for u in group_members])
        print("👨‍🏫 Supervisors:", [u.username for u in group_supervisors])

        recipients = (group_members | group_supervisors).distinct().exclude(id=instance.sender.id)
        print("📩 Recipients:", [u.username for u in recipients])

        notifications = [
            Notification(
                recipient=member,
                sender=instance.sender,
                notification_type="group_chat",
                related_content_type=ContentType.objects.get_for_model(instance),
                related_object_id=instance.id,
            )
            for member in recipients
        ]
        Notification.objects.bulk_create(notifications)


# @receiver(post_save, sender=Follow)
# def notify_follow(sender, instance, created, **kwargs):
#     if created:
#         Notification.objects.create(
#             recipient=instance.following, 
#             sender=instance.follower,  
#             notification_type="follow", 
#             related_content_type=ContentType.objects.get_for_model(instance),
#             related_object_id=instance.id
#         )

@receiver(post_save, sender=Post)
def notify_followers_on_new_post(sender, instance, created, **kwargs):
    if created:
        author = instance.author
        followers = Follow.objects.filter(following=author).select_related('follower')

        notifications = [
            Notification(
                recipient=f.follower,
                sender=author,
                notification_type="new_post",
                related_content_type=ContentType.objects.get_for_model(Post),
                related_object_id=instance.id
            )
            for f in followers if f.follower != author  
        ]

        Notification.objects.bulk_create(notifications)


# @receiver(post_save, sender=Comment)
# def notify_post_author_on_comment(sender, instance, created, **kwargs):
#     if created and instance.post.author != instance.author: 
#         Notification.objects.create(
#             recipient=instance.post.author,
#             sender=instance.author,
#             notification_type="comment",
#             related_content_type=ContentType.objects.get_for_model(instance),
#             related_object_id=instance.id
#         )
@receiver(post_save, sender=Comment)
def notify_post_author_on_comment(sender, instance, created, **kwargs):
    if not created:
        return

    author = instance.author
    post_author = instance.post.author


    mentioned_usernames = extract_mentions(instance.comment)
    mentioned_users = User.objects.filter(username__in=mentioned_usernames)

    
    if mentioned_users.exists():
        notifications = [
            Notification(
                recipient=user,
                sender=author,
                notification_type="mention",
                related_content_type=ContentType.objects.get_for_model(instance),
                related_object_id=instance.id
            )
            for user in mentioned_users if user != author
        ]
        Notification.objects.bulk_create(notifications)

    elif post_author != author:
        Notification.objects.create(
            recipient=post_author,
            sender=author,
            notification_type="comment",
            related_content_type=ContentType.objects.get_for_model(instance),
            related_object_id=instance.id
        )

def extract_mentions(text):
    print("🧪 extract_mentions called with text:", text)
    return set(re.findall(r'@([\w\.-]+)', text))

@receiver(post_save, sender=Post)
# @receiver(post_save, sender=Comment)
def notify_mentioned_users(sender, instance, created, **kwargs):
    try:
        print("🚀 Signal triggered for:", instance)
        if created:
            if isinstance(instance, Post):
                text = instance.body
            # elif isinstance(instance, Comment):
            #     text = instance.comment
            else:
                print("⚠️ Not Post or Comment instance")
                return

            mentioned_usernames = extract_mentions(text)
            print("📛 Mentioned usernames:", mentioned_usernames)

            mentioned_users = User.objects.filter(username__in=mentioned_usernames)
            print("👤 Mentioned users found:", list(mentioned_users))

            notifications = [
                Notification(
                    recipient=user,
                    sender=instance.author,
                    notification_type="mention", 
                    related_content_type=ContentType.objects.get_for_model(instance),
                    related_object_id=instance.id
                )
                for user in mentioned_users if user != instance.author
            ]
            Notification.objects.bulk_create(notifications)
            print("✅ Notifications created:", notifications)
    except Exception as e:
        print("❌ Error in mention signal:", e)

        
@receiver(post_save, sender=Follow)
def notify_follow(sender, instance, created, **kwargs):
    # If the Follow instance is newly created
    if created:
        # Send a 'follow' notification
        Notification.objects.create(
            recipient=instance.following,
            sender=instance.follower,
            notification_type="follow",
            related_content_type=ContentType.objects.get_for_model(instance),
            related_object_id=instance.id
        )

@receiver(post_delete, sender=Follow)
def notify_unfollow(sender, instance, **kwargs):
    # Send an 'unfollow' notification when the follow relationship is deleted
    Notification.objects.create(
        recipient=instance.following,
        sender=instance.follower,
        notification_type="unfollow",
        related_content_type=ContentType.objects.get_for_model(instance),
        related_object_id=instance.id
    )

@receiver(post_save, sender=Reaction)
def notify_reaction(sender, instance, created, **kwargs):
    if created:
        if instance.post and instance.post.author != instance.user:
            Notification.objects.create(
                recipient=instance.post.author,
                sender=instance.user,
                notification_type="reaction",
                reaction_type=instance.reaction_type,
                related_content_type=ContentType.objects.get_for_model(instance),
                related_object_id=instance.id
            )
        elif instance.comment and instance.comment.author != instance.user:
            Notification.objects.create(
                recipient=instance.comment.author,
                sender=instance.user,
                notification_type="reaction",
                reaction_type=instance.reaction_type,
                related_content_type=ContentType.objects.get_for_model(instance),
                related_object_id=instance.id
            )

@receiver(post_delete, sender=Reaction)
def remove_reaction_notification(sender, instance, **kwargs):
    Notification.objects.filter(
    sender=instance.user,
    related_object_id=instance.id,
    related_content_type=ContentType.objects.get_for_model(instance)
    ).delete()
