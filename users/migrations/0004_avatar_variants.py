from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('users', '0003_follow'),
    ]

    operations = [
        migrations.AddField(
            model_name='customuser',
            name='avatar_sm',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='avatar_md',
            field=models.URLField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='avatar_lg',
            field=models.URLField(blank=True, null=True),
        ),
    ]
