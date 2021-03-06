# Generated by Django 2.0.2 on 2018-02-19 21:22

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('projections', '0002_auto_20180209_1721'),
    ]

    operations = [
        migrations.AlterField(
            model_name='batterprojection',
            name='pos',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=200), blank=True, size=None),
        ),
        migrations.AlterField(
            model_name='battervalue',
            name='pos',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=200), blank=True, size=None),
        ),
        migrations.AlterField(
            model_name='pitcherprojection',
            name='pos',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=200), blank=True, size=None),
        ),
        migrations.AlterField(
            model_name='pitchervalue',
            name='pos',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(max_length=200), blank=True, size=None),
        ),
    ]
