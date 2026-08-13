# API Reference — License & Customer Management

Base URL: `https://music-api.mubert.com/api/v3`

**Headers:** `company-id`, `license-token` (both required on every `/service/*` route), plus
`Content-Type: application/json` on the requests that send a body (`POST`/`PUT`).

## Response envelope

Successful JSON responses from the endpoints below are wrapped in a top-level `data` key — read
`resp.json()["data"]`, not the body itself. The models described below are the contents of `data`.
The two list endpoints in this file (`GET /service/licenses`, `GET /service/customers`) add a
sibling `meta` block with exactly `offset`, `limit` and `total` — no `page`, `per_page` or `links`.
Single-resource responses (create, show, update) carry `data` only, with no `meta`.

Two exceptions:

- `DELETE /service/customers/{id}` returns **204 with an empty body** — never call `.json()` on it.
- The customer webhook payload → **bare JSON array of track objects**, never `data`-wrapped.

**Always check the status before reading `data`.** On a `422` (or any error) the body has no `data`
key, so `resp.json()["data"]` raises `KeyError` instead of telling you what is wrong.

## Errors

Error responses are not wrapped in `data`. `401` and `403` carry `message` + `code`.
Validation failures return `422` with `message` + an `errors` object keyed by field, and
**no** `code`. A `404` from a UUID route carries only `message`.

| Condition | Status | Body |
|---|---|---|
| bad/missing/mismatched `company-id` + `license-token`, non-UUID `company-id` | **401** | `{"message": "Unauthenticated", "code": "Unauthenticated"}` |
| customer belongs to another company; customer not active (`CustomerIsNotActive`); customer cap reached (`LicenseLimitUsersCount`) | **403** | `{"message": ..., "code": ...}` |
| unknown id on a UUID route (`/service/customers/{id}`, `/service/licenses/{id}`) | **404** | `{"message": "No query results for model [App\\Models\\Customer] <uuid>"}` — **no `code`**, and it leaks the internal model class |
| unknown `custom_id` on `/service/customers/custom-id/{custom_id}` | **404** | `{"message": "Customer not found", "code": "CustomerNotFound"}` |
| invalid or missing `custom_id`, non-integer `limit`/`offset` | **422** | `{"message": ..., "errors": {"<field>": [...]}}` — **no `code`** |
| invalid `order`/`order_by` on the customer list (API bug, see below) | **500** | `{"message": "Server Error"}` |

There is no `description` key — it never appears in any response. Branch on the HTTP status, not on
`code`: the two `404` shapes differ, and client code that reads `body["code"]` raises `KeyError` on
the UUID route.

---

## Licenses

### `GET /service/licenses` - List all licenses

**Response:** `200 OK` — `data` is an array of license models, `meta` carries `offset`/`limit`/`total`.

License model fields: `id`, `company_id`, `type`, `status`, `webhook_url`, `webhook_enabled`,
`track_expiration_time`, `expired_at`, the allow-all flags with their allowed-value arrays
(`allow_all_features`/`features`, `allow_all_bitrates`/`bitrates`, `allow_all_intensities`/`intensities`,
`allow_all_formats`/`track_formats`, `allow_all_modes`/`track_modes`), the per-license defaults
(`default_bitrate`, `default_intensity`, `default_format`, `default_mode`), and `license_limits`.

The field names are `track_formats`, `track_modes` and `license_limits` — there is no `formats`,
`modes` or `limits` key, and usage statistics are not a separate field: the counters
(`total_tracks_count`, `monthly_streaming_duration`, `customers_count`, `daily_reset_at`, …) live
**inside** `license_limits` alongside the matching `*_limit` fields. `-1` means unlimited.

The `default_*` fields are why generation defaults are per-licence, not API constants: another
licence can hand out different ones.

---

### `GET /service/licenses/{license_id}` - Get license

**Response:** `200 OK` - Single license model under `data`, no `meta`. An unknown UUID returns the
route-binding `404` described above (`message` only, no `code`).

---

### `PUT /service/licenses/{license_id}` - Update license webhook

**Body:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `webhook_url` | string\|null | No | URL to receive webhook notifications, **max 255 characters**. Send `null` to clear it. |
| `webhook_enabled` | boolean | No | Enable/disable webhook |

**Response:** `200 OK` - Updated license model under `data` (the licence is re-read after the write,
so the response reflects it).

#### Webhook payload

> Everything in this subsection is **verified against the API source** (`SendWebhookFeature.php:172-174`
> and `TrackPublicResource`), not against a live delivery — configuring a webhook URL mutates the
> licence, which was out of scope. Treat the shape as source-confirmed, not field-observed.

The webhook body is a **bare JSON array** of track models. It is **not** `data`-wrapped and it is
**not** a single object, so parse it as a list — `payload["id"]` raises `TypeError` in Python and
yields `undefined` in JavaScript on every real delivery. `SendWebhookFeature` serialises the
collection with `->toArray()` rather than `->toResponse()`, which is what drops the envelope.

One element is emitted per completed generation, so a track rendered in two formats arrives as two
elements sharing the same track `id`, each carrying just the one generation the delivery is about.

```json
[
  {
    "id": "track-id",
    "session_id": "session-id",
    "playlist_index": null,
    "prompt": "lo-fi study beat",
    "duration": 30,
    "intensity": "high",
    "mode": "track",
    "bpm": 120,
    "key": "C",
    "generations": [
      {
        "session_id": "gen-session-id",
        "format": "mp3",
        "bitrate": 128,
        "status": "done",
        "generated_at": "2024-01-01T00:00:00Z",
        "expired_at": "2024-02-01T00:00:00Z",
        "created_at": "2024-01-01T00:00:00Z",
        "url": "https://..."
      }
    ]
  }
]
```

Generation `status` is `processing`, `done` or `failed`; `url` is `null` unless the status is `done`.
Delivery is retried with an `(attempts + 1)²`-second backoff.

---

## Customers

### `POST /service/customers` - Create customer

**Body:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `custom_id` | string | Yes | Your identifier. `^[a-zA-Z0-9._@-]+$`, length 1–255. Spaces, `+`, unicode → 422. |

Note what the charset excludes: emails containing `+`, any identifier with a space, and every
non-ASCII character. A 256-character value returns `422`, a 255-character one is accepted.

`POST /service/customers` is an **idempotent find-or-create**: reposting an existing
`custom_id` returns the same customer, the same access-token record and the same token;
a soft-deleted customer is restored with its original id.

To recover a token you already issued, prefer the read-only path:
`GET /service/customers/custom-id/{custom_id}` returns the identical `access.token` without writing
anything. Reposting works too, but it resurrects a soft-deleted customer as a side effect.

**Response:** `200 OK` (never `201`)

```json
{
  "data": {
    "id": "customer-uuid",
    "company_id": "company-uuid",
    "custom_id": "my-app-user-1",
    "status": "active",
    "access": {
      "id": "access-token-record-uuid",
      "customer_id": "customer-uuid",
      "license_id": "license-uuid",
      "token": "access-token-for-public-api",
      "expired_at": "2025-01-01T00:00:00Z",
      "customer_limits": {
        "id": "customer-limit-uuid",
        "customer_id": "customer-uuid",
        "license_id": "license-uuid",
        "max_concurrent_track_generations": -1,
        "total_tracks_count": 0,
        "total_tracks_count_limit": -1,
        "total_tracks_duration": 0,
        "total_tracks_duration_limit": -1,
        "monthly_tracks_count": 0,
        "monthly_tracks_count_limit": -1,
        "monthly_tracks_duration": 0,
        "monthly_tracks_duration_limit": -1,
        "daily_tracks_count": 0,
        "daily_tracks_count_limit": -1,
        "daily_tracks_duration": 0,
        "daily_tracks_duration_limit": -1,
        "total_streaming_duration": 0,
        "total_streaming_duration_limit": -1,
        "monthly_streaming_duration": 0,
        "monthly_streaming_duration_limit": -1,
        "daily_streaming_duration": 0,
        "daily_streaming_duration_limit": -1,
        "daily_reset_at": null,
        "monthly_reset_at": null
      }
    }
  }
}
```

`customer_limits` is nested **inside `access`**, not beside it: `data["customer_limits"]` raises
`KeyError` on every endpoint that returns a customer. It holds 25 keys — the counters and their
`*_limit` twins plus the two reset timestamps — and `-1` means unlimited.

A fresh customer's limits are **all `-1`**, including
`daily_streaming_duration_limit` and `monthly_streaming_duration_limit`. Those are the per-customer
column defaults, not values copied from the licence: the copy is broken upstream
(`FindOrCreateCustomerLicenseLimitFeature` writes `customer_*`-prefixed keys the entity does not
declare), so do not expect a licence's `customer_daily_streaming_duration_limit` to appear here.

For public endpoints (track generation, streaming, library) use `data.id` — the customer's own ID —
as the `customer-id` header, and `data.access.token` as the `access-token` header.

`data.access.id` identifies the access-token record, not the customer. Sending it as `customer-id`
returns `401` even for a valid customer and token: the lookup matches the header against the token's
`customer_id`, which equals the customer's `id`.

Access tokens expire **one month** after issue, auto-extended only if used within 7 days of
expiry; otherwise `403 AccessTokenExpired`. There is no refresh endpoint: while a token is still
valid, read it back with `GET /service/customers/custom-id/{custom_id}`; once it has expired,
re-`POST /service/customers` with the same `custom_id` to mint a fresh one.

---

### `GET /service/customers` - List customers

**Query Parameters:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `limit` | integer | No | Default `100`. `0` or negative is silently treated as `100`, not as an empty page. No server-side maximum — `limit=100000` is echoed back verbatim. |
| `offset` | integer | No | Default `0`. A negative offset is accepted and echoed back rather than rejected. |
| `order_by` | string | No | **Unsupported — avoid.** Undocumented, unvalidated; default `custom_id`. An unknown column returns `500`. |
| `order` | string | No | **Unsupported — avoid.** Undocumented, unvalidated; default `asc`. Anything other than `asc`/`desc` returns `500`. |

Non-integer `limit`/`offset` return `422`.

**Response:** `200 OK` — Customer models in `data`, pagination in `meta` (`offset`, `limit`, `total`).

Each list item is the **full** customer model, including `access.token` in plaintext and the whole
25-field `customer_limits`. One call at the default `limit=100` therefore dumps every listed
customer's live access token — do not log the response, and page deliberately rather than
fetching everything.

---

### `GET /service/customers/{customer_id}` - Get customer by ID

**Response:** `200 OK` - Customer model under `data` (with `access` and `access.customer_limits`).
Unknown UUID → route-binding `404` with `message` only.

---

### `GET /service/customers/custom-id/{custom_id}` - Get customer by custom ID

**Response:** `200 OK` - Customer model under `data`.
Unknown `custom_id` → `404 {"message": "Customer not found", "code": "CustomerNotFound"}`.

---

### `PUT /service/customers/{customer_id}` - Rename customer

Undocumented on mubert.com/api/docs but live and working.

**Body:**

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `custom_id` | string | Yes | Same rules as create: `^[a-zA-Z0-9._@-]+$`, length 1–255. |

**Response:** `200 OK` — `{"data": {"id", "company_id", "custom_id", "status"}}`, exactly those four
keys. The relations are not eager-loaded on update, so the response carries **no `access`** and
**no `customer_limits`** — GET the customer if you need the token.

An invalid `custom_id` returns `422` as on create, but renaming onto a `custom_id` that is already
taken returns **`500 {"message": "Server Error"}`** — including when the holder is only
soft-deleted. Check availability yourself before renaming.

---

### `DELETE /service/customers/{customer_id}` - Delete customer

**Response:** `204 No Content`, zero-length body, no `Content-Type`. Do not parse it.

Customer deletion is asynchronous for the customer's own credentials: measured **60.6 s**
before the pair starts returning 401 (service-side lookups 404 immediately).

The delete is a soft delete — re-`POST /service/customers` with the same `custom_id` restores the
customer with its original id.

---

## Known API-side bugs

Report these to Mubert; do not design around them silently.

- **`order` / `order_by` on `GET /service/customers` return `500`.** Neither key appears in
  `CustomerIndexServiceRequest::rules()`, so user input reaches `OrderDirectionEnum::from()` and the
  `ORDER BY` clause unvalidated. Live: `?order=bogus` → `500 {"message": "Server Error"}`,
  `?order_by=bogus` → `500`. Avoid both parameters until they are validated.
- **`PUT /service/customers/{id}` returns `500` on a duplicate `custom_id`.** Uniqueness is not
  validated, so the database constraint surfaces as a server error — and a soft-deleted customer
  still holds its name. Live: rename onto a live or a soft-deleted `custom_id` → `500`.
- **Per-customer streaming limits are never copied from the licence** — every fresh customer gets
  `-1` for all three streaming limits regardless of what the licence says.
- **The UUID-route `404` leaks the internal model class** (`App\Models\Customer`) in `message`.
- **A customer belonging to another company yields `403`, not `404`** — route-model binding resolves
  globally and the company check runs afterwards.
