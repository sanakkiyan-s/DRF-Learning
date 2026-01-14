# generate_stripe_plans.py
import stripe
import json
import os
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configuration
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')

if not STRIPE_SECRET_KEY:
    print("❌ Error: Please set STRIPE_SECRET_KEY in .env file")
    print("Example .env file:")
    print("STRIPE_SECRET_KEY=sk_test_xxxxxx")
    exit(1)

# Initialize Stripe client
stripe.api_key = STRIPE_SECRET_KEY

print(f"🔑 Using Stripe Key: {STRIPE_SECRET_KEY[:8]}...")
print(f"📅 Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
print("=" * 70)

# Your Netflix-style subscription plans
PLANS_DATA = [
    {
        'name': 'Mobile',
        'description': 'Watch on 1 phone or tablet at a time. Download on 1 phone or tablet.',
        'price_monthly': 149.00,
        'price_yearly': 1490.00,
        'features': ['1 Screen', '480p'],
        'metadata': {
            'max_concurrent_streams': '1',
            'max_profiles': '1',
            'quality': 'SD'
        }
    },
    {
        'name': 'Basic',
        'description': 'Watch on 1 screen at a time. Download on 1 phone or tablet.',
        'price_monthly': 199.00,
        'price_yearly': 1990.00,
        'features': ['1 Screen', '720p'],
        'metadata': {
            'max_concurrent_streams': '1',
            'max_profiles': '1',
            'quality': 'HD'
        }
    },
    {
        'name': 'Standard',
        'description': 'Watch on 2 screens at a time in HD. Download on 2 phones or tablets.',
        'price_monthly': 499.00,
        'price_yearly': 4990.00,
        'features': ['2 Screens', '1080p', 'Dolby Atmos'],
        'metadata': {
            'max_concurrent_streams': '2',
            'max_profiles': '2',
            'quality': 'FHD'
        }
    },
    {
        'name': 'Premium',
        'description': 'Watch on 4 screens at a time in Ultra HD. Download on 4 phones or tablets.',
        'price_monthly': 649.00,
        'price_yearly': 6490.00,
        'features': ['4 Screens', '4K+HDR', 'Dolby Atmos', 'Spatial Audio'],
        'metadata': {
            'max_concurrent_streams': '4',
            'max_profiles': '5',
            'quality': 'UHD'
        }
    }
]

def create_stripe_product_and_prices(plan_data):
    """Create a Product and its Monthly/Yearly Prices in Stripe"""
    try:
        # 1. Create Product
        print(f"\n📦 Creating Product: {plan_data['name']}...")
        product = stripe.Product.create(
            name=plan_data['name'],
            description=plan_data['description'],
            metadata=plan_data['metadata']
        )
        print(f"  ✅ Created Product: {product.id}")

        # 2. Create Monthly Price
        print(f"  creating Monthly Price: ₹{plan_data['price_monthly']}...")
        price_monthly = stripe.Price.create(
            product=product.id,
            unit_amount=int(plan_data['price_monthly'] * 100), # in paise
            currency='inr',
            recurring={'interval': 'month'},
            metadata={'type': 'monthly'}
        )
        print(f"  ✅ Created Monthly Price: {price_monthly.id}")

        # 3. Create Yearly Price
        print(f"  creating Yearly Price: ₹{plan_data['price_yearly']}...")
        price_yearly = stripe.Price.create(
            product=product.id,
            unit_amount=int(plan_data['price_yearly'] * 100), # in paise
            currency='inr',
            recurring={'interval': 'year'},
            metadata={'type': 'yearly'}
        )
        print(f"  ✅ Created Yearly Price: {price_yearly.id}")

        return {
            'success': True,
            'product': product,
            'price_monthly': price_monthly,
            'price_yearly': price_yearly,
            'plan_name': plan_data['name']
        }

    except Exception as e:
        print(f"  ❌ Error: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'plan_name': plan_data['name']
        }

def generate_database_update_code(results):
    """Generate Python code to update Django models"""
    print("\n" + "=" * 90)
    print("🐍 DJANGO SHELL CODE TO UPDATE MODELS")
    print("=" * 90)
    print("# Run this in 'python manage.py shell'")
    print("from api.models import SubscriptionPlan")
    print("")
    
    for res in results:
        if res['success']:
            name = res['plan_name']
            prod_id = res['product'].id
            price_m_id = res['price_monthly'].id
            price_y_id = res['price_yearly'].id
            
            print(f"# Updating {name}...")
            print(f"plan = SubscriptionPlan.objects.get(name='{name}')")
            print(f"plan.stripe_product_id = '{prod_id}'")
            print(f"plan.stripe_price_id_monthly = '{price_m_id}'")
            print(f"plan.stripe_price_id_yearly = '{price_y_id}'")
            print("plan.save()")
            print("")

def main():
    print("🚀 STRIPE SUBSCRIPTION PLAN GENERATOR")
    print("=" * 70)
    
    confirm = input("This will create 4 Products and 8 Prices in Stripe. Continue? (y/n): ")
    if confirm.lower() != 'y':
        print("Cancelled.")
        return

    results = []
    for plan in PLANS_DATA:
        result = create_stripe_product_and_prices(plan)
        results.append(result)
    
    # Summary
    success_count = sum(1 for r in results if r['success'])
    print("\n" + "=" * 70)
    print(f"Completed: {success_count}/{len(PLANS_DATA)} Plans created successfully.")
    
    if success_count > 0:
        generate_database_update_code(results)

if __name__ == "__main__":
    main()
