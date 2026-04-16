from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="affiliateclick",
            name="utm_campaign",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="affiliateclick",
            name="utm_content",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="affiliateclick",
            name="utm_medium",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="affiliateclick",
            name="utm_source",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="lead",
            name="consent_given",
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name="lead",
            name="source",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="lead",
            name="utm_campaign",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="lead",
            name="utm_content",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="lead",
            name="utm_medium",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
        migrations.AddField(
            model_name="lead",
            name="utm_source",
            field=models.CharField(blank=True, default="", max_length=120),
        ),
    ]
