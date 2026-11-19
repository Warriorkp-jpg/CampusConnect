from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('drive', '0002_drive_details_and_deadline'),
    ]

    operations = [
        migrations.AlterField(
            model_name='drive',
            name='max_backlogs',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
