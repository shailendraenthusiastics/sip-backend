from django.contrib import admin

from .models import AffiliateClick, Calculation, Lead


@admin.register(Calculation)
class CalculationAdmin(admin.ModelAdmin):
    list_display = ("user", "amount", "rate", "time", "result", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "user__email")


@admin.register(AffiliateClick)
class AffiliateClickAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "source",
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("user__username", "source", "utm_source", "utm_campaign")


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    list_display = (
        "email",
        "source",
        "utm_source",
        "utm_campaign",
        "consent_given",
        "created_at",
    )
    list_filter = ("created_at",)
    search_fields = ("email", "source", "utm_source", "utm_campaign")
