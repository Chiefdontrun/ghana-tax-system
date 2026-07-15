import json
import logging
from django.http import HttpResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

logger = logging.getLogger(__name__)

@method_decorator(csrf_exempt, name="dispatch")
class ArkeselCaptureView(View):
    def dispatch(self, request, *args, **kwargs):
        payload = {
            "method": request.method,
            "headers": dict(request.headers),
            "GET": dict(request.GET),
            "POST": dict(request.POST),
            "body": request.body.decode('utf-8', errors='ignore')
        }
        
        with open("arkesel_payload.json", "w") as f:
            json.dump(payload, f, indent=2)
            
        logger.info("Captured Arkesel payload to arkesel_payload.json")
        
        # Return a simple generic response that won't crash standard USSD aggregators
        # Many aggregators expect a "continue" string or similar
        return HttpResponse("Continue processing...", status=200, content_type="text/plain")
