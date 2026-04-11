---
name: mubert-manage
description: Manage Mubert Music API v3 licenses and customers. Use when creating or listing customers, retrieving or updating licenses, configuring webhooks, or managing API access tokens. Service-level administration for the Mubert B2B royalty-free music platform.
compatibility: Requires internet access and Mubert service credentials (company-id + license-token).
metadata:
  author: mubert
  version: "3.0"
  openclaw:
    requires:
      env:
        - MUBERT_COMPANY_ID
        - MUBERT_LICENSE_TOKEN
    primaryEnv: MUBERT_LICENSE_TOKEN
---

# Mubert License & Customer Management

Manage licenses, customers, and webhooks via the Mubert Music API v3 service endpoints. Mubert provides royalty-free AI-generated music — use these endpoints to provision access for your users so they can generate and stream music within your app without any copyright concerns.

These endpoints require company-level credentials (`company-id` + `license-token`).

> **Setup:** See [Installation Guide](references/installation.md) for credentials.

## Quick Start

### Python

```python
import requests

BASE = "https://music-api.mubert.com/api/v3"
HEADERS = {
    "company-id": COMPANY_ID,
    "license-token": LICENSE_TOKEN,
    "Content-Type": "application/json",
}

# Create a customer
resp = requests.post(f"{BASE}/service/customers", headers=HEADERS, json={
    "custom_id": "my-app-user-1",
})
customer = resp.json()
customer_id = customer["access"]["id"]
access_token = customer["access"]["token"]
print(f"Customer created: {customer_id}")

# List all licenses
licenses = requests.get(f"{BASE}/service/licenses", headers=HEADERS).json()

# List all customers
customers = requests.get(f"{BASE}/service/customers", headers=HEADERS, params={
    "limit": 50,
    "offset": 0,
}).json()
```

### TypeScript

```typescript
const BASE = "https://music-api.mubert.com/api/v3";
const HEADERS = {
  "company-id": COMPANY_ID,
  "license-token": LICENSE_TOKEN,
  "Content-Type": "application/json",
};

// Create a customer
const createRes = await fetch(`${BASE}/service/customers`, {
  method: "POST",
  headers: HEADERS,
  body: JSON.stringify({ custom_id: "my-app-user-1" }),
});
const customer = await createRes.json();
const customerId = customer.access.id;
const accessToken = customer.access.token;
console.log(`Customer created: ${customerId}`);

// List all licenses
const licensesRes = await fetch(`${BASE}/service/licenses`, {
  headers: HEADERS,
});
const licenses = await licensesRes.json();

// List all customers
const customersRes = await fetch(
  `${BASE}/service/customers?limit=50&offset=0`,
  { headers: HEADERS },
);
const customers = await customersRes.json();
```

### cURL

```bash
# Create a customer
curl -X POST "https://music-api.mubert.com/api/v3/service/customers" \
  -H "company-id: $MUBERT_COMPANY_ID" \
  -H "license-token: $MUBERT_LICENSE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"custom_id": "my-app-user-1"}'

# List licenses
curl -X GET "https://music-api.mubert.com/api/v3/service/licenses" \
  -H "company-id: $MUBERT_COMPANY_ID" \
  -H "license-token: $MUBERT_LICENSE_TOKEN"

# List customers
curl -X GET "https://music-api.mubert.com/api/v3/service/customers?limit=50" \
  -H "company-id: $MUBERT_COMPANY_ID" \
  -H "license-token: $MUBERT_LICENSE_TOKEN"
```

## Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/service/licenses` | GET | List all licenses |
| `/service/licenses/{id}` | GET | Get specific license |
| `/service/licenses/{id}` | PUT | Update license webhook |
| `/service/customers` | POST | Create customer |
| `/service/customers` | GET | List customers (paginated) |
| `/service/customers/{id}` | GET | Get customer by ID |
| `/service/customers/custom-id/{id}` | GET | Get customer by custom ID |
| `/service/customers/{id}` | DELETE | Delete customer |

See [API Reference](references/api_reference.md) for full parameter details.

## Customer Management

### Create Customer

```json
{ "custom_id": "your-user-id" }
```

`custom_id` max 255 characters. The response contains:
- `access.id` — use as `customer-id` header for public endpoints
- `access.token` — use as `access-token` header for public endpoints

### Get Customer

By internal ID:
```python
requests.get(f"{BASE}/service/customers/{customer_id}", headers=HEADERS)
```

```typescript
await fetch(`${BASE}/service/customers/${customerId}`, { headers: HEADERS });
```

By your custom ID:
```python
requests.get(f"{BASE}/service/customers/custom-id/{custom_id}", headers=HEADERS)
```

```typescript
await fetch(`${BASE}/service/customers/custom-id/${customId}`, { headers: HEADERS });
```

### Delete Customer

```python
requests.delete(f"{BASE}/service/customers/{customer_id}", headers=HEADERS)
# Returns 204 No Content
```

```typescript
await fetch(`${BASE}/service/customers/${customerId}`, {
  method: "DELETE",
  headers: HEADERS,
});
```

## License Management

### List & Get Licenses

```python
# All licenses
licenses = requests.get(f"{BASE}/service/licenses", headers=HEADERS).json()

# Specific license
license = requests.get(f"{BASE}/service/licenses/{license_id}", headers=HEADERS).json()
```

```typescript
const licenses = await (
  await fetch(`${BASE}/service/licenses`, { headers: HEADERS })
).json();

const license = await (
  await fetch(`${BASE}/service/licenses/${licenseId}`, { headers: HEADERS })
).json();
```

License model includes: features, bitrates, formats, modes, limits, and usage statistics.

### Configure Webhook

Receive notifications when track generation completes:

```python
requests.put(f"{BASE}/service/licenses/{license_id}", headers=HEADERS, json={
    "webhook_url": "https://your-server.com/webhook",
    "webhook_enabled": True,
})
```

```typescript
await fetch(`${BASE}/service/licenses/${licenseId}`, {
  method: "PUT",
  headers: HEADERS,
  body: JSON.stringify({
    webhook_url: "https://your-server.com/webhook",
    webhook_enabled: true,
  }),
});
```

Webhook payload contains track models with `id`, `session_id`, `duration`, `intensity`, `mode`, `key`, `bpm`, and `generations` array (each with `status`, `url`, `expired_at`).

## Authentication

| Headers | Use case |
|---------|----------|
| `company-id` + `license-token` | All service endpoints |

## Error Handling

- **401** - Invalid credentials (company-id/license-token)
- **404** - Customer or license not found
- **422** - Invalid parameters

## Related Skills

After creating a customer and obtaining `customer-id` + `access-token`, use these skills:
- **mubert-generate** — generate, edit, and browse royalty-free music tracks
- **mubert-streaming** — stream real-time AI-generated music

## References

- [Installation Guide](references/installation.md)
- [API Reference](references/api_reference.md)
