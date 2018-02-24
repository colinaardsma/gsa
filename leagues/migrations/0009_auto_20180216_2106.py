# Generated by Django 2.0.2 on 2018-02-16 21:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leagues', '0008_league_status'),
    ]

    operations = [
        migrations.RenameField(
            model_name='league',
            old_name='status',
            new_name='draft_status',
        ),
        migrations.AddField(
            model_name='league',
            name='end_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='league',
            name='start_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]