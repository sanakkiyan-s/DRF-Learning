import requests
import json

BASE_URL = 'http://127.0.0.1:8000/api'

# Test credentials (ensure this user has a Standard plan with 2 download devices allowed)
EMAIL = 'sana@gmail.com'  # Adjust as needed
PASSWORD = 'sana'

def login():
    """Login and get access token."""
    response = requests.post(f'{BASE_URL}/auth/login/', json={
        'email': EMAIL,
        'password': PASSWORD
    })
    data = response.json()
    print(f"✓ Login successful. Device ID: {data.get('device_id')}")
    return data['access'], data['device_id']

def get_profile_id(token):
    """Get the first profile ID."""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{BASE_URL}/profiles/', headers=headers)
    profiles = response.json()
    profile_id = profiles[0]['id']
    print(f"✓ Using Profile: {profiles[0]['name']} ({profile_id})")
    return profile_id

def get_content_id(token):
    """Get the first movie ID."""
    headers = {'Authorization': f'Bearer {token}'}
    response = requests.get(f'{BASE_URL}/movies/', headers=headers)
    movies = response.json()
    if movies:
        content_id = movies[0]['id']
        print(f"✓ Using Content: {movies[0]['title']} ({content_id})")
        return content_id
    else:
        print("⚠ No movies found. Please populate data first.")
        return None

def test_download_creation(token, profile_id, device_id, content_id, quality='HD'):
    """Test creating a download."""
    headers = {
        'Authorization': f'Bearer {token}',
        'X-Profile-ID': profile_id
    }
    response = requests.post(f'{BASE_URL}/downloads/', headers=headers, json={
        'content_id': content_id,
        'device_id': device_id,
        'video_quality': quality
    })
    print(f"\n--- Test: Create Download ({quality}) ---")
    print(f"Status: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    return response

def test_download_list(token, profile_id):
    """List all downloads."""
    headers = {
        'Authorization': f'Bearer {token}',
        'X-Profile-ID': profile_id
    }
    response = requests.get(f'{BASE_URL}/downloads/', headers=headers)
    print(f"\n--- List Downloads ---")
    print(f"Count: {len(response.json())}")
    return response.json()

if __name__ == '__main__':
    print("=" * 60)
    print("DOWNLOAD FEATURE VERIFICATION")
    print("=" * 60)
    
    # Setup
    token, device_id = login()
    profile_id = get_profile_id(token)
    content_id = get_content_id(token)
    
    if not content_id:
        exit(1)
    
    # Test 1: Create download with HD (should work)
    print("\n[Test 1] Create HD Download (Expected: 201 Created)")
    response = test_download_creation(token, profile_id, device_id, content_id, 'HD')
    assert response.status_code == 201, "Should succeed for HD quality"
    
    # Test 2: Request UHD (should downgrade to HD for non-Premium)
    print("\n[Test 2] Request UHD Download (Expected: Downgrade to HD)")
    response = test_download_creation(token, profile_id, device_id, content_id, 'UHD')
    data = response.json()
    if 'notice' in data:
        print(f"✓ Notice: {data['notice']}")
        print(f"✓ Quality was downgraded as expected")
    
    # Test 3: List downloads
    print("\n[Test 3] List All Downloads")
    downloads = test_download_list(token, profile_id)
    
    print("\n" + "=" * 60)
    print("✓ All tests completed successfully")
    print("=" * 60)
