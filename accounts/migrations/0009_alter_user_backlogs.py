from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0008_notification'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='backlogs',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
