# Generated by Django 5.1.7 on 2025-04-02 14:16

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('notification_type', models.CharField(choices=[('reaction', 'Reaction'), ('comment', 'Comment'), ('new_post', 'New Post'), ('mention', 'Mention'), ('message', 'Message'), ('chat', 'Chat'), ('group_chat', 'Group Chat'), ('follow', 'Follow'), ('batch_assignment', 'Batch Assignment'), ('batch_end', 'Batch End')], max_length=20)),
                ('reaction_type', models.CharField(blank=True, choices=[('like', 'Like'), ('love', 'Love'), ('haha', 'Haha'), ('wow', 'Wow'), ('sad', 'Sad'), ('angry', 'Angry')], max_length=10, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('is_read', models.BooleanField(default=False)),
                ('related_object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL)),
                ('related_content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('sender', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='sent_notifications', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
