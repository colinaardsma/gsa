# Generated by Django 2.0.2 on 2018-02-06 15:36

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('leagues', '0004_auto_20180206_1449'),
    ]

    operations = [
        migrations.RenameField(
            model_name='profile',
            old_name='yahooGuid',
            new_name='yahoo_guid',
        ),
    ]
