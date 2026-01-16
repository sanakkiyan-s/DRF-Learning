# Netflix Clone API Documentation

Base URL: `http://127.0.0.1:8000/api`

## Table of Contents
- [Authentication](#authentication)
- [User Management](#user-management)
- [Subscription & Payments](#subscription--payments)
- [Profiles](#profiles)
- [Content](#content)
- [User Interactions](#user-interactions)
- [Device Management & Streaming](#device-management--streaming)
- [Downloads](#downloads)

---

## Authentication

### Login (Device-Aware)
```http
POST /auth/login/
```

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response (200 OK):**
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "device_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
}
```

**Note:** The `device_id` is extracted from the User-Agent header and should be stored for subsequent requests.

### Refresh Token
```http
POST /auth/refresh/
```

**Request Body:**
```json
{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

---

## User Management

### Create Account
```http
POST /accounts/
```

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "password": "securePassword123",
  "country_code": "+1",
  "phone_number": "1234567890"
}
```

---

## Subscription & Payments

### List Subscription Plans
```http
GET /plans/
```

**Response:**
```json
[
  {
    "id": "uuid",
    "name": "Premium",
    "price_monthly": 649.00,
    "max_concurrent_streams": 4,
    "max_profiles": 5,
    "supports_uhd": true,
    "allows_downloads": true,
    "max_download_devices": 4
  }
]
```

### Get Subscription Status
```http
GET /subscription/status/
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "status": "active",
  "plan_name": "Premium",
  "current_period_end": "2026-02-16T12:00:00Z",
  "cancel_at_period_end": false,
  "can_stream": true,
  "max_streams": 4
}
```

### Create Stripe Checkout Session
```http
POST /payment/stripe/checkout/
```

**Request Body:**
```json
{
  "plan_id": "uuid",
  "interval": "monthly"
}
```

**Response:**
```json
{
  "checkout_url": "https://checkout.stripe.com/...",
  "session_id": "cs_test_..."
}
```

### Manage Subscription

#### Get Billing Portal URL
```http
GET /subscription/manage/
```

**Response:**
```json
{
  "portal_url": "https://billing.stripe.com/..."
}
```

#### Cancel Subscription
```http
POST /subscription/manage/
```

**Request Body:**
```json
{
  "action": "cancel"
}
```

**Response:**
```json
{
  "message": "Subscription will cancel at end of billing period",
  "end_date": "2026-02-16T12:00:00Z"
}
```

#### Reactivate Subscription
```http
POST /subscription/manage/
```

**Request Body:**
```json
{
  "action": "reactivate"
}
```

### Billing History
```http
GET /subscription/billing-history/
```

**Response:**
```json
[
  {
    "date": "2026-01-16T12:00:00Z",
    "amount": 649.00,
    "currency": "INR",
    "plan": "Premium",
    "status": "completed",
    "invoice_number": "INV-001"
  }
]
```

---

## Profiles

### List Profiles
```http
GET /profiles/
```

**Headers:**
```
Authorization: Bearer <access_token>
```

### Create Profile
```http
POST /profiles/
```

**Request Body:**
```json
{
  "name": "Kids",
  "is_kid_profile": true,
  "avatar_url": "https://example.com/avatar.png",
  "language_code": "en"
}
```

**Error Response (403):** If profile limit exceeded
```json
{
  "error": "Profile limit reached. Your plan allows a maximum of 5 profiles."
}
```

### Select Profile (Start Streaming)
```http
POST /profile/select/
```

**Headers:**
```
Authorization: Bearer <access_token>
X-Device-ID: <device_id>
```

**Request Body:**
```json
{
  "profile_id": "uuid"
}
```

**Error Response (403):** If concurrent stream limit exceeded
```json
{
  "error": "Too many concurrent streams",
  "max_streams": 2,
  "active_streams": 2
}
```

---

## Content

### List Movies
```http
GET /movies/
```

**Query Parameters:**
- `genre`: Filter by genre name (e.g., `?genre=Action`)

**Response:**
```json
[
  {
    "id": "uuid",
    "title": "Inception",
    "description": "A thief who steals...",
    "director": "Christopher Nolan",
    "release_date": "2010-07-16",
    "duration_minutes": 148,
    "poster_image_url": "https://...",
    "genres": ["Action", "Sci-Fi"],
    "cast": [
      {
        "name": "Leonardo DiCaprio",
        "character_name": "Cobb",
        "role_type": "actor"
      }
    ]
  }
]
```

### Get Movie Details
```http
GET /movies/{id}/
```

### List TV Shows
```http
GET /tv-shows/
```

**Response:**
```json
[
  {
    "id": "uuid",
    "title": "Breaking Bad",
    "total_seasons": 5,
    "total_episodes": 62,
    "status": "completed",
    "seasons": [
      {
        "season_number": 1,
        "episodes": [
          {
            "episode_number": 1,
            "title": "Pilot",
            "duration_minutes": 58
          }
        ]
      }
    ]
  }
]
```

### List Genres
```http
GET /genres/
```

---

## User Interactions

**All interaction endpoints require these headers:**
```
Authorization: Bearer <access_token>
X-Profile-ID: <profile_uuid>
```

### Watch History
```http
POST /watch-history/
```

**Request Body:**
```json
{
  "content_id": "uuid",
  "watched_seconds": 1800,
  "start_position_seconds": 0,
  "end_position_seconds": 1800
}
```

### Watch Progress (Continue Watching)
```http
POST /watch-progress/
```

**Request Body:**
```json
{
  "content_id": "uuid",
  "resume_time_seconds": 1800
}
```

**Note:** This endpoint uses upsert logic - it creates or updates the resume point.

### Rate Content
```http
POST /ratings/
```

**Request Body:**
```json
{
  "content_id": "uuid",
  "rating_value": 5
}
```

**Validation:** `rating_value` must be between 1-5.

### Write Review
```http
POST /reviews/
```

**Request Body:**
```json
{
  "content_id": "uuid",
  "title": "Amazing Movie!",
  "body": "This film is a masterpiece...",
  "contains_spoilers": false
}
```

### Watchlist (My List)

#### Add to Watchlist
```http
POST /watchlist/
```

**Request Body:**
```json
{
  "content_id": "uuid"
}
```

#### List Watchlist
```http
GET /watchlist/
```

#### Remove from Watchlist
```http
DELETE /watchlist/{id}/
```

**Note:** This sets `is_in_watchlist=False` instead of deleting the record.

---

## Device Management & Streaming

### Get Active Streams
```http
GET /stream/active/
```

**Headers:**
```
Authorization: Bearer <access_token>
```

**Response:**
```json
{
  "max_streams": 2,
  "active_count": 1,
  "sessions": [
    {
      "session_id": "uuid",
      "device_name": "Chrome on Windows",
      "profile_name": "Dad",
      "login_at": "2026-01-16T10:00:00Z"
    }
  ]
}
```

### End Stream Session
```http
POST /stream/logout/
```

**Option 1:** Logout specific session
```json
{
  "session_id": "uuid"
}
```

**Option 2:** Logout all sessions on current device
```
Headers:
X-Device-ID: <device_id>
```

---

## Downloads

**All download endpoints require:**
```
Authorization: Bearer <access_token>
X-Profile-ID: <profile_uuid>
```

### Create Download
```http
POST /downloads/
```

**Request Body:**
```json
{
  "content_id": "uuid",
  "device_id": "uuid",
  "video_quality": "UHD"
}
```

**Quality Options:** `SD`, `HD`, `FHD`, `UHD`

**Success Response (201):**
```json
{
  "id": "uuid",
  "content": {
    "id": "uuid",
    "title": "Inception",
    "poster_image_url": "https://..."
  },
  "device_name": "Chrome on Windows",
  "video_quality": "HD",
  "download_status": "pending",
  "expires_at": "2026-02-15T10:00:00Z",
  "notice": "Quality downgraded to HD (UHD not available on your plan)"
}
```

**Error Responses:**

**403 - Plan doesn't allow downloads:**
```json
{
  "error": "Downloads not available on your plan",
  "plan_name": "Basic"
}
```

**403 - Device limit reached:**
```json
{
  "error": "Maximum download devices reached",
  "max_devices": 2,
  "active_devices": 2
}
```

### List Downloads
```http
GET /downloads/
```

### Delete Download
```http
DELETE /downloads/{id}/
```

---

## Subscription Plan Limits Summary

| Feature | Basic | Standard | Premium |
|---------|-------|----------|---------|
| Concurrent Streams | 1 | 2 | 4 |
| Max Profiles | 1 | 2 | 5 |
| Downloads | ❌ | ✅ (2 devices) | ✅ (4 devices) |
| UHD Quality | ❌ | ❌ | ✅ |
| HDR/Dolby Atmos | ❌ | ❌ | ✅ |

---

## Error Codes

| Status | Meaning |
|--------|---------|
| 400 | Bad Request (validation errors) |
| 401 | Unauthorized (missing/invalid token) |
| 403 | Forbidden (plan limits exceeded) |
| 404 | Not Found |
| 500 | Internal Server Error |

---

## Webhook Integration (Stripe)

**Endpoint:** `POST /payment/stripe/webhook/`

**Events Handled:**
- `checkout.session.completed` - New subscription created
- `invoice.payment_succeeded` - Payment received
- `invoice.payment_failed` - Payment failed
- `customer.subscription.updated` - Subscription modified
- `customer.subscription.deleted` - Subscription cancelled
- `customer.subscription.trial_will_end` - Trial ending soon

**Note:** Webhooks use signature verification for security.
