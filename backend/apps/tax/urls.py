"""Tax URL configuration."""

from django.urls import path
from apps.tax.views import (
    TaxHealthView,
    RateScheduleListView,
    RateScheduleDetailView,
    GenerateBatchView,
    AssessmentListView,
    AssessmentDetailView,
    AssessmentExceptionListView,
    ResolveTurnoverView,
    RetryExceptionView
)

urlpatterns = [
    path("health/", TaxHealthView.as_view(), name="tax-health"),
    
    # Rate Schedules
    path("rate-schedules/", RateScheduleListView.as_view(), name="rate-schedules-list"),
    path("rate-schedules/<str:schedule_id>/", RateScheduleDetailView.as_view(), name="rate-schedules-detail"),
    
    # Assessments
    path("assessments/generate-batch/", GenerateBatchView.as_view(), name="assessments-generate-batch"),
    path("assessments/", AssessmentListView.as_view(), name="assessments-list"),
    path("assessments/<str:assessment_id>/", AssessmentDetailView.as_view(), name="assessments-detail"),
    
    # Assessment Exceptions
    path("assessment-exceptions/", AssessmentExceptionListView.as_view(), name="exceptions-list"),
    path("assessment-exceptions/<str:exception_id>/resolve-turnover/", ResolveTurnoverView.as_view(), name="exceptions-resolve-turnover"),
    path("assessment-exceptions/<str:exception_id>/retry/", RetryExceptionView.as_view(), name="exceptions-retry"),
]
