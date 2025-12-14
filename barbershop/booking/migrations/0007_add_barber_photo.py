from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('booking', '0006_userprofile'),
    ]

    operations = [
        migrations.AddField(
            model_name='barber',
            name='photo',
            field=models.ImageField(blank=True, null=True, upload_to='barbers/', validators=[django.core.validators.FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]),
        ),
    ]
