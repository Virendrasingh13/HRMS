# Generated by Django 5.2.1 on 2025-06-26 03:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0007_alter_country_code'),
    ]

    operations = [
        migrations.AlterField(
            model_name='companydocument',
            name='status',
            field=models.CharField(choices=[('Approve', 'Approve'), ('Under Review', 'Under Review'), ('Rejected', 'Rejected')], default='Under Review', max_length=15),
        ),
        migrations.AlterField(
            model_name='employeedocument',
            name='status',
            field=models.CharField(choices=[('Approve', 'Approve'), ('Under Review', 'Under Review'), ('Rejected', 'Rejected')], default='Under Review', max_length=15),
        ),
    ]
