from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Notification
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
        group_members = instance.group.members.exclude(id=instance.sender.id)
        notifications = [
            Notification(
                recipient=member,
                sender=instance.sender,
                notification_type="group_chat",
                related_object_id=instance.id
            )
            for member in group_members
        ]
        Notification.objects.bulk_create(notifications)

@receiver(post_save, sender=Post)
def notify_followers_on_new_post(sender, instance, created, **kwargs):
    if created:
        followers = instance.author.followers.all()
        notifications = [
            Notification(
                recipient=follower,
                sender=instance.author,
                notification_type="new_post",
                related_content_type=ContentType.objects.get_for_model(instance),
                related_object_id=instance.id
            )
            for follower in followers
        ]
        Notification.objects.bulk_create(notifications)

@receiver(post_save, sender=Comment)
def notify_post_author_on_comment(sender, instance, created, **kwargs):
    if created and instance.post.author != instance.author: 
        Notification.objects.create(
            recipient=instance.post.author,
            sender=instance.author,
            notification_type="comment",
            related_content_type=ContentType.objects.get_for_model(instance),
            related_object_id=instance.id
        )

def extract_mentions(text):
    return set(re.findall(r'@([\w.-]+)', text))  

@receiver(post_save, sender=Post)
@receiver(post_save, sender=Comment)
def notify_mentioned_users(sender, instance, created, **kwargs):
    if created:
        if isinstance(instance, Post):
            text = instance.body  
        elif isinstance(instance, Comment):
            text = instance.comment  
        else:
            return  

        mentioned_usernames = extract_mentions(text) 
        mentioned_users = User.objects.filter(username__in=mentioned_usernames)

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
