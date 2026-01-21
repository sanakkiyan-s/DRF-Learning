
import os
import django
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'netflix.settings')
django.setup()

from api.models import SubscriptionPlan

def update_plans():
    print("Seeding and Updating Subscription Plans in Database...")

    plans_data = [
        {
            'name': 'Mobile',
            'description': 'Watch on 1 phone or tablet at a time. Download on 1 phone or tablet.',
            'price_monthly': 149.00,
            'price_yearly': 1490.00,
            'max_concurrent_streams': 1,
            'max_profiles': 1,
            'max_download_devices': 1,
            'allows_downloads': True,
            'supports_uhd': False,
            'supports_hdr': False,
            'supports_dolby_atmos': False,
            'stripe_product_id': 'prod_TpCivtE20mJAwb',
            'stripe_price_id_monthly': 'price_1SrYJEGNBxyOu63nEIyMpApz',
            'stripe_price_id_yearly': 'price_1SrYJEGNBxyOu63ny5qDZoBC'
        },
        {
            'name': 'Basic',
            'description': 'Watch on 1 screen at a time. Download on 1 phone or tablet.',
            'price_monthly': 199.00,
            'price_yearly': 1990.00,
            'max_concurrent_streams': 1,
            'max_profiles': 1,
            'max_download_devices': 1,
            'allows_downloads': True,
            'supports_uhd': False,
            'supports_hdr': False,
            'supports_dolby_atmos': False,
            'stripe_product_id': 'prod_TpCiS4hBvedjDH',
            'stripe_price_id_monthly': 'price_1SrYJFGNBxyOu63n8ns4p5Z8',
            'stripe_price_id_yearly': 'price_1SrYJFGNBxyOu63nztNnJV0E'
        },
        {
            'name': 'Standard',
            'description': 'Watch on 2 screens at a time in HD. Download on 2 phones or tablets.',
            'price_monthly': 499.00,
            'price_yearly': 4990.00,
            'max_concurrent_streams': 2,
            'max_profiles': 2,
            'max_download_devices': 2,
            'allows_downloads': True,
            'supports_uhd': False,  # 1080p
            'supports_hdr': False,
            'supports_dolby_atmos': True,
            'stripe_product_id': 'prod_TpCiS9QBtvKuvp',
            'stripe_price_id_monthly': 'price_1SrYJGGNBxyOu63nXAzsdIxX',
            'stripe_price_id_yearly': 'price_1SrYJHGNBxyOu63nWc724TpK'
        },
        {
            'name': 'Premium',
            'description': 'Watch on 4 screens at a time in Ultra HD. Download on 4 phones or tablets.',
            'price_monthly': 649.00,
            'price_yearly': 6490.00,
            'max_concurrent_streams': 4,
            'max_profiles': 5,
            'max_download_devices': 4,
            'allows_downloads': True,
            'supports_uhd': True,  # 4K
            'supports_hdr': True,
            'supports_dolby_atmos': True,
            'stripe_product_id': 'prod_TpCi5uSCZsQy4j',
            'stripe_price_id_monthly': 'price_1SrYJHGNBxyOu63nIw2pd2GW',
            'stripe_price_id_yearly': 'price_1SrYJIGNBxyOu63nfIu0R3Oo'
        }
    ]

    for p in plans_data:
        try:
            plan, created = SubscriptionPlan.objects.update_or_create(
                name=p['name'],
                defaults={
                    'description': p['description'],
                    'price_monthly': p['price_monthly'],
                    'price_yearly': p['price_yearly'],
                    'max_concurrent_streams': p['max_concurrent_streams'],
                    'max_profiles': p['max_profiles'],
                    'max_download_devices': p['max_download_devices'],
                    'allows_downloads': p['allows_downloads'],
                    'supports_uhd': p['supports_uhd'],
                    'supports_hdr': p['supports_hdr'],
                    'supports_dolby_atmos': p['supports_dolby_atmos'],
                    'stripe_product_id': p['stripe_product_id'],
                    'stripe_price_id_monthly': p['stripe_price_id_monthly'],
                    'stripe_price_id_yearly': p['stripe_price_id_yearly'],
                    'is_active': True
                }
            )
            action = "Created" if created else "Updated"
            print(f"✅ {action} plan: {p['name']}")
        except Exception as e:
            print(f"❌ Error processing {p['name']}: {e}")

if __name__ == "__main__":
    update_plans()
