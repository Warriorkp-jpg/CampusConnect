import uuid

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0005_studentroster_academic_data'),
    ]

    operations = [
        migrations.CreateModel(
            name='StudentEmailOTP',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('challenge_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True)),
                ('roll_number', models.CharField(max_length=30)),
                ('code_hash', models.CharField(max_length=128)),
                ('expires_at', models.DateTimeField()),
                ('attempts', models.PositiveSmallIntegerField(default=0)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('consumed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'ordering': ('-created_at',),
                'indexes': [
                    models.Index(fields=['roll_number', 'created_at'], name='accounts_st_roll_n_7d3c1a_idx'),
                    models.Index(fields=['challenge_id', 'expires_at'], name='accounts_st_challe_7a0a44_idx'),
                ],
            },
        ),
    ]
