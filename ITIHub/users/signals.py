from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from chat.models import GroupChat
from batches.models import Batch, StudentBatch
from .models import Profile

#from django.contrib.auth.models import User ---> instead we will import the custom user model
from .models import User

User = get_user_model()


# signal to when supervisor creates a batch, a group chat is created for the batch and the supervisor is added as an admin
@receiver(post_save, sender=Batch)
def create_group_chat_for_batch(sender, instance, created, **kwargs):
    if created and instance.supervisor:
        chat_name = f"Batch {instance.name} Chat"
        
        # Check if a chat with this name already exists before creating a new one
        if not GroupChat.objects.filter(name=chat_name).exists():
            group_chat = GroupChat.objects.create(name=chat_name)
            group_chat.supervisors.add(instance.supervisor)
            group_chat.save()



@receiver(post_save, sender=User)
def add_user_to_batch_chat(sender, instance, **kwargs):
    if instance.is_active and instance.is_student:
        # Ensure the user has a related Student instance
        if hasattr(instance, "student_profile"):  
            student = instance.student_profile  # Get related Student instance
            student_batch = StudentBatch.objects.filter(student=student).last()
            
            if student_batch:
                # Get the group chat for the batch
                group_chat = GroupChat.objects.filter(batches=student_batch.batch).first()
                if group_chat:
                    group_chat.members.add(instance)  # Add student to the group chat
                    group_chat.save()  # Save the group chat

# =====================================================================================================================

# Create a profile when a new user is created
def createProfile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.get_or_create(  # Ensures no duplicate profile is created
            user=instance,
            defaults={
                # this will copy the common data(attributes) from the user model to the profile model
                'username': instance.username,
                'email': instance.email,
                'first_name': instance.first_name,
                'last_name': instance.last_name,
            }
        )

# Update the user when the profile is updated
def updateProfile(sender, instance, created, **kwargs):
    if not created:  # Prevent updates during profile creation
        user = instance.user
        user.first_name = instance.first_name
        user.last_name = instance.last_name
        user.username = instance.username
        user.email = instance.email
        user.save()

# Delete the user when their profile is deleted
def deleteProfile(sender, instance, **kwargs):
    user = instance.user
    if user:  # Avoid deleting the user twice
        user.delete()

# Connect signals
post_save.connect(createProfile, sender=User)
post_save.connect(updateProfile, sender=Profile)
post_delete.connect(deleteProfile, sender=Profile)
