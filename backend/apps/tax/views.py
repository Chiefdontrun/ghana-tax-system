"""Tax API Views."""

from datetime import datetime, timezone
import uuid

from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from apps.auth_app.permissions import IsTaxAdmin, IsSysAdmin
from core.utils.response import success_response, error_response
from apps.tax.services import TaxService
from apps.tax.exceptions import TurnoverRequiredError, RateScheduleNotFoundError
from apps.tax.repository import TaxRateScheduleRepository, TaxAssessmentRepository, TaxAssessmentExceptionRepository
from apps.audit.repository import AuditRepository


class TaxHealthView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return success_response(data={"status": "ok"}, message="Tax app ready.")


class RateScheduleListView(APIView):
    def get_permissions(self):
        if self.request.method == 'POST':
            return [IsSysAdmin()]
        return [IsTaxAdmin()]

    def get(self, request):
        repo = TaxRateScheduleRepository()
        query = {}
        for key in ["tax_category", "business_type", "region", "district"]:
            if val := request.query_params.get(key):
                query[key] = val
        if val := request.query_params.get("effective_year"):
            query["effective_year"] = int(val)
        if val := request.query_params.get("is_active"):
            query["is_active"] = val.lower() == "true"
        
        cursor = repo._col().find(query, {"_id": 0}).sort("created_at", -1)
        return success_response(data=list(cursor))

    def post(self, request):
        data = request.data
        rate_type = data.get("rate_type")
        
        if rate_type == "FIXED":
            if data.get("percentage_rate") is not None or data.get("min_amount") is not None or data.get("max_amount") is not None:
                return error_response("FIXED rate schedules must not specify percentage_rate, min_amount, or max_amount.", http_status=400)
            if data.get("fixed_amount") is None:
                return error_response("FIXED rate schedules require a fixed_amount.", http_status=400)
                
        elif rate_type == "PERCENTAGE_TURNOVER":
            if data.get("fixed_amount") is not None:
                return error_response("PERCENTAGE_TURNOVER rate schedules must not specify fixed_amount.", http_status=400)
            if data.get("percentage_rate") is None:
                return error_response("PERCENTAGE_TURNOVER rate schedules require a percentage_rate.", http_status=400)
        else:
            return error_response("Invalid rate_type.", http_status=400)
            
        schedule_id = str(uuid.uuid4())
        doc = {
            "schedule_id": schedule_id,
            "tax_category": data.get("tax_category"),
            "business_type": data.get("business_type"),
            "region": data.get("region"),
            "district": data.get("district"),
            "rate_type": rate_type,
            "fixed_amount": data.get("fixed_amount"),
            "percentage_rate": data.get("percentage_rate"),
            "min_amount": data.get("min_amount"),
            "max_amount": data.get("max_amount"),
            "period": data.get("period", "ANNUAL"),
            "effective_year": data.get("effective_year"),
            "is_active": data.get("is_active", True),
            "created_by": request.user.get("admin_id"),
            "created_at": datetime.now(timezone.utc),
            "updated_at": datetime.now(timezone.utc),
        }
        
        repo = TaxRateScheduleRepository()
        repo._col().insert_one(doc)
        doc.pop("_id", None)
        
        AuditRepository().log({
            "action": "TAX_SCHEDULE_CREATED",
            "entity_type": "tax_rate_schedule",
            "entity_id": schedule_id,
            "actor_type": "admin",
            "actor_id": request.user.get("admin_id"),
            "channel": "admin",
            "details": doc
        })
        
        return success_response(data=doc, message="Rate schedule created.", http_status=201)

class RateScheduleDetailView(APIView):
    permission_classes = [IsSysAdmin]

    def patch(self, request, schedule_id):
        repo = TaxRateScheduleRepository()
        schedule = repo.find_by_id(schedule_id)
        if not schedule:
            return error_response("Schedule not found.", http_status=404)
            
        data = request.data
        
        # Determine effective values based on patch.
        # Check if the user is un-setting things (passing None).
        new_rate_type = data.get("rate_type", schedule.get("rate_type"))
        
        def _get_val(key):
            if key in data:
                return data[key]
            return schedule.get(key)
            
        new_fixed_amount = _get_val("fixed_amount")
        new_percentage_rate = _get_val("percentage_rate")
        new_min_amount = _get_val("min_amount")
        new_max_amount = _get_val("max_amount")
        
        if new_rate_type == "FIXED":
            if new_percentage_rate is not None or new_min_amount is not None or new_max_amount is not None:
                return error_response("FIXED rate schedules must not specify percentage_rate, min_amount, or max_amount.", http_status=400)
            if new_fixed_amount is None:
                return error_response("FIXED rate schedules require a fixed_amount.", http_status=400)
                
        elif new_rate_type == "PERCENTAGE_TURNOVER":
            if new_fixed_amount is not None:
                return error_response("PERCENTAGE_TURNOVER rate schedules must not specify fixed_amount.", http_status=400)
            if new_percentage_rate is None:
                return error_response("PERCENTAGE_TURNOVER rate schedules require a percentage_rate.", http_status=400)
                
        updates = {k: v for k, v in data.items() if k in [
            "tax_category", "business_type", "region", "district", "rate_type",
            "fixed_amount", "percentage_rate", "min_amount", "max_amount",
            "period", "effective_year", "is_active"
        ]}
        
        updates["updated_at"] = datetime.now(timezone.utc)
        repo._col().update_one({"schedule_id": schedule_id}, {"$set": updates})
        
        updated = repo.find_by_id(schedule_id)
        
        AuditRepository().log({
            "action": "TAX_SCHEDULE_UPDATED",
            "entity_type": "tax_rate_schedule",
            "entity_id": schedule_id,
            "actor_type": "admin",
            "actor_id": request.user.get("admin_id"),
            "channel": "admin",
            "details": {"updates": updates}
        })
        
        return success_response(data=updated, message="Rate schedule updated.")

class GenerateBatchView(APIView):
    permission_classes = [IsSysAdmin]

    def post(self, request):
        year = request.data.get("year")
        if not year:
            return error_response("Year is required.", http_status=400)
            
        service = TaxService()
        summary = service.generate_annual_assessments_batch(int(year), admin_id=request.user.get("admin_id"))
        
        return success_response(data=summary, message="Batch generation completed.")

class AssessmentListView(APIView):
    permission_classes = [IsTaxAdmin]

    def get(self, request):
        repo = TaxAssessmentRepository()
        query = {}
        for key in ["status", "business_type", "region", "district", "period_label", "trader_id"]:
            if val := request.query_params.get(key):
                query[key] = val
        
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        skip = (page - 1) * page_size
        
        total = repo._col().count_documents(query)
        cursor = repo._col().find(query, {"_id": 0}).sort("created_at", -1).skip(skip).limit(page_size)
        
        return success_response(data=list(cursor), meta={"total": total, "page": page, "page_size": page_size})

class AssessmentDetailView(APIView):
    permission_classes = [IsTaxAdmin]

    def get(self, request, assessment_id):
        repo = TaxAssessmentRepository()
        assessment = repo.find_by_id(assessment_id)
        if not assessment:
            return error_response("Assessment not found.", http_status=404)
            
        assessment["payments"] = []
        return success_response(data=assessment)

class AssessmentExceptionListView(APIView):
    permission_classes = [IsTaxAdmin]

    def get(self, request):
        repo = TaxAssessmentExceptionRepository()
        filters = {}
        for key in ["exception_type", "status", "business_type", "district"]:
            if val := request.query_params.get(key):
                filters[key] = val
                
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        skip = (page - 1) * page_size
        
        data, total = repo.list_with_filters(filters, skip=skip, limit=page_size)
        return success_response(data=data, meta={"total": total, "page": page, "page_size": page_size})

class ResolveTurnoverView(APIView):
    permission_classes = [IsTaxAdmin]

    def post(self, request, exception_id):
        turnover = request.data.get("declared_turnover_pesewas")
        if turnover is None:
            return error_response("declared_turnover_pesewas is required.", http_status=400)
            
        repo = TaxAssessmentExceptionRepository()
        exception = repo.find_by_id(exception_id)
        if not exception or exception.get("exception_type") != "NEEDS_TURNOVER":
            return error_response("Exception not found or not NEEDS_TURNOVER.", http_status=404)
            
        if exception.get("status") == "RESOLVED":
            return error_response("Exception already resolved.", http_status=400)
            
        service = TaxService()
        try:
            assessment = service.generate_assessment(
                business_id=exception["business_id"],
                tax_category=exception["tax_category"],
                period_label=exception["period_label"],
                channel_generated="admin_manual",
                declared_turnover_pesewas=int(turnover),
                actor_id=request.user.get("admin_id")
            )
            
            repo.update(exception_id, {
                "status": "RESOLVED",
                "resolved_by": request.user.get("admin_id"),
                "resolved_at": datetime.now(timezone.utc)
            })
            return success_response(data={"assessment": assessment}, message="Turnover resolved and assessment generated.")
        except Exception as e:
            return error_response(str(e), http_status=400)

class RetryExceptionView(APIView):
    permission_classes = [IsTaxAdmin]

    def post(self, request, exception_id):
        repo = TaxAssessmentExceptionRepository()
        exception = repo.find_by_id(exception_id)
        if not exception or exception.get("exception_type") != "MISSING_SCHEDULE":
            return error_response("Exception not found or not MISSING_SCHEDULE.", http_status=404)
            
        if exception.get("status") == "RESOLVED":
            return error_response("Exception already resolved.", http_status=400)
            
        service = TaxService()
        try:
            assessment = service.generate_assessment(
                business_id=exception["business_id"],
                tax_category=exception["tax_category"],
                period_label=exception["period_label"],
                channel_generated="admin_manual",
                actor_id=request.user.get("admin_id")
            )
            
            repo.update(exception_id, {
                "status": "RESOLVED",
                "resolved_by": request.user.get("admin_id"),
                "resolved_at": datetime.now(timezone.utc)
            })
            return success_response(data={"assessment": assessment}, message="Schedule found and assessment generated.")
        except RateScheduleNotFoundError as e:
            return error_response("Schedule still missing. " + str(e), http_status=400)
        except Exception as e:
            return error_response(str(e), http_status=400)
