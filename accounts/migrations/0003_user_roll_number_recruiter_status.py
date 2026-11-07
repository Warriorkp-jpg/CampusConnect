from django.db import migrations, models


def migrate_existing_roles(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(role='ADMIN').update(role='TPO')
    User.objects.filter(role='RECRUITER').update(recruiter_status='PENDING')


def reverse_existing_roles(apps, schema_editor):
    User = apps.get_model('accounts', 'User')
    User.objects.filter(role='TPO').update(role='ADMIN')
    User.objects.filter(role='RECRUITER').update(recruiter_status='NOT_REQUIRED')


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_backlogs_user_cgpa'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='roll_number',
            field=models.CharField(blank=True, max_length=30, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='user',
            name='recruiter_status',
            field=models.CharField(
                choices=[
                    ('NOT_REQUIRED', 'Not required'),
                    ('PENDING', 'Pending approval'),
                    ('APPROVED', 'Approved'),
                    ('REJECTED', 'Rejected'),
                ],
                default='NOT_REQUIRED',
                max_length=20,
            ),
        ),
        migrations.AlterField(
            model_name='user',
            name='role',
            field=models.CharField(
                choices=[
                    ('TPO', 'Training and Placement Officer'),
                    ('RECRUITER', 'Recruiter'),
                    ('STUDENT', 'Student'),
                ],
                default='STUDENT',
                max_length=9,
            ),
        ),
        migrations.RunPython(migrate_existing_roles, reverse_existing_roles),
    ]
