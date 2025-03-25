import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.contenttypes.models import ContentType
from .models import Notification
from chat.models import ChatMessage, GroupMessage
from posts.models import Post, Comment , Reaction
from django.contrib.auth import get_user_model

User = get_user_model()


@receiver(post_save, sender=ChatMessage)
def notify_private_message(sender, instance, created, **kwargs):
    if created and instance.receiver:
        Notification.objects.create(
            recipient=instance.receiver,
            notification_type="chat",
            related_object_id=instance.id,
            # related_object_type=ContentType.objects.get_for_model(ChatMessage)
        )   

@receiver(post_save, sender=GroupMessage)
def notify_group_message(sender, instance, created, **kwargs):
    if created:
        group_members = instance.group.members.exclude(id=instance.sender.id) 

        for member in group_members:
            Notification.objects.create(
                recipient=member,
                notification_type="group_chat",
                related_object_id=instance.id, 
                # related_object_type=ContentType.objects.get_for_model(GroupMessage)
            )







# @receiver(post_save, sender=Post)
# def notify_new_post(sender, instance, created, **kwargs):
#     if created:
#         followers = instance.author.followers.all()
#         for follower in followers:
#             Notification.objects.create(
#                 recipient=follower,
#                 sender=instance.author,
#                 notification_type="new_post",
#                 content_type=ContentType.objects.get_for_model(instance),
#                 object_id=instance.id
#             )


# @receiver(post_save, sender=Comment)
# def notify_comment(sender, instance, created, **kwargs):
#     if created and instance.post.author != instance.author:
#         Notification.objects.create(
#             recipient=instance.post.author,
#             sender=instance.author,
#             notification_type="comment",
#             content_type=ContentType.objects.get_for_model(instance),
#             object_id=instance.id
#         )

# @receiver(post_save, sender=Reaction)  # Reaction model should be defined in posts/models.py
# def notify_reaction(sender, instance, created, **kwargs):
#     if created and instance.post.author != instance.user:
#         Notification.objects.create(
#             recipient=instance.post.author,
#             sender=instance.user,
#             notification_type="reaction",
#             content_type=ContentType.objects.get_for_model(instance),
#             object_id=instance.id
#         )

# @receiver(post_save, sender=User)
# def notify_follow(sender, instance, created, **kwargs):
#     if created:
#         for follower in instance.followers.all():
#             Notification.objects.create(
#                 recipient=follower,
#                 sender=instance,
#                 notification_type="follow",
#                 content_type=ContentType.objects.get_for_model(instance),
#                 object_id=instance.id
#             )
