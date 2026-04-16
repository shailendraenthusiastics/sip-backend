from django.contrib import admin
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from core.views import (
    CurrentUserView,
    CustomTokenObtainPairView,
    ExportAffiliateClicksCSVView,
    ExportLeadsCSVView,
    LeadCaptureView,
    MonetizationSummaryView,
    SIPCalculateView,
    SignupView,
    TrackAffiliateView,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/users/me/", CurrentUserView.as_view(), name="current-user"),
    path("api/users/signup/", SignupView.as_view(), name="signup"),
    path("api/token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("api/sip/", SIPCalculateView.as_view(), name="sip-calculate"),
    path("api/track/", TrackAffiliateView.as_view(), name="affiliate-track"),
    path("api/lead/", LeadCaptureView.as_view(), name="lead-capture"),
    path(
        "api/analytics/summary/",
        MonetizationSummaryView.as_view(),
        name="analytics-summary",
    ),
    path(
        "api/analytics/export/clicks/",
        ExportAffiliateClicksCSVView.as_view(),
        name="analytics-export-clicks",
    ),
    path(
        "api/analytics/export/leads/",
        ExportLeadsCSVView.as_view(),
        name="analytics-export-leads",
    ),
]
