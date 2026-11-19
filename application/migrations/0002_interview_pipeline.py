import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('application', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='application',
            name='status',
            field=models.CharField(
                choices=[
                    ('APPLIED', 'Applied'),
                    ('SHORTLISTED', 'Shortlisted'),
                    ('INTERVIEW', 'Interview'),
                    ('REJECTED', 'Rejected'),
                    ('SELECTED', 'Selected'),
                ],
                default='APPLIED',
                max_length=15,
            ),
        ),
        migrations.AddField(
            model_name='application',
            name='updated_at',
            field=models.DateTimeField(auto_now=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='application',
            name='interview_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='application',
            name='interview_mode',
            field=models.CharField(blank=True, choices=[('ONLINE', 'Online'), ('IN_PERSON', 'In person')], max_length=12),
        ),
    ]
