# Generated by Django 5.1.7 on 2025-04-03 00:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='password_reset_code',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='user',
            name='reset_code_expiry',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
