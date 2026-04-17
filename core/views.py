from decimal import Decimal, ROUND_HALF_UP
from datetime import timedelta
import csv

from django.db import IntegrityError
from django.http import HttpResponse
from django.db.models import Count
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import AffiliateClick, Calculation, Lead
from .serializers import (
    AffiliateClickSerializer,
    CalculationSerializer,
    CustomTokenObtainPairSerializer,
    LeadSerializer,
    SIPRequestSerializer,
    SignupSerializer,
)


def calculate_sip_future_value(monthly_investment, annual_interest_rate, years):
    monthly_rate = (Decimal(annual_interest_rate) / Decimal("100")) / Decimal("12")
    months = years * 12

    if monthly_rate == 0:
        return monthly_investment * Decimal(months)

    one_plus_r = Decimal("1") + monthly_rate
    future_value = (
        monthly_investment
        * ((one_plus_r**months - Decimal("1")) / monthly_rate)
        * one_plus_r
    )
    return future_value


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = serializer.save()
        except IntegrityError:
            return Response(
                {"detail": "A user with this username or email already exists."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(
            {
                "message": "Account created successfully.",
                "user": {"id": user.id, "username": user.username, "email": user.email},
            },
            status=status.HTTP_201_CREATED,
        )


class CustomTokenObtainPairView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CustomTokenObtainPairSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)


class CurrentUserView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        return Response(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "is_staff": user.is_staff,
            }
        )


class ApiIndexView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response(
            {
                "status": "ok",
                "message": "StableMoney API is running.",
                "endpoints": {
                    "health": "/api/health/",
                    "signup": "/api/users/signup/",
                    "login": "/api/token/",
                    "token_refresh": "/api/token/refresh/",
                    "sip": "/api/sip/",
                    "track": "/api/track/",
                    "lead": "/api/lead/",
                },
            }
        )


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok"})


class SIPCalculateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SIPRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        monthly_investment = serializer.validated_data["monthly_investment"]
        annual_interest_rate = serializer.validated_data["annual_interest_rate"]
        years = serializer.validated_data["years"]

        future_value = calculate_sip_future_value(
            monthly_investment, annual_interest_rate, years
        )
        total_invested = monthly_investment * Decimal(years * 12)
        total_profit = future_value - total_invested

        calculation = Calculation.objects.create(
            user=request.user,
            amount=monthly_investment,
            rate=annual_interest_rate,
            time=years,
            result=future_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP),
        )

        chart_data = []
        for year in range(1, years + 1):
            year_value = calculate_sip_future_value(
                monthly_investment, annual_interest_rate, year
            )
            chart_data.append(
                {
                    "year": year,
                    "future_value": float(
                        year_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    ),
                    "invested": float(
                        (monthly_investment * Decimal(year * 12)).quantize(
                            Decimal("0.01"), rounding=ROUND_HALF_UP
                        )
                    ),
                }
            )

        return Response(
            {
                "message": "SIP calculated successfully.",
                "calculation_id": calculation.id,
                "future_value": future_value.quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                ),
                "total_invested": total_invested.quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                ),
                "total_profit": total_profit.quantize(
                    Decimal("0.01"), rounding=ROUND_HALF_UP
                ),
                "chart_data": chart_data,
            },
            status=status.HTTP_201_CREATED,
        )


class TrackAffiliateView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AffiliateClickSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        click = AffiliateClick.objects.create(
            user=request.user, **serializer.validated_data
        )
        return Response(
            {
                "message": "Affiliate click tracked.",
                "click_id": click.id,
                "source": click.source,
            },
            status=status.HTTP_201_CREATED,
        )


class LeadCaptureView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LeadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        lead = serializer.save()
        return Response(
            {
                "message": "Lead saved successfully.",
                "lead_id": lead.id,
                "email": lead.email,
                "source": lead.source,
            },
            status=status.HTTP_201_CREATED,
        )


class MonetizationSummaryView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        last_30_days = timezone.now() - timedelta(days=30)

        calculations_qs = Calculation.objects.all()
        clicks_qs = AffiliateClick.objects.all()
        leads_qs = Lead.objects.all()

        total_calculations = calculations_qs.count()
        total_clicks = clicks_qs.count()
        total_leads = leads_qs.count()

        conversion_rate = (
            round((total_clicks / total_calculations) * 100, 2)
            if total_calculations
            else 0
        )

        leads_per_click = (
            round((total_leads / total_clicks) * 100, 2) if total_clicks else 0
        )

        top_campaigns = list(
            clicks_qs.exclude(utm_campaign="")
            .values("utm_campaign")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        top_sources = list(
            clicks_qs.values("source")
            .annotate(count=Count("id"))
            .order_by("-count")[:5]
        )

        recent_clicks = clicks_qs.filter(created_at__gte=last_30_days).count()
        recent_leads = leads_qs.filter(created_at__gte=last_30_days).count()

        return Response(
            {
                "totals": {
                    "calculations": total_calculations,
                    "affiliate_clicks": total_clicks,
                    "leads": total_leads,
                },
                "rates": {
                    "click_to_calculation_percent": conversion_rate,
                    "lead_to_click_percent": leads_per_click,
                },
                "last_30_days": {
                    "affiliate_clicks": recent_clicks,
                    "leads": recent_leads,
                },
                "top_campaigns": top_campaigns,
                "top_sources": top_sources,
            }
        )


def _parse_date_window(request):
    start = request.query_params.get("start")
    end = request.query_params.get("end")
    return start, end


class ExportAffiliateClicksCSVView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        clicks = AffiliateClick.objects.all().order_by("-created_at")
        start, end = _parse_date_window(request)
        if start:
            clicks = clicks.filter(created_at__date__gte=start)
        if end:
            clicks = clicks.filter(created_at__date__lte=end)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = (
            'attachment; filename="affiliate_clicks_report.csv"'
        )

        writer = csv.writer(response)
        writer.writerow(
            [
                "id",
                "username",
                "source",
                "utm_source",
                "utm_medium",
                "utm_campaign",
                "utm_content",
                "created_at",
            ]
        )

        for click in clicks:
            writer.writerow(
                [
                    click.id,
                    click.user.username,
                    click.source,
                    click.utm_source,
                    click.utm_medium,
                    click.utm_campaign,
                    click.utm_content,
                    click.created_at.isoformat(),
                ]
            )

        return response


class ExportLeadsCSVView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        leads = Lead.objects.all().order_by("-created_at")
        start, end = _parse_date_window(request)
        if start:
            leads = leads.filter(created_at__date__gte=start)
        if end:
            leads = leads.filter(created_at__date__lte=end)

        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="lead_report.csv"'

        writer = csv.writer(response)
        writer.writerow(
            [
                "id",
                "email",
                "source",
                "utm_source",
                "utm_medium",
                "utm_campaign",
                "utm_content",
                "consent_given",
                "created_at",
            ]
        )

        for lead in leads:
            writer.writerow(
                [
                    lead.id,
                    lead.email,
                    lead.source,
                    lead.utm_source,
                    lead.utm_medium,
                    lead.utm_campaign,
                    lead.utm_content,
                    lead.consent_given,
                    lead.created_at.isoformat(),
                ]
            )

        return response
