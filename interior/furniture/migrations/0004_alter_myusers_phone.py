# Generated by Django 5.0.6 on 2025-04-02 16:18

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('furniture', '0003_alter_myusers_phone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myusers',
            name='phone',
            field=models.CharField(blank=True, max_length=25, null=True, unique=True),
        ),
    ]
