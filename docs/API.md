# API Documentation

## Base URL
```
https://your-app.onrender.com/api/v1
```

## Authentication

### JWT Token Authentication
All protected endpoints require a JWT token in the Authorization header:
```
Authorization: Bearer <access_token>
```

### Obtaining Tokens
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

Response:
```json
{
  "access": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": "tourist"
  }
}
```

### Refreshing Tokens
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9..."
}
```

## Endpoints

### Destinations

#### List Destinations
```http
GET /api/v1/destinations/
```

Query Parameters:
- `search` - Search by name
- `category` - Filter by category ID
- `district` - Filter by district
- `province` - Filter by province
- `min_rating` - Minimum rating
- `max_rating` - Maximum rating
- `has_images` - Filter destinations with images (true/false)
- `verified_only` - Show only verified destinations
- `ordering` - Sort by: name, rating, views, created_at
- `page` - Page number
- `limit` - Results per page (default: 10)

Response:
```json
{
  "count": 1000,
  "next": "https://api.example.com/api/v1/destinations/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "Phewa Lake",
      "slug": "phewa-lake",
      "description": "A beautiful lake in Pokhara",
      "latitude": 28.2096,
      "longitude": 83.9560,
      "city": "Pokhara",
      "district": "Kaski",
      "province": "Gandaki",
      "average_rating": 4.5,
      "ratings_count": 128,
      "views_count": 5420,
      "cover_image_url": "https://example.com/images/phewa.jpg",
      "category": {
        "id": 1,
        "name": "Lakes"
      }
    }
  ]
}
```

#### Get Destination Detail
```http
GET /api/v1/destinations/{slug}/
```

#### Get Destination Gallery
```http
GET /api/v1/destinations/{slug}/gallery/
```

#### Get Nearby Destinations
```http
GET /api/v1/destinations/nearby/?latitude=28.21&longitude=83.96&radius_km=20
```

### Hotels

#### List Hotels
```http
GET /api/v1/hotels/?destination={id}
```

#### Get Hotel Detail
```http
GET /api/v1/hotels/{id}/
```

### Reviews

#### List Reviews
```http
GET /api/v1/reviews/?destination={id}
```

#### Create Review
```http
POST /api/v1/reviews/
Authorization: Bearer <token>
Content-Type: application/json

{
  "destination": 1,
  "comment": "Amazing place!"
}
```

### Ratings

#### Create Rating
```http
POST /api/v1/ratings/
Authorization: Bearer <token>
Content-Type: application/json

{
  "destination": 1,
  "value": 5
}
```

### Itineraries

#### List Itineraries
```http
GET /api/v1/itineraries/
Authorization: Bearer <token>
```

#### Create Itinerary
```http
POST /api/v1/itineraries/
Authorization: Bearer <token>
Content-Type: application/json

{
  "title": "Annapurna Circuit",
  "start_date": "2026-04-01",
  "num_days": 14,
  "category_filter": [1, 2]
}
```

### Navigation

#### Calculate Route
```http
POST /api/v1/navigation/route
Content-Type: application/json

{
  "start_latitude": 28.21,
  "start_longitude": 83.96,
  "end_latitude": 28.23,
  "end_longitude": 83.99
}
```

### Weather

#### Get Current Weather
```http
GET /api/v1/weather/current/?lat=28.21&lng=83.96
```

#### Get Weather Forecast
```http
GET /api/v1/weather/forecast/?lat=28.21&lng=83.96&days=5
```

### User Profile

#### Get Profile
```http
GET /api/v1/auth/profile/
Authorization: Bearer <token>
```

#### Update Profile
```http
PATCH /api/v1/auth/profile/
Authorization: Bearer <token>
Content-Type: application/json

{
  "first_name": "John",
  "last_name": "Doe"
}
```

### Location

#### Update Location
```http
POST /api/v1/auth/update-location/
Authorization: Bearer <token>
Content-Type: application/json

{
  "latitude": 28.21,
  "longitude": 83.96,
  "accuracy": 10
}
```

#### Get Location History
```http
GET /api/v1/location-history/
Authorization: Bearer <token>
```

### Health Check
```http
GET /api/v1/health/
```

Response:
```json
{
  "status": "healthy",
  "checks": {
    "database": "ok",
    "cache": "ok",
    "static_files": "ok"
  }
}
```

## Error Responses

All errors follow this format:
```json
{
  "error": {
    "code": "error_code",
    "message": "Human readable error message",
    "details": {}
  }
}
```

Common error codes:
- `authentication_required` - Missing or invalid token
- `permission_denied` - Insufficient permissions
- `not_found` - Resource not found
- `validation_error` - Invalid input data
- `rate_limit_exceeded` - Too many requests

## Rate Limits

| Endpoint | Limit |
|----------|-------|
| Search | 30/min |
| Chatbot | 20/min |
| Public config | 60/min |
| Auth endpoints | 10/min |

## Pagination

All list endpoints support pagination:
- `page` - Page number (default: 1)
- `limit` - Results per page (default: 10, max: 100)

## Filtering

Most list endpoints support filtering via query parameters. See individual endpoint documentation for available filters.

## Sorting

Use the `ordering` parameter to sort results:
- `name` - Sort by name (ascending)
- `-name` - Sort by name (descending)
- `rating` - Sort by rating (ascending)
- `-rating` - Sort by rating (descending)
- `created_at` - Sort by creation date (ascending)
- `-created_at` - Sort by creation date (descending)
