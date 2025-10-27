
from decimal import Decimal
from django.http import HttpResponse

from .models import Order, Payment
from .services import record_payment


class StripeWH_Handler:
    """Handle Stripe webhook events for this project."""

    def __init__(self, request):
        self.request = request

    # ---------- helpers ----------
    def _record(self, order: Order, *, success: bool, provider_ref: str) -> HttpResponse:
        """Create a Payment row and mark order paid on success."""
        status = Payment.Status.SUCCESS if success else Payment.Status.FAILED
        record_payment(
            order=order,
            provider="stripe",
            method=Payment.Method.CARD,
            status=status,
            amount=Decimal(order.total_amount),
            provider_ref=provider_ref,
        )
        return HttpResponse(status=200)

    def _order_from_metadata(self, metadata: dict | None) -> Order | None:
        """Find the order using the id we attach in Checkout Session metadata."""
        metadata = metadata or {}
        order_id = metadata.get("order_id")
        if not order_id:
            return None
        try:
            return Order.objects.get(pk=order_id)
        except Order.DoesNotExist:
            return None

    # ---------- generic ----------
    def handle_event(self, event):
        """Default handler for unhandled events."""
        return HttpResponse(status=200)

    # ---------- specific handlers ----------
    def handle_checkout_session_completed(self, event):
        """
        Fired when a Checkout Session completes successfully.
        event['data']['object'] is the Session.
        We expect metadata.order_id to be present (set when creating the Session).
        """
        session = event["data"]["object"]
        order = self._order_from_metadata(session.get("metadata"))
        if not order:
            return HttpResponse(status=200)

        provider_ref = session.get("payment_intent") or session.get("id")
        return self._record(order, success=True, provider_ref=provider_ref)

    def handle_payment_intent_succeeded(self, event):
        """
        Optional fallback if you decide to rely on PI events.
        """
        intent = event["data"]["object"]
        order = self._order_from_metadata(intent.get("metadata"))
        if not order:
            return HttpResponse(status=200)

        provider_ref = intent.get("id")
        return self._record(order, success=True, provider_ref=provider_ref)

    def handle_payment_intent_payment_failed(self, event):
        intent = event["data"]["object"]
        order = self._order_from_metadata(intent.get("metadata"))
        if not order:
            return HttpResponse(status=200)

        provider_ref = intent.get("id")
        return self._record(order, success=False, provider_ref=provider_ref)
