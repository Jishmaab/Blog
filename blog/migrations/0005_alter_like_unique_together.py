# Generated by Django 4.2.7 on 2023-12-01 05:27

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0004_alter_notification_id'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='like',
            unique_together={('author', 'post')},
        ),
    ]
