import os
import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'netflix.settings')
django.setup()

from api.models import User, UserSubscription, BillingHistory, StripeEvent

print("--- Debugging Billing State ---")
users = User.objects.all()
print(f"Total Users: {users.count()}")

for user in users:
    print(f"\nUser: {user.email} (ID: {user.id})")
    print(f"  Stripe Customer ID: {user.stripe_customer_id}")
    
    subs = UserSubscription.objects.filter(user=user)
    print(f"  Subscriptions ({subs.count()}):")
    for sub in subs:
        print(f"    - Plan: {sub.subscription_plan.name}")
        print(f"      Status: {sub.status}")
        print(f"      Stripe Sub ID: {sub.stripe_subscription_id}")
        print(f"      Created: {sub.created_at}")

    history = BillingHistory.objects.filter(user=user)
    print(f"  Billing History ({history.count()}):")
    for item in history:
        print(f"    - Invoice: {item.invoice_number}")
        print(f"      Amount: {item.amount} {item.currency}")
        print(f"      Status: {item.payment_status}")

print("\n--- Recent Stripe Events ---")
events = StripeEvent.objects.order_by('-processed_at')[:10]
for event in events:
    print(f"  {event.processed_at}: {event.event_type} ({event.event_id})")
