import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'netflix.settings')
django.setup()

from api.models import StripeEvent

event_id = 'evt_1Spnm0GNBxyOu63nE9QbYUIj'

try:
    event = StripeEvent.objects.get(event_id=event_id)
    print(f"Found stuck event: {event.event_id} (Processed at: {event.processed_at})")
    event.delete()
    print("Event deleted successfully. You can now resend the webhook.")
except StripeEvent.DoesNotExist:
    print("Event not found (already deleted?).")
