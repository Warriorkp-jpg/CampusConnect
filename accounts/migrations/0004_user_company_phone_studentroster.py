from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0003_user_roll_number_recruiter_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='company_name',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='user',
            name='phone_number',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.CreateModel(
            name='StudentRoster',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('roll_number', models.CharField(max_length=30, unique=True)),
                ('full_name', models.CharField(max_length=150)),
                ('college_email', models.EmailField(blank=True, max_length=254)),
                ('program', models.CharField(default='B.Tech CSE', max_length=100)),
                ('batch', models.CharField(blank=True, max_length=20)),
                ('added_at', models.DateTimeField(auto_now_add=True)),
                ('student_user', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='roster_record', to='accounts.user')),
            ],
        ),
    ]
