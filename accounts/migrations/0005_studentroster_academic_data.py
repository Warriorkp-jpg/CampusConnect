from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ('accounts', '0004_user_company_phone_studentroster'),
    ]

    operations = [
        migrations.AddField(
            model_name='studentroster',
            name='cgpa',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=4),
        ),
        migrations.AddField(
            model_name='studentroster',
            name='backlogs',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
