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
if resp.status_code != 200:
    # 422 -> {"message": ..., "errors": {"custom_id": [...]}}; 401 -> {"message", "code"}
    raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")
customer = resp.json()["data"]
customer_id = customer["id"]                  # -> customer-id header
access_token = customer["access"]["token"]    # -> access-token header
print(f"Customer created: {customer_id}")

# List all licenses
licenses = requests.get(f"{BASE}/service/licenses", headers=HEADERS).json()["data"]

# List all customers
customers = requests.get(f"{BASE}/service/customers", headers=HEADERS, params={
    "limit": 50,
    "offset": 0,
}).json()["data"]
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
if (!createRes.ok) {
  // 422 -> { message, errors: { custom_id: [...] } }; 401 -> { message, code }
  throw new Error(`HTTP ${createRes.status}: ${await createRes.text()}`);
}
const { data: customer } = await createRes.json();
const customerId = customer.id;                 // -> customer-id header
const accessToken = customer.access.token;      // -> access-token header
console.log(`Customer created: ${customerId}`);

// List all licenses
const licensesRes = await fetch(`${BASE}/service/licenses`, {
  headers: HEADERS,
});
const { data: licenses } = await licensesRes.json();

// List all customers
const customersRes = await fetch(
  `${BASE}/service/customers?limit=50&offset=0`,
  { headers: HEADERS },
);
const { data: customers } = await customersRes.json();
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
| `/service/customers` | POST | Create **or fetch** customer (idempotent by `custom_id`) |
| `/service/customers` | GET | List customers (paginated; each item includes that customer's plaintext `access.token` and full `customer_limits`) |
| `/service/customers/{id}` | GET | Get customer by ID |
| `/service/customers/custom-id/{custom_id}` | GET | Get customer by custom ID |
| `/service/customers/{id}` | PUT | Rename customer (`custom_id`); returns the customer **without** `access`/`customer_limits` |
| `/service/customers/{id}` | DELETE | Delete customer |

See [API Reference](references/api_reference.md) for full parameter details.

## Customer Management

### Create Customer

```json
{ "custom_id": "your-user-id" }
```

`custom_id` charset: `^[a-zA-Z0-9._@-]+$`, length 1–255. Spaces, `+`, unicode → 422. (So a raw email containing `+` is not a usable `custom_id`.)

The response is `200` — never `201`. Check the status before reading `data`: an error body has no `data` key, so `resp.json()["data"]` raises `KeyError` instead of showing you `message` (and `errors` on a 422).

The response body is wrapped in `data`, and the credentials for public endpoints come from two different levels of it:
- `data.id` — the customer's own ID — use as the `customer-id` header
- `data.access.token` — use as the `access-token` header

`data.access.id` is the ID of the access-token record itself and is not accepted by any endpoint — sending it as `customer-id` returns `401` even for a valid customer. (`data.access.customer_id` is the same value as `data.id` and works too.)

The per-customer limits live at **`data.access.customer_limits`**, nested inside `access` — not beside it. `data["customer_limits"]` raises `KeyError` on every endpoint that returns a customer. A fresh customer gets `-1` (unlimited) for all of them, including the daily and monthly streaming limits: those are per-customer column defaults, and the copy from the licence's `customer_*_streaming_duration_limit` fields is broken upstream, so never assume a licence value was inherited.

`POST /service/customers` is an **idempotent find-or-create**: reposting an existing `custom_id` returns the same customer, the same access-token record and the same token; a soft-deleted customer is restored with its original id. A duplicate `custom_id` is never an error.

Lost a token? `GET /service/customers/custom-id/{custom_id}` returns the identical `access.token` read-only — prefer it over reposting, which would resurrect a soft-deleted customer as a side effect.

Access tokens expire **one month** after issue, auto-extended only if used within 7 days of expiry; otherwise `403 AccessTokenExpired`. There is no refresh endpoint — once a token has expired, reposting the same `custom_id` mints a fresh one.

### Rename Customer

```python
resp = requests.put(f"{BASE}/service/customers/{customer_id}", headers=HEADERS, json={
    "custom_id": "my-app-user-1-renamed",
})
if resp.status_code != 200:
    # 422 -> bad charset/length; 500 -> the new custom_id is already taken
    raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")
renamed = resp.json()["data"]   # id, company_id, custom_id, status — no `access`
```

```typescript
const renameRes = await fetch(`${BASE}/service/customers/${customerId}`, {
  method: "PUT",
  headers: HEADERS,
  body: JSON.stringify({ custom_id: "my-app-user-1-renamed" }),
});
const { data: renamed } = await renameRes.json();
```

`custom_id` follows the same rules as on create (a bad value is a `422`). The update response does **not** eager-load the relations, so it carries no `access` and no `customer_limits` — exactly `id`, `company_id`, `custom_id`, `status`.

Renaming onto a `custom_id` that is already taken returns **`500`**, including when the holder is only soft-deleted: uniqueness is not validated. Check the name is free first.

### List Customers

Defaults are `offset=0`, `limit=100`. `limit=0` or a negative limit is silently treated as `100`, not as an empty page; there is no server-side maximum (`limit=100000` is echoed back verbatim), and a negative `offset` is echoed back rather than rejected. Non-integer values return `422`. `meta` carries exactly `offset`, `limit`, `total`.

`GET /service/customers` also accepts undocumented `order` and `order_by` parameters. **Avoid them:** they are unvalidated, and a value outside `asc`/`desc` (or an unknown column) returns `500 {"message": "Server Error"}`.

Every item in the list carries that customer's plaintext `access.token`, so one call can dump every customer's live credentials — do not log the response.

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

The `204` has an empty body — do not call `.json()` on it.

Customer deletion is asynchronous for the customer's own credentials: measured **60.6 s** before the pair starts returning 401 (service-side lookups 404 immediately). Concretely: the deleted customer's `customer-id` + `access-token` kept returning `200` on `/public/*` up to t+58.1 s and first returned `401 Unauthenticated` (not `403`) at t+60.6 s, while `GET /service/customers/{id}` and `/custom-id/{x}` returned `404` in the same second as the `204`. Don't treat a successful public call right after deletion as a failed revocation.

The delete is a soft delete: reposting the same `custom_id` restores the customer with its original id.

## License Management

### List & Get Licenses

```python
# All licenses
licenses = requests.get(f"{BASE}/service/licenses", headers=HEADERS).json()["data"]

# Specific license
license = requests.get(f"{BASE}/service/licenses/{license_id}", headers=HEADERS).json()["data"]
```

```typescript
const { data: licenses } = await (
  await fetch(`${BASE}/service/licenses`, { headers: HEADERS })
).json();

const { data: license } = await (
  await fetch(`${BASE}/service/licenses/${licenseId}`, { headers: HEADERS })
).json();
```

License model fields: `id`, `company_id`, `type`, `status`, `webhook_url`, `webhook_enabled`, `track_expiration_time`, `expired_at`, the allow-all flags plus allowed-value arrays (`allow_all_features`/`features`, `allow_all_bitrates`/`bitrates`, `allow_all_intensities`/`intensities`, `allow_all_formats`/`track_formats`, `allow_all_modes`/`track_modes`), the per-license defaults (`default_bitrate`, `default_intensity`, `default_format`, `default_mode`), and `license_limits` — which holds both the limits (`-1` = unlimited) and the usage counters (`total_tracks_count`, `monthly_streaming_duration`, `customers_count`, `daily_reset_at`, …).

The field names are `track_formats`, `track_modes` and `license_limits` — not `formats`, `modes` or `limits` — and usage statistics are not a separate field.

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

`webhook_url` is capped at 255 characters and is nullable — send `null` to clear it.

> The webhook shape below is **verified against the API source**, not against a live delivery: configuring a webhook URL mutates the licence, so it was deliberately not exercised.

The webhook body is a **bare JSON array** of track models — there is no `data` wrapper and it is not a single object, so parse it as a list. One element is emitted per completed generation, meaning a track rendered in two formats arrives as two elements sharing the same track `id`. Each element has `id`, `session_id`, `playlist_index`, `prompt`, `duration`, `intensity`, `mode`, `bpm`, `key` and a `generations` array holding just the one generation this delivery is about (`session_id`, `format`, `bitrate`, `status`, `generated_at`, `expired_at`, `created_at`, `url`).

Generation `status` is `processing`, `done`, or `failed`. Act on the payload when the status is `done` — `url` is `null` otherwise.

## Authentication

| Headers | Use case |
|---------|----------|
| `company-id` + `license-token` | All service endpoints |

## Error Handling

Error bodies are not wrapped in `data`. `401` and `403` carry `message` + `code`. Validation failures return `422` with `message` + an `errors` object keyed by field, and **no** `code`. A `404` from a UUID route carries only `message`. There is no `description` key.

- **401** - Invalid credentials (company-id/license-token), including a non-UUID `company-id`. A deleted customer's public credentials also end up here after the ~60 s auth cache — `401 Unauthenticated`, not `403`.
- **403** - The customer exists but belongs to another company (authorization runs after route binding, so this is *not* a 404), the customer is not active (`CustomerIsNotActive`), or the license customer cap is reached (`LicenseLimitUsersCount`)
- **404** - Customer or license not found. Two different bodies: lookups by path **UUID** return the raw Laravel binding error `{"message": "No query results for model [App\\Models\\Customer] <uuid>"}` with **no `code`** (it also leaks the internal model class), while `custom-id` lookups return `{"message": "Customer not found", "code": "CustomerNotFound"}`. Branch on the status code, not on `code`.
- **422** - Invalid parameters (body carries `errors`, not `code`)
- **500** - Two known API-side bugs, both from missing validation: an invalid `order`/`order_by` query value on `GET /service/customers` (avoid both parameters), and `PUT /service/customers/{id}` renaming onto a `custom_id` that is already taken (or held by a soft-deleted customer).

## Related Skills

After creating a customer and obtaining `customer-id` + `access-token`, use these skills:
- **mubert-generate** — generate, edit, and browse royalty-free music tracks
- **mubert-streaming** — stream real-time AI-generated music

## References

- [Installation Guide](references/installation.md)
- [API Reference](references/api_reference.md)
