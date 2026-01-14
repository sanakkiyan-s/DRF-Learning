import os
import django
import sys

# Setup Django environment
sys.path.append('/home/sana/django/netflix')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'netflix.settings')
django.setup()

from api.models import SubscriptionPlan

print("Updating Subscription Plans with Stripe IDs...")

try:
    # Updating Mobile...
    plan = SubscriptionPlan.objects.get(name='Mobile')
    plan.stripe_product_id = 'prod_Tmmgb6q5VNQyNE'
    plan.stripe_price_id_monthly = 'price_1SpD7GGNBxyOu63nc5sqcrDz'
    plan.stripe_price_id_yearly = 'price_1SpD7HGNBxyOu63nBlqPYZOI'
    plan.save()
    print("✅ Mobile updated")

    # Updating Basic...
    plan = SubscriptionPlan.objects.get(name='Basic')
    plan.stripe_product_id = 'prod_TmmgADZ61mez5Y'
    plan.stripe_price_id_monthly = 'price_1SpD7IGNBxyOu63nPcAwwyyw'
    plan.stripe_price_id_yearly = 'price_1SpD7IGNBxyOu63nLoAYwSJs'
    plan.save()
    print("✅ Basic updated")

    # Updating Standard...
    plan = SubscriptionPlan.objects.get(name='Standard')
    plan.stripe_product_id = 'prod_TmmgxxymaNicAu'
    plan.stripe_price_id_monthly = 'price_1SpD7JGNBxyOu63nisXnl6cd'
    plan.stripe_price_id_yearly = 'price_1SpD7JGNBxyOu63nCP5j4owv'
    plan.save()
    print("✅ Standard updated")

    # Updating Premium...
    plan = SubscriptionPlan.objects.get(name='Premium')
    plan.stripe_product_id = 'prod_TmmgYwPg0Kqcdy'
    plan.stripe_price_id_monthly = 'price_1SpD7KGNBxyOu63nZFk3FuLO'
    plan.stripe_price_id_yearly = 'price_1SpD7LGNBxyOu63nlZjmVl46'
    plan.save()
    print("✅ Premium updated")
    
except Exception as e:
    print(f"❌ Error: {e}")
