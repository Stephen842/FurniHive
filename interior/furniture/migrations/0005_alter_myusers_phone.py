# Generated by Django 5.0.6 on 2025-04-03 09:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('furniture', '0004_alter_myusers_phone'),
    ]

    operations = [
        migrations.AlterField(
            model_name='myusers',
            name='phone',
            field=models.CharField(default='0000000000', max_length=25, unique=True),
        ),
    ]
