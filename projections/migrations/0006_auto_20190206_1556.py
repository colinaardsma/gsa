# Generated by Django 2.1.5 on 2019-02-06 15:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projections', '0005_auto_20180219_2215'),
    ]

    operations = [
        migrations.AddField(
            model_name='batterprojection',
            name='originalValue',
            field=models.FloatField(default=0.0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='battervalue',
            name='originalValue',
            field=models.FloatField(default=0.0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='pitcherprojection',
            name='originalValue',
            field=models.FloatField(default=0.0),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='pitchervalue',
            name='originalValue',
            field=models.FloatField(default=0.0),
            preserve_default=False,
        ),
    ]