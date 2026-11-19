from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0007_studentprofile'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=120)),
                ('message', models.CharField(max_length=500)),
                ('category', models.CharField(choices=[('GENERAL', 'General'), ('APPLICATION', 'Application'), ('RECRUITER', 'Recruiter'), ('PLACEMENT', 'Placement')], default='GENERAL', max_length=20)),
                ('is_read', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='accounts.user')),
            ],
            options={
                'ordering': ('-created_at',),
                'indexes': [
                    models.Index(fields=['user', 'is_read', 'created_at'], name='accounts_notif_user_read_idx'),
                ],
            },
        ),
    ]
