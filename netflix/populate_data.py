# populate_data.py
import os
import django
from django.utils import timezone
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'netflix.settings')
django.setup()

from django.contrib.auth.hashers import make_password
from api.models import *

def create_users_and_profiles():
    """Create users and their profiles"""
    print("Creating users and profiles...")
    
    # Create users
    users_data = [
        {
            'email': 'john.doe@example.com',
            'password': 'password123',
            'phone_number': '+919876543210',
            'country_code': 'IN',
            'last_login_at': timezone.now() - timedelta(days=2)
        },
        {
            'email': 'jane.smith@example.com',
            'password': 'password123',
            'phone_number': '+919876543211',
            'country_code': 'IN',
            'last_login_at': timezone.now() - timedelta(days=1)
        },
        {
            'email': 'robert.johnson@example.com',
            'password': 'password123',
            'phone_number': '+919876543212',
            'country_code': 'US',
            'last_login_at': timezone.now() - timedelta(hours=12)
        },
        {
            'email': 'sarah.wilson@example.com',
            'password': 'password123',
            'phone_number': '+919876543213',
            'country_code': 'UK',
            'last_login_at': timezone.now() - timedelta(hours=6)
        }
    ]
    
    users = []
    for user_data in users_data:
        user, created = User.objects.get_or_create(
            email=user_data['email'],
            defaults={
                'password': make_password(user_data['password']),
                'phone_number': user_data['phone_number'],
                'country_code': user_data['country_code'],
                'last_login_at': user_data['last_login_at']
            }
        )
        users.append(user)
        print(f"Created user: {user.email}")
    
    # Create profiles for each user
    profiles_data = [
        # John Doe's profiles
        {'user': users[0], 'name': 'John', 'age': 28, 'is_kid_profile': False},
        {'user': users[0], 'name': 'Kids', 'age': 8, 'is_kid_profile': True},
        
        # Jane Smith's profiles
        {'user': users[1], 'name': 'Jane', 'age': 32, 'is_kid_profile': False},
        {'user': users[1], 'name': 'Spouse', 'age': 35, 'is_kid_profile': False},
        
        # Robert Johnson's profile
        {'user': users[2], 'name': 'Robert', 'age': 40, 'is_kid_profile': False},
        
        # Sarah Wilson's profiles
        {'user': users[3], 'name': 'Sarah', 'age': 25, 'is_kid_profile': False},
        {'user': users[3], 'name': 'Guest', 'age': 30, 'is_kid_profile': False},
    ]
    
    profiles = []
    for profile_data in profiles_data:
        profile, created = Profile.objects.get_or_create(
            user=profile_data['user'],
            name=profile_data['name'],
            defaults={
                'age': profile_data['age'],
                'is_kid_profile': profile_data['is_kid_profile'],
                'avatar_url': f"https://api.dicebear.com/7.x/avataaars/svg?seed={profile_data['name']}"
            }
        )
        profiles.append(profile)
        print(f"Created profile: {profile.user.email} - {profile.name}")
    
    return users, profiles

def create_maturity_levels():
    """Create maturity levels"""
    print("\nCreating maturity levels...")
    
    maturity_levels_data = [
        {'code': 'U', 'name': 'Universal', 'description': 'Suitable for all ages', 'minimum_age': 0},
        {'code': '7+', 'name': '7 Plus', 'description': 'Suitable for age 7 and above', 'minimum_age': 7},
        {'code': '13+', 'name': 'Teen', 'description': 'Suitable for age 13 and above', 'minimum_age': 13},
        {'code': '16+', 'name': 'Young Adult', 'description': 'Suitable for age 16 and above', 'minimum_age': 16},
        {'code': '18+', 'name': 'Adult', 'description': 'Adults only', 'minimum_age': 18},
        {'code': 'A', 'name': 'Adults Only', 'description': 'Explicit content for adults', 'minimum_age': 21},
    ]
    
    maturity_levels = {}
    for ml_data in maturity_levels_data:
        ml, created = MaturityLevel.objects.get_or_create(
            code=ml_data['code'],
            defaults=ml_data
        )
        maturity_levels[ml.code] = ml
        print(f"Created maturity level: {ml.code} - {ml.name}")
    
    return maturity_levels

def create_genres():
    """Create genres"""
    print("\nCreating genres...")
    
    genres_data = [
        {'name': 'Action', 'description': 'High-energy physical stunts and chases'},
        {'name': 'Comedy', 'description': 'Humor and entertainment'},
        {'name': 'Drama', 'description': 'Serious plot-driven content'},
        {'name': 'Science Fiction', 'description': 'Futuristic technology and science'},
        {'name': 'Horror', 'description': 'Scary and suspenseful content'},
        {'name': 'Romance', 'description': 'Love stories and relationships'},
        {'name': 'Thriller', 'description': 'Suspenseful and exciting narratives'},
        {'name': 'Documentary', 'description': 'Non-fiction educational content'},
        {'name': 'Animation', 'description': 'Animated content for all ages'},
        {'name': 'Crime', 'description': 'Criminal activities and investigations'},
    ]
    
    genres = {}
    for genre_data in genres_data:
        genre, created = Genre.objects.get_or_create(
            name=genre_data['name'],
            defaults=genre_data
        )
        genres[genre.name] = genre
        print(f"Created genre: {genre.name}")
    
    return genres

def create_cast_members():
    """Create cast members"""
    print("\nCreating cast members...")
    
    cast_data = [
        {'name': 'Christopher Nolan', 'birth_date': '1970-07-30'},
        {'name': 'Leonardo DiCaprio', 'birth_date': '1974-11-11'},
        {'name': 'Joseph Gordon-Levitt', 'birth_date': '1981-02-17'},
        {'name': 'Ellen Page', 'birth_date': '1987-02-21'},
        {'name': 'Tom Hardy', 'birth_date': '1977-09-15'},
        
        {'name': 'The Duffer Brothers', 'birth_date': '1984-02-15'},
        {'name': 'Millie Bobby Brown', 'birth_date': '2004-02-19'},
        {'name': 'Finn Wolfhard', 'birth_date': '2002-12-23'},
        {'name': 'Winona Ryder', 'birth_date': '1971-10-29'},
        {'name': 'David Harbour', 'birth_date': '1975-04-10'},
        
        {'name': 'Rajkumar Hirani', 'birth_date': '1962-11-20'},
        {'name': 'Aamir Khan', 'birth_date': '1965-03-14'},
        {'name': 'Kareena Kapoor', 'birth_date': '1980-09-21'},
        {'name': 'Sharman Joshi', 'birth_date': '1979-04-28'},
        
        {'name': 'James Cameron', 'birth_date': '1954-08-16'},
        {'name': 'Sam Worthington', 'birth_date': '1976-08-02'},
        {'name': 'Zoe Saldana', 'birth_date': '1978-06-19'},
    ]
    
    cast_members = {}
    for cast in cast_data:
        member, created = CastMember.objects.get_or_create(
            name=cast['name'],
            defaults={
                'birth_date': cast['birth_date'],
                'profile_image_url': f"https://api.dicebear.com/7.x/avataaars/svg?seed={cast['name'].replace(' ', '')}"
            }
        )
        cast_members[cast['name']] = member
        print(f"Created cast member: {member.name}")
    
    return cast_members

def create_content_and_movies(maturity_levels, genres, cast_members):
    """Create content and movies"""
    print("\nCreating content and movies...")
    
    # Create movies
    movies_data = [
        {
            'title': 'Inception',
            'description': 'A thief who steals corporate secrets through dream-sharing technology is given the inverse task of planting an idea into the mind of a C.E.O.',
            'content_type': Content.ContentType.MOVIE,
            'release_date': '2010-07-16',
            'duration_minutes': 148,
            'poster_image_url': 'https://image.tmdb.org/t/p/w500/9gk7adHYeDvHkCSEqAvQNLV5Uge.jpg',
            'backdrop_image_url': 'https://image.tmdb.org/t/p/w1280/s3TBrRGB1iav7gFOCNx3H31MoES.jpg',
            'trailer_url': 'https://www.youtube.com/watch?v=YoHD9XEInc0',
            'imdb_id': 'tt1375666',
            'tmdb_id': 27205,
            'maturity_level': maturity_levels['13+'],
            'movie_details': {
                'director': 'Christopher Nolan',
                'budget': 160000000,
                'box_office_revenue': 836800000,
                'awards': 'Won 4 Oscars. 157 wins & 220 nominations total'
            },
            'genres': ['Action', 'Science Fiction', 'Thriller'],
            'cast': [
                {'member': 'Leonardo DiCaprio', 'character_name': 'Cobb', 'role_type': 'actor'},
                {'member': 'Joseph Gordon-Levitt', 'character_name': 'Arthur', 'role_type': 'actor'},
                {'member': 'Ellen Page', 'character_name': 'Ariadne', 'role_type': 'actor'},
                {'member': 'Tom Hardy', 'character_name': 'Eames', 'role_type': 'actor'},
                {'member': 'Christopher Nolan', 'character_name': None, 'role_type': 'director'},
            ]
        },
        {
            'title': '3 Idiots',
            'description': 'Two friends are searching for their long lost companion. They revisit their college days and recall the memories of their friend who inspired them to think differently.',
            'content_type': Content.ContentType.MOVIE,
            'release_date': '2009-12-25',
            'duration_minutes': 170,
            'poster_image_url': 'https://image.tmdb.org/t/p/w500/66A9MqXOyVFCssoloscw0z5hPff.jpg',
            'backdrop_image_url': 'https://image.tmdb.org/t/p/w1280/8Rs2L3fLgP2fghgEfRq0FqQxdfF.jpg',
            'trailer_url': 'https://www.youtube.com/watch?v=K0eDlFX9GMc',
            'imdb_id': 'tt1187043',
            'tmdb_id': 20453,
            'maturity_level': maturity_levels['U'],
            'movie_details': {
                'director': 'Rajkumar Hirani',
                'budget': 55000000,
                'box_office_revenue': 460000000,
                'awards': 'Won 6 Filmfare Awards'
            },
            'genres': ['Comedy', 'Drama'],
            'cast': [
                {'member': 'Aamir Khan', 'character_name': 'Rancho', 'role_type': 'actor'},
                {'member': 'Kareena Kapoor', 'character_name': 'Pia', 'role_type': 'actor'},
                {'member': 'Sharman Joshi', 'character_name': 'Raju', 'role_type': 'actor'},
                {'member': 'Rajkumar Hirani', 'character_name': None, 'role_type': 'director'},
            ]
        },
        {
            'title': 'Avatar',
            'description': 'A paraplegic Marine dispatched to the moon Pandora on a unique mission becomes torn between following his orders and protecting the world he feels is his home.',
            'content_type': Content.ContentType.MOVIE,
            'release_date': '2009-12-18',
            'duration_minutes': 162,
            'poster_image_url': 'https://image.tmdb.org/t/p/w500/jRXYjXNq0Cs2TcJjLkki24MLp7u.jpg',
            'backdrop_image_url': 'https://image.tmdb.org/t/p/w1280/8rpDcsfLJypbO6vREc0547VKqEv.jpg',
            'trailer_url': 'https://www.youtube.com/watch?v=5PSNL1qE6VY',
            'imdb_id': 'tt0499549',
            'tmdb_id': 19995,
            'maturity_level': maturity_levels['13+'],
            'movie_details': {
                'director': 'James Cameron',
                'budget': 237000000,
                'box_office_revenue': 2923706026,
                'awards': 'Won 3 Oscars. 89 wins & 129 nominations total'
            },
            'genres': ['Action', 'Science Fiction', 'Drama'],
            'cast': [
                {'member': 'Sam Worthington', 'character_name': 'Jake Sully', 'role_type': 'actor'},
                {'member': 'Zoe Saldana', 'character_name': 'Neytiri', 'role_type': 'actor'},
                {'member': 'James Cameron', 'character_name': None, 'role_type': 'director'},
            ]
        }
    ]
    
    movies = []
    for movie_data in movies_data:
        # Create content
        content, created = Content.objects.get_or_create(
            title=movie_data['title'],
            defaults={
                'description': movie_data['description'],
                'content_type': movie_data['content_type'],
                'release_date': movie_data['release_date'],
                'duration_minutes': movie_data['duration_minutes'],
                'poster_image_url': movie_data['poster_image_url'],
                'backdrop_image_url': movie_data['backdrop_image_url'],
                'trailer_url': movie_data['trailer_url'],
                'imdb_id': movie_data['imdb_id'],
                'tmdb_id': movie_data['tmdb_id'],
                'maturity_level': movie_data['maturity_level'],
            }
        )
        
        # Create movie details
        Movie.objects.get_or_create(
            content=content,
            defaults=movie_data['movie_details']
        )
        
        # Add genres
        for genre_name in movie_data['genres']:
            ContentGenre.objects.get_or_create(
                content=content,
                genre=genres[genre_name]
            )
        
        # Add cast
        for cast_info in movie_data['cast']:
            ContentCast.objects.get_or_create(
                content=content,
                cast_member=cast_members[cast_info['member']],
                defaults={
                    'character_name': cast_info['character_name'],
                    'role_type': cast_info['role_type']
                }
            )
        
        movies.append(content)
        print(f"Created movie: {content.title}")
    
    return movies

def create_tv_shows_and_episodes(maturity_levels, genres, cast_members):
    """Create TV shows, seasons, and episodes"""
    print("\nCreating TV shows, seasons, and episodes...")
    
    # Create TV show
    tv_show_data = {
        'title': 'Stranger Things',
        'description': 'When a young boy vanishes, a small town uncovers a mystery involving secret experiments, terrifying supernatural forces and one strange little girl.',
        'content_type': Content.ContentType.TV_SHOW,
        'release_date': '2016-07-15',
        'duration_minutes': 50,
        'poster_image_url': 'https://image.tmdb.org/t/p/w500/49WJfeN0moxb9IPfGn8AIqMGskD.jpg',
        'backdrop_image_url': 'https://image.tmdb.org/t/p/w1280/56v2KjBlU4XaOv9rVYEQypROD7P.jpg',
        'trailer_url': 'https://www.youtube.com/watch?v=b9EkMc79ZSU',
        'imdb_id': 'tt4574334',
        'tmdb_id': 66732,
        'maturity_level': maturity_levels['16+'],
        'tv_show_details': {
            'total_seasons': 4,
            'total_episodes': 34,
            'status': 'ongoing'
        },
        'genres': ['Drama', 'Science Fiction', 'Horror'],
        'cast': [
            {'member': 'Millie Bobby Brown', 'character_name': 'Eleven', 'role_type': 'actor'},
            {'member': 'Finn Wolfhard', 'character_name': 'Mike Wheeler', 'role_type': 'actor'},
            {'member': 'Winona Ryder', 'character_name': 'Joyce Byers', 'role_type': 'actor'},
            {'member': 'David Harbour', 'character_name': 'Jim Hopper', 'role_type': 'actor'},
            {'member': 'The Duffer Brothers', 'character_name': None, 'role_type': 'director'},
        ],
        'seasons': [
            {
                'season_number': 1,
                'title': 'Season One',
                'release_date': '2016-07-15',
                'poster_image_url': 'https://image.tmdb.org/t/p/w500/5n0D8D5Xx8FkHt7KuohTB2cl6U.jpg',
                'episodes': [
                    {
                        'title': 'Chapter One: The Vanishing of Will Byers',
                        'description': 'On his way home from a friends house, young Will sees something terrifying. Nearby, a sinister secret lurks in the depths of a government lab.',
                        'duration_minutes': 47,
                        'release_date': '2016-07-15',
                    },
                    {
                        'title': 'Chapter Two: The Weirdo on Maple Street',
                        'description': 'Lucas, Mike and Dustin try to talk to the girl they found in the woods. Hopper questions an anxious Joyce about an unsettling phone call.',
                        'duration_minutes': 55,
                        'release_date': '2016-07-15',
                    },
                    {
                        'title': 'Chapter Three: Holly, Jolly',
                        'description': 'An increasingly concerned Nancy looks for Barb and finds out what Jonathan has been up to. Joyce is convinced Will is trying to talk to her.',
                        'duration_minutes': 51,
                        'release_date': '2016-07-15',
                    }
                ]
            },
            {
                'season_number': 2,
                'title': 'Season Two',
                'release_date': '2017-10-27',
                'poster_image_url': 'https://image.tmdb.org/t/p/w500/lXS60geme1LlEob5Wgvj3KilClA.jpg',
                'episodes': [
                    {
                        'title': 'Chapter One: MADMAX',
                        'description': 'One year after the events with the Demogorgon, the party has a new member, Max, and the boys are trying to adjust to her arrival.',
                        'duration_minutes': 48,
                        'release_date': '2017-10-27',
                    }
                ]
            }
        ]
    }
    
    # Create TV show content
    tv_show, created = Content.objects.get_or_create(
        title=tv_show_data['title'],
        defaults={
            'description': tv_show_data['description'],
            'content_type': tv_show_data['content_type'],
            'release_date': tv_show_data['release_date'],
            'duration_minutes': tv_show_data['duration_minutes'],
            'poster_image_url': tv_show_data['poster_image_url'],
            'backdrop_image_url': tv_show_data['backdrop_image_url'],
            'trailer_url': tv_show_data['trailer_url'],
            'imdb_id': tv_show_data['imdb_id'],
            'tmdb_id': tv_show_data['tmdb_id'],
            'maturity_level': tv_show_data['maturity_level'],
        }
    )
    
    # Create TV show details
    tv_show_obj, _ = TVShow.objects.get_or_create(
        content=tv_show,
        defaults=tv_show_data['tv_show_details']
    )
    
    # Add genres
    for genre_name in tv_show_data['genres']:
        ContentGenre.objects.get_or_create(
            content=tv_show,
            genre=genres[genre_name]
        )
    
    # Add cast
    for cast_info in tv_show_data['cast']:
        ContentCast.objects.get_or_create(
            content=tv_show,
            cast_member=cast_members[cast_info['member']],
            defaults={
                'character_name': cast_info['character_name'],
                'role_type': cast_info['role_type']
            }
        )
    
    # Create seasons and episodes
    episodes = []
    for season_data in tv_show_data['seasons']:
        season, _ = Season.objects.get_or_create(
            tv_show=tv_show_obj,
            season_number=season_data['season_number'],
            defaults={
                'title': season_data['title'],
                'release_date': season_data['release_date'],
                'poster_image_url': season_data['poster_image_url'],
                'description': f'Season {season_data["season_number"]} of {tv_show.title}'
            }
        )
        
        for ep_idx, episode_data in enumerate(season_data['episodes'], 1):
            # Create episode content
            ep_content, _ = Content.objects.get_or_create(
                title=episode_data['title'],
                content_type=Content.ContentType.TV_SHOW,
                release_date=episode_data['release_date'],
                defaults={
                    'description': episode_data['description'],
                    'duration_minutes': episode_data['duration_minutes'],
                    'maturity_level': tv_show.maturity_level,
                    'poster_image_url': tv_show.poster_image_url,
                    'backdrop_image_url': tv_show.backdrop_image_url,
                }
            )
            
            # Create episode
            episode, _ = Episode.objects.get_or_create(
                content=ep_content,
                season=season,
                episode_number=ep_idx,
                defaults={}
            )
            
            episodes.append(episode)
            print(f"Created episode: {tv_show.title} S{season.season_number}E{ep_idx} - {episode_data['title']}")
    
    print(f"Created TV show: {tv_show.title}")
    return tv_show, episodes

def create_subscription_plans():
    """Create subscription plans"""
    print("\nCreating subscription plans...")
    
    plans_data = [
        {
            'name': 'Mobile',
            'description': 'Watch on 1 phone or tablet at a time. Download on 1 phone or tablet.',
            'price_monthly': 149.00,
            'price_yearly': 1490.00,
            'max_concurrent_streams': 1,
            'max_profiles': 1,
            'supports_uhd': False,
            'supports_hdr': False,
            'supports_dolby_atmos': False,
            'allows_downloads': True,
            'max_download_devices': 1,
            'display_order': 1
        },
        {
            'name': 'Basic',
            'description': 'Watch on 1 screen at a time. Download on 1 phone or tablet.',
            'price_monthly': 199.00,
            'price_yearly': 1990.00,
            'max_concurrent_streams': 1,
            'max_profiles': 1,
            'supports_uhd': False,
            'supports_hdr': False,
            'supports_dolby_atmos': False,
            'allows_downloads': True,
            'max_download_devices': 1,
            'display_order': 2
        },
        {
            'name': 'Standard',
            'description': 'Watch on 2 screens at a time in HD. Download on 2 phones or tablets.',
            'price_monthly': 499.00,
            'price_yearly': 4990.00,
            'max_concurrent_streams': 2,
            'max_profiles': 2,
            'supports_uhd': False,
            'supports_hdr': False,
            'supports_dolby_atmos': True,
            'allows_downloads': True,
            'max_download_devices': 2,
            'display_order': 3
        },
        {
            'name': 'Premium',
            'description': 'Watch on 4 screens at a time in Ultra HD. Download on 4 phones or tablets.',
            'price_monthly': 649.00,
            'price_yearly': 6490.00,
            'max_concurrent_streams': 4,
            'max_profiles': 5,
            'supports_uhd': True,
            'supports_hdr': True,
            'supports_dolby_atmos': True,
            'allows_downloads': True,
            'max_download_devices': 4,
            'display_order': 4
        }
    ]
    
    plans = []
    for plan_data in plans_data:
        plan, created = SubscriptionPlan.objects.get_or_create(
            name=plan_data['name'],
            defaults=plan_data
        )
        plans.append(plan)
        print(f"Created subscription plan: {plan.name} - ₹{plan.price_monthly}/month")
    
    return plans

def create_user_subscriptions(users, plans):
    """Create user subscriptions"""
    print("\nCreating user subscriptions...")
    
    subscriptions = []
    
    # Assign different plans to users
    user_plans = [
        (users[0], plans[3]),  # John - Premium
        (users[1], plans[2]),  # Jane - Standard
        (users[2], plans[1]),  # Robert - Basic
        (users[3], plans[0]),  # Sarah - Mobile
    ]
    
    for user, plan in user_plans:
        subscription, created = UserSubscription.objects.get_or_create(
            user=user,
            defaults={
                'subscription_plan': plan,
                'status': UserSubscription.SubscriptionStatus.ACTIVE,
                'current_period_start': timezone.now() - timedelta(days=15),
                'current_period_end': timezone.now() + timedelta(days=15),
                'payment_method_last_four': '4242',
                'payment_method_type': 'credit_card'
            }
        )
        subscriptions.append(subscription)
        print(f"Created subscription for {user.email}: {plan.name} - {subscription.status}")
    
    return subscriptions

def create_billing_history(users, plans):
    """Create billing history"""
    print("\nCreating billing history...")
    
    billing_records = []
    
    for i, user in enumerate(users):
        plan = plans[min(i, 3)]  # Assign different plans
        
        # Create 3 months of billing history
        for month in range(3):
            billing_date = timezone.now() - timedelta(days=30 * (month + 1))
            
            billing, created = BillingHistory.objects.get_or_create(
                user=user,
                invoice_number=f"INV-{user.id.hex[:8]}-{month+1}",
                defaults={
                    'subscription_plan': plan,
                    'amount': plan.price_monthly,
                    'currency': 'INR',
                    'payment_status': BillingHistory.PaymentStatus.COMPLETED,
                    'billing_cycle_start': billing_date,
                    'billing_cycle_end': billing_date + timedelta(days=30),
                    'payment_gateway_transaction_id': f"TXN{user.id.hex[:8]}{month+1}",
                    'receipt_url': f"https://receipts.example.com/{user.id.hex[:8]}-{month+1}"
                }
            )
            billing_records.append(billing)
    
    print(f"Created {len(billing_records)} billing history records")
    return billing_records

def create_devices(users):
    """Create devices for users"""
    print("\nCreating devices...")
    
    devices = []
    
    devices_data = [
        # John's devices
        {
            'user': users[0],
            'device_type': Device.DeviceType.MOBILE,
            'device_name': "John's iPhone",
            'device_model': 'iPhone 14 Pro',
            'os_version': 'iOS 17.2',
            'app_version': 'Netflix 8.0'
        },
        {
            'user': users[0],
            'device_type': Device.DeviceType.SMART_TV,
            'device_name': "Living Room TV",
            'device_model': 'Samsung QLED',
            'os_version': 'Tizen 6.5',
            'app_version': 'Netflix 5.2'
        },
        
        # Jane's devices
        {
            'user': users[1],
            'device_type': Device.DeviceType.MOBILE,
            'device_name': "Jane's Samsung",
            'device_model': 'Samsung Galaxy S23',
            'os_version': 'Android 14',
            'app_version': 'Netflix 8.0'
        },
        
        # Robert's devices
        {
            'user': users[2],
            'device_type': Device.DeviceType.DESKTOP,
            'device_name': "Work Laptop",
            'device_model': 'MacBook Pro',
            'os_version': 'macOS 14',
            'app_version': 'Chrome Browser'
        },
        
        # Sarah's devices
        {
            'user': users[3],
            'device_type': Device.DeviceType.TABLET,
            'device_name': "Sarah's iPad",
            'device_model': 'iPad Pro',
            'os_version': 'iPadOS 17',
            'app_version': 'Netflix 8.0'
        },
    ]
    
    for device_data in devices_data:
        device, created = Device.objects.get_or_create(
            user=device_data['user'],
            device_name=device_data['device_name'],
            defaults={
                'device_type': device_data['device_type'],
                'device_model': device_data['device_model'],
                'os_version': device_data['os_version'],
                'app_version': device_data['app_version'],
                'last_login_at': timezone.now() - timedelta(hours=12)
            }
        )
        devices.append(device)
        print(f"Created device: {device.user.email} - {device.device_name}")
    
    return devices

def create_device_logins(profiles, devices):
    """Create device login history"""
    print("\nCreating device login history...")
    
    logins = []
    
    # Map profiles to users
    profile_user_map = {}
    for profile in profiles:
        profile_user_map[profile.id] = profile.user
    
    # Create login sessions
    for profile in profiles:
        # Find a device for this user
        user_devices = [d for d in devices if d.user == profile.user]
        if user_devices:
            device = user_devices[0]
            
            # Create 5 login sessions for each profile
            for i in range(5):
                login_at = timezone.now() - timedelta(days=i, hours=i*2)
                logout_at = login_at + timedelta(hours=1)
                
                login, created = DeviceLogin.objects.get_or_create(
                    device=device,
                    profile=profile,
                    login_at=login_at,
                    defaults={
                        'ip_address': '192.168.1.' + str(100 + i),
                        'location_country': profile.user.country_code,
                        'logout_at': logout_at if i > 0 else None  # Keep current session active
                    }
                )
                logins.append(login)
    
    print(f"Created {len(logins)} device login records")
    return logins

def create_watch_history_and_interactions(profiles, movies, tv_show, episodes):
    """Create watch history and user content interactions"""
    print("\nCreating watch history and interactions...")
    
    all_content = movies + [tv_show] + list(episodes)
    
    for profile in profiles:
        print(f"\nCreating watch data for profile: {profile.name}")
        
        # Skip kid profiles for mature content
        if profile.is_kid_profile:
            available_content = []
            for c in all_content:
                # Handle Episode objects
                if isinstance(c, Episode):
                    maturity_level = c.content.maturity_level
                else:
                    maturity_level = c.maturity_level
                
                if maturity_level.minimum_age <= profile.age:
                    available_content.append(c)
        else:
            available_content = all_content
        
        # Watch 3-5 pieces of content per profile
        import random
        watched_content = random.sample(available_content, min(len(available_content), random.randint(3, 5)))
        
        for content_item in watched_content:
            # Determine if this is an episode or movie/show
            is_episode = hasattr(content_item, 'episode_details') or isinstance(content_item, Episode)
            
            # Get the actual content object if it's an episode
            if isinstance(content_item, Episode):
                content = content_item.content
            else:
                content = content_item
            
            # Create watch history
            watch_started_at = timezone.now() - timedelta(days=random.randint(1, 30))
            watch_duration = random.randint(300, content.duration_minutes * 60 if content.duration_minutes else 3600)
            watch_ended_at = watch_started_at + timedelta(seconds=watch_duration)
            
            watch_history, _ = WatchHistory.objects.get_or_create(
                profile=profile,
                content=content,
                watch_started_at=watch_started_at,
                defaults={
                    'watch_ended_at': watch_ended_at,
                    'watched_seconds': watch_duration,
                    'start_position_seconds': 0,
                    'end_position_seconds': min(watch_duration, content.duration_minutes * 60 if content.duration_minutes else watch_duration)
                }
            )
            
            # Create or update user content interaction
            interaction, created = UserContentInteraction.objects.get_or_create(
                profile=profile,
                content=content,
                defaults={
                    'total_watch_time_seconds': watch_duration,
                    'watch_count': 1,
                    'last_watched_at': watch_started_at
                }
            )
            
            if not created:
                interaction.total_watch_time_seconds += watch_duration
                interaction.watch_count += 1
                interaction.last_watched_at = watch_started_at
                interaction.save()
            
            # Sometimes leave watch progress for unfinished content
            if random.random() > 0.7:  # 30% chance
                resume_time = random.randint(0, watch_duration // 2)
                WatchProgress.objects.update_or_create(
                    profile=profile,
                    content=content,
                    defaults={
                        'resume_time_seconds': resume_time,
                        'last_watched_at': watch_started_at
                    }
                )
            
            print(f"  Watched: {content.title} ({watch_duration//60} mins)")
    
    print(f"\nCreated watch history for {len(profiles)} profiles")

def create_ratings_and_reviews(profiles, movies, tv_show):
    """Create ratings and reviews"""
    print("\nCreating ratings and reviews...")
    
    all_content = movies + [tv_show]
    
    for profile in profiles:
        # Rate 2-3 pieces of content per profile
        import random
        rated_content = random.sample(all_content, min(len(all_content), random.randint(2, 3)))
        
        for content in rated_content:
            # Create rating
            rating_value = random.randint(3, 5)  # Mostly positive ratings
            rating, _ = Rating.objects.get_or_create(
                profile=profile,
                content=content,
                defaults={
                    'rating_value': rating_value,
                    'rated_at': timezone.now() - timedelta(days=random.randint(1, 10))
                }
            )
            
            # Sometimes write a review (20% chance)
            if random.random() > 0.8:
                review_title = f"My thoughts on {content.title}"
                review_body = f"I really enjoyed watching {content.title}. "
                if content.content_type == Content.ContentType.MOVIE:
                    review_body += "The storyline was engaging and the acting was superb."
                else:
                    review_body += "The characters are well-developed and each episode leaves me wanting more."
                
                Review.objects.get_or_create(
                    profile=profile,
                    content=content,
                    defaults={
                        'title': review_title,
                        'body': review_body,
                        'contains_spoilers': False
                    }
                )
                
                print(f"  {profile.name} rated {content.title} {rating_value}/5 and wrote a review")
            else:
                print(f"  {profile.name} rated {content.title} {rating_value}/5")

def create_downloads(profiles, movies, devices):
    """Create download records"""
    print("\nCreating download records...")
    
    downloads = []
    
    for profile in profiles:
        # Each profile downloads 1-2 items
        import random
        profile_devices = [d for d in devices if d.user == profile.user]
        
        if profile_devices and movies:
            device = profile_devices[0]
            num_downloads = random.randint(1, min(2, len(movies)))
            downloaded_movies = random.sample(movies, num_downloads)
            
            for movie in downloaded_movies:
                # Skip mature content for kid profiles
                if profile.is_kid_profile and movie.maturity_level.minimum_age > profile.age:
                    continue
                
                # Determine video quality based on user's subscription
                subscription = UserSubscription.objects.filter(user=profile.user).first()
                video_quality = Download.VideoQuality.HD
                if subscription and subscription.subscription_plan.supports_uhd:
                    video_quality = random.choice([Download.VideoQuality.HD, Download.VideoQuality.UHD])
                
                download_status = random.choice([
                    Download.DownloadStatus.COMPLETED,
                    Download.DownloadStatus.COMPLETED,
                    Download.DownloadStatus.EXPIRED  # Some expired downloads
                ])
                
                downloaded_at = timezone.now() - timedelta(days=random.randint(1, 45))
                expires_at = downloaded_at + timedelta(days=30)
                
                download, created = Download.objects.get_or_create(
                    profile=profile,
                    content=movie,
                    device=device,
                    defaults={
                        'video_quality': video_quality,
                        'file_size_bytes': random.randint(500000000, 2000000000),  # 500MB - 2GB
                        'download_path': f"/downloads/{profile.id}/{movie.id}.mp4",
                        'download_status': download_status,
                        'progress_percentage': 100,
                        'downloaded_at': downloaded_at,
                        'expires_at': expires_at
                    }
                )
                downloads.append(download)
                print(f"  {profile.name} downloaded {movie.title} ({video_quality})")
    
    print(f"\nCreated {len(downloads)} download records")

def main():
    """Main function to populate all data"""
    print("Starting data population...")
    print("=" * 50)
    
    try:
        # Clear existing data (optional - comment out if you want to keep existing data)
        # User.objects.all().delete()
        # print("Cleared existing data")
        
        # Create data in order
        users, profiles = create_users_and_profiles()
        maturity_levels = create_maturity_levels()
        genres = create_genres()
        cast_members = create_cast_members()
        movies = create_content_and_movies(maturity_levels, genres, cast_members)
        tv_show, episodes = create_tv_shows_and_episodes(maturity_levels, genres, cast_members)
        plans = create_subscription_plans()
        subscriptions = create_user_subscriptions(users, plans)
        billing_history = create_billing_history(users, plans)
        devices = create_devices(users)
        device_logins = create_device_logins(profiles, devices)
        create_watch_history_and_interactions(profiles, movies, tv_show, episodes)
        create_ratings_and_reviews(profiles, movies, tv_show)
        create_downloads(profiles, movies, devices)
        
        print("\n" + "=" * 50)
        print("Data population completed successfully!")
        print("\nSummary:")
        print(f"  Users: {User.objects.count()}")
        print(f"  Profiles: {Profile.objects.count()}")
        print(f"  Content: {Content.objects.count()} (Movies: {Movie.objects.count()}, TV Shows: {TVShow.objects.count()})")
        print(f"  Episodes: {Episode.objects.count()}")
        print(f"  Watch History: {WatchHistory.objects.count()}")
        print(f"  Ratings: {Rating.objects.count()}")
        print(f"  Devices: {Device.objects.count()}")
        print(f"  Downloads: {Download.objects.count()}")
        
    except Exception as e:
        print(f"\nError occurred: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()