# Generated by Django 5.0.1 on 2024-01-31 08:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('account', '0006_disease_category'),
    ]

    operations = [
        migrations.AlterField(
            model_name='disease',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='disease/'),
        ),
    ]