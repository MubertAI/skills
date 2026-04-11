# API Reference — License & Customer Management

Base URL: `https://music-api.mubert.com/api/v3`

**Headers:** `company-id`, `license-token`, `Content-Type: application/json`

---

## Licenses

### `GET /service/licenses` - List all licenses

**Response:** `200 OK` - Array of license models with features, bitrates, formats, modes, limits, statistics.

---

### `GET /service/licenses/{license_id}` - Get license

**Response:** `200 OK` - Single license model.

---

### `PUT /service/licenses/{license_id}` - Update license webhook

**Body:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `webhook_url` | string | No | URL to receive webhook notifications |
| `webhook_enabled` | boolean | No | Enable/disable webhook |

Webhook payload contains track models:

```json
{
  "id": "track-id",
  "session_id": "session-id",
  "duration": 30,
  "intensity": "high",
  "mode": "track",
  "key": "C",
  "bpm": 120,
  "generations": [
    {
      "session_id": "gen-session-id",
      "format": "mp3",
      "bitrate": 128,
      "status": "completed",
      "generated_at": "2024-01-01T00:00:00Z",
      "expired_at": "2024-02-01T00:00:00Z",
      "created_at": "2024-01-01T00:00:00Z",
      "url": "https://..."
    }
  ]
}
```

**Response:** `200 OK` - Updated license model.

---

## Customers

### `POST /service/customers` - Create customer

**Body:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `custom_id` | string | Yes | Your identifier, max 255 characters |

**Response:** `200 OK`

```json
{
  "id": "customer-uuid",
  "company_id": "company-uuid",
  "custom_id": "my-app-user-1",
  "status": "active",
  "access": {
    "id": "customer-id-for-public-api",
    "customer_id": "customer-uuid",
    "license_id": "license-uuid",
    "token": "access-token-for-public-api",
    "expired_at": "2025-01-01T00:00:00Z"
  },
  "customer_limits": {
    "daily_streaming_duration": 0,
    "daily_streaming_duration_limit": 86400,
    "monthly_streaming_duration": 0,
    "monthly_streaming_duration_limit": 2592000,
    "total_streaming_duration": 0,
    "total_streaming_duration_limit": -1
  }
}
```

Use `access.id` as `customer-id` and `access.token` as `access-token` for public endpoints (track generation, streaming, library).

---

### `GET /service/customers` - List customers

**Query Parameters:**

| Parameter | Type | Required |
|-----------|------|----------|
| `limit` | integer | No |
| `offset` | integer | No |

**Response:** `200 OK` - Paginated array of customer models.

---

### `GET /service/customers/{customer_id}` - Get customer by ID

**Response:** `200 OK` - Customer model.

---

### `GET /service/customers/custom-id/{custom_id}` - Get customer by custom ID

**Response:** `200 OK` - Customer model.

---

### `DELETE /service/customers/{customer_id}` - Delete customer

**Response:** `204 No Content`
