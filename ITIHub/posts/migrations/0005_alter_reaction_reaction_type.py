# Generated by Django 5.1.7 on 2025-04-04 13:18

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("posts", "0004_alter_reaction_reaction_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="reaction",
            name="reaction_type",
            field=models.CharField(
                choices=[
                    ("Like", "Like"),
                    ("Love", "Love"),
                    ("Celebrate", "Celebrate"),
                    ("Laugh", "Laugh"),
                    ("Insightful", "Insightful"),
                    ("Support", "Support"),
                ],
                max_length=10,
            ),
        ),
    ]
