from django.conf import settings
from django.db import models


class Calculation(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="calculations"
    )
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    rate = models.DecimalField(max_digits=6, decimal_places=2)
    time = models.PositiveIntegerField()
    result = models.DecimalField(max_digits=16, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.amount} for {self.time} years"


class AffiliateClick(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="affiliate_clicks",
    )
    source = models.CharField(max_length=255)
    utm_source = models.CharField(max_length=120, blank=True, default="")
    utm_medium = models.CharField(max_length=120, blank=True, default="")
    utm_campaign = models.CharField(max_length=120, blank=True, default="")
    utm_content = models.CharField(max_length=120, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} - {self.source}"


class Lead(models.Model):
    email = models.EmailField()
    source = models.CharField(max_length=120, blank=True, default="")
    utm_source = models.CharField(max_length=120, blank=True, default="")
    utm_medium = models.CharField(max_length=120, blank=True, default="")
    utm_campaign = models.CharField(max_length=120, blank=True, default="")
    utm_content = models.CharField(max_length=120, blank=True, default="")
    consent_given = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.email
