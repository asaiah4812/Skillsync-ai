from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_access_and_matric_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='expected_graduation_year',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
    ]

