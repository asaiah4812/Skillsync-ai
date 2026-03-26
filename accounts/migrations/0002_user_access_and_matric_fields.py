from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='has_listed_skill',
            field=models.BooleanField(
                default=False,
                help_text='True when the student has listed at least one skill.',
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='matriculation_number',
            field=models.CharField(blank=True, max_length=30, null=True, unique=True),
        ),
        migrations.AddField(
            model_name='user',
            name='subscription_active',
            field=models.BooleanField(
                default=False,
                help_text='True when learner access subscription is active.',
            ),
        ),
        migrations.AddField(
            model_name='user',
            name='subscription_expires_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
