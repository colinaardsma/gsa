# Generated by Django 2.0.2 on 2018-02-16 20:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leagues', '0007_auto_20180208_1911'),
    ]

    operations = [
        migrations.AddField(
            model_name='league',
            name='status',
            field=models.CharField(default='blah', max_length=200),
            preserve_default=False,
        ),
    ]
