from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('drive', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='drive',
            name='description',
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name='drive',
            name='location',
            field=models.CharField(blank=True, max_length=150),
        ),
        migrations.AddField(
            model_name='drive',
            name='application_deadline',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='drive',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
