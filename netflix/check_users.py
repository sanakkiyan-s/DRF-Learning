import os
import django
import sys

sys.path.append('/home/sana/django/netflix')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'netflix.settings')
django.setup()

from api.models import User, UserSubscription

print("Checking Users and Subscriptions:")
print("-" * 50)

for user in User.objects.all():
    try:
        sub = UserSubscription.objects.get(user=user)
        status = sub.status
        plan = sub.subscription_plan.name
        print(f"User: {user.email:<30} | Status: {status:<10} | Plan: {plan}")
    except UserSubscription.DoesNotExist:
        print(f"User: {user.email:<30} | NO SUBSCRIPTION")
    except Exception as e:
        print(f"User: {user.email:<30} | Error: {e}")
