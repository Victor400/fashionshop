# orders/webhooks.py
from django.http import HttpResponse
from django.conf import settings
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
import stripe

@require_POST
@csrf_exempt
def stripe_webhook(request):
    """Listen for webhooks from Stripe."""
    stripe.api_key = settings.STRIPE_SECRET_KEY
    wh_secret = settings.STRIPE_WEBHOOK_SECRET

    payload = request.body
    sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, wh_secret)
    except (ValueError, stripe.error.SignatureVerificationError):
        return HttpResponse(status=400)

    # Handle events you care about (example)
    if event["type"] == "checkout.session.completed":
        # You can add logic here later if you want
        pass

    return HttpResponse(status=200)
