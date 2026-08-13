---
name: mubert-setup
description: Set up Mubert Music API credentials. Use when the user needs to configure API keys, has just signed up at mubert.com/api, wants to save credentials to .env, or when any other mubert skill reports missing credentials. Walks the user through obtaining, validating, and storing company-id, license-token, customer-id, and access-token.
compatibility: Requires internet access to validate credentials against Mubert API.
metadata:
  author: mubert
  version: "3.0"
---

# Mubert API Key Setup

This skill walks users through obtaining, validating, and storing Mubert Music API credentials.

## Step 1: Check Existing Credentials

Before requesting new keys, check if credentials already exist:

1. Check environment variables: `MUBERT_COMPANY_ID`, `MUBERT_LICENSE_TOKEN`, `MUBERT_CUSTOMER_ID`, `MUBERT_ACCESS_TOKEN`
2. Check for a `.env` file in the project root
3. If found, validate them (see Step 4)
4. If valid, inform the user: "Your Mubert API is already configured and working!"

```python
import os
has_service = os.environ.get("MUBERT_COMPANY_ID") and os.environ.get("MUBERT_LICENSE_TOKEN")
has_public = os.environ.get("MUBERT_CUSTOMER_ID") and os.environ.get("MUBERT_ACCESS_TOKEN")
```

```typescript
const hasService = process.env.MUBERT_COMPANY_ID && process.env.MUBERT_LICENSE_TOKEN;
const hasPublic = process.env.MUBERT_CUSTOMER_ID && process.env.MUBERT_ACCESS_TOKEN;
```

## Step 2: Get API Key

If no credentials are found, guide the user:

> **To get your Mubert API credentials:**
>
> 1. Go to [mubert.com/api](https://mubert.com/api)
> 2. Sign up or log in
> 3. Choose a plan and complete payment
> 4. Check your email — you'll receive `company-id` and `license-token` in the confirmation letter
>
> Once you have them, paste them here and I'll set everything up.

Wait for the user to provide their `company-id` and `license-token`. Sanity-check the shapes before calling the API: `company-id` (and later `customer-id`) must be a UUID — the server rejects a non-UUID with a plain 401 before it ever looks the key up — while `license-token` and `access-token` are opaque strings (the access token is 64 characters).

## Step 3: Ask About Usage Pattern

The email pair is service-level only. `MUBERT_CUSTOMER_ID` and `MUBERT_ACCESS_TOKEN` are never taken from the email — they only exist once a customer is created via `POST /service/customers` (Step 5). They can be re-read later with `GET /service/customers/custom-id/{custom_id}`, which returns the same `access.token`. Never write `company-id` / `license-token` into the customer variables: public endpoints reject them with HTTP 401 `{"message":"Unauthenticated","code":"Unauthenticated"}`.

Once the user provides service credentials, ask:

> **How are you planning to use Mubert?**
>
> 1. **Single user / personal project** — I'll create one customer and save all credentials to `.env`. You'll be ready to generate tracks and stream music immediately.
>
> 2. **Multi-user app** — I'll create a customer provisioning script that your app can use to create a separate Mubert customer per user, each with their own credentials and usage limits.

## Step 4: Validate Credentials

### Validate service credentials (company-id + license-token)

```bash
curl -s -o /dev/null -w "%{http_code}" \
  -X GET "https://music-api.mubert.com/api/v3/service/licenses" \
  -H "company-id: $MUBERT_COMPANY_ID" \
  -H "license-token: $MUBERT_LICENSE_TOKEN"
```

```python
import os
import requests

company_id = os.environ["MUBERT_COMPANY_ID"]
license_token = os.environ["MUBERT_LICENSE_TOKEN"]

resp = requests.get("https://music-api.mubert.com/api/v3/service/licenses", headers={
    "company-id": company_id,
    "license-token": license_token,
})
if resp.status_code == 200:
    print("Service credentials are valid!")
    print(f"Licenses: {len(resp.json()['data'])} found")
else:
    print(f"Invalid credentials (HTTP {resp.status_code}). Please check and try again.")
```

```typescript
const companyId = process.env.MUBERT_COMPANY_ID!;
const licenseToken = process.env.MUBERT_LICENSE_TOKEN!;

const resp = await fetch("https://music-api.mubert.com/api/v3/service/licenses", {
  headers: {
    "company-id": companyId,
    "license-token": licenseToken,
  },
});
if (resp.ok) {
  const { data: licenses } = await resp.json();
  console.log(`Service credentials valid! ${licenses.length} license(s) found.`);
} else {
  console.error(`Invalid credentials (HTTP ${resp.status}). Please check and try again.`);
}
```

Interpreting the failure: **401** `{"code": "Unauthenticated"}` means the pair itself is not recognised — a wrong `company-id`, a wrong `license-token`, or a `company-id` that is not a UUID all produce this identical body, so ask the user to re-paste both values. **403** means the credentials were recognised but something else is wrong — read the `code` field: `LicenseExpired`, `LicenseIsNotActive`, `CompanyIsNotActive` (service side) or `AccessTokenExpired`, `CustomerIsNotActive` (customer side). Those need a renewed subscription or a re-provisioned customer, not a re-typed key.

If validation fails with 401, tell the user:
> Credentials are invalid. Please double-check them at [mubert.com/api](https://mubert.com/api). If the problem persists, contact business@mubert.com (the address the API docs list for API-key issues); support@mubert.com is CC'd on every credentials email and also works.

### Validate customer credentials (customer-id + access-token)

Every successful body from the three endpoints this skill calls is wrapped in a top-level `data` key: `GET /service/licenses` returns `data` plus a `meta` block (`offset`, `limit`, `total`) because it is paginated, while `GET /public/playlists` and `POST /service/customers` return `data` only, with no `meta`.

Error responses are not wrapped in `data`. `401` and `403` carry `message` + `code`. Validation failures return `422` with `message` + an `errors` object keyed by field, and **no** `code`. A `404` from a UUID route carries only `message`. A credential failure is always `401 {"message": "Unauthenticated", "code": "Unauthenticated"}` — for missing headers, a malformed (non-UUID) id, a wrong token, or a deleted customer alike.

`/public/music-library/*` responses are cached by the CDN with `Cache-Control: public`; a repeat request may be served from cache. Never validate credentials against them — use `GET /public/playlists`.

```python
customer_id = os.environ["MUBERT_CUSTOMER_ID"]
access_token = os.environ["MUBERT_ACCESS_TOKEN"]

resp = requests.get("https://music-api.mubert.com/api/v3/public/playlists", headers={
    "customer-id": customer_id,
    "access-token": access_token,
})
if resp.status_code == 200:
    print("Customer credentials are valid!")
else:
    print(f"Invalid customer credentials (HTTP {resp.status_code}).")
    # A 403 whose body is not JSON (e.g. "error code: 1010") is the CDN/WAF blocking the
    # User-Agent, not a credential problem. Use requests/curl, never urllib.
```

```typescript
const customerId = process.env.MUBERT_CUSTOMER_ID!;
const accessToken = process.env.MUBERT_ACCESS_TOKEN!;

const resp = await fetch("https://music-api.mubert.com/api/v3/public/playlists", {
  headers: {
    "customer-id": customerId,
    "access-token": accessToken,
  },
});
if (resp.ok) {
  console.log("Customer credentials valid!");
} else {
  console.error(`Invalid customer credentials (HTTP ${resp.status}).`);
}
```

## Step 5: Create Customer (if single-user)

If the user chose single-user mode, create a customer automatically. Pick a `custom_id` that identifies *this project* (e.g. `myapp-default-user`) rather than the bare `default-user` below: `custom_id` is unique per company, and `POST /service/customers` is find-or-create, so two projects on the same company that both post `default-user` silently share one customer, one access token and one usage quota.

```python
resp = requests.post("https://music-api.mubert.com/api/v3/service/customers", headers={
    "company-id": company_id,
    "license-token": license_token,
    "Content-Type": "application/json",
}, json={"custom_id": "default-user"})

# Check the status BEFORE reading ["data"]: error bodies are never `data`-wrapped.
# 422 -> {"message": ..., "errors": {"custom_id": [...]}} (no "code" key)
# 401/403 -> {"message": ..., "code": ...}
if resp.status_code != 200:
    raise RuntimeError(f"Customer creation failed (HTTP {resp.status_code}): {resp.text}")

customer = resp.json()["data"]
customer_id = customer["id"]                  # -> customer-id header
access_token = customer["access"]["token"]    # -> access-token header
```

```typescript
const resp = await fetch("https://music-api.mubert.com/api/v3/service/customers", {
  method: "POST",
  headers: {
    "company-id": companyId,
    "license-token": licenseToken,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({ custom_id: "default-user" }),
});
// Check the status BEFORE destructuring `data`: error bodies are never `data`-wrapped.
// 422 -> { message, errors: { custom_id: [...] } } (no `code`); 401/403 -> { message, code }
if (!resp.ok) {
  throw new Error(`Customer creation failed (HTTP ${resp.status}): ${await resp.text()}`);
}
const { data: customer } = await resp.json();
const customerId = customer.id;                 // -> customer-id header
const accessToken = customer.access.token;      // -> access-token header
```

## Step 6: Save to .env

Save all credentials to `.env` file in the project root. Replace existing values if present.

```
# Mubert Music API v3 credentials
# Obtained from https://mubert.com/api

# Service-level (for managing licenses and customers)
MUBERT_COMPANY_ID=<company-id>
MUBERT_LICENSE_TOKEN=<license-token>

# Customer-level (for generating tracks, streaming, and library access)
# NOTE: the access token expires 1 month after it is issued. It is auto-extended
# by another month whenever it is used within 7 days of expiry, so an actively
# used token never dies — but if it sits unused for >30 days the API answers
# HTTP 403 {"code": "AccessTokenExpired"}. Recover by re-running Step 5 with the
# same custom_id; that re-issues a token and returns the same customer id.
MUBERT_CUSTOMER_ID=<customer-id>
MUBERT_ACCESS_TOKEN=<access-token>
```

After saving, tell the user:

> Your Mubert API is configured! Here's what you can do now:
>
> - **Generate music** — "generate a 30 second chill lo-fi track"
> - **Stream music** — "get a streaming link for my app"
> - **Browse library** — "find electronic tracks with 120 BPM"
>
> All generated music is **royalty-free** and licensed for commercial use.

## Step 7: Multi-User Setup (if chosen)

If the user chose multi-user mode, generate a customer provisioning module instead of creating a single customer. The module should:

1. Accept a user identifier (e.g. your app's user ID)
2. Call `POST /service/customers` with that ID as `custom_id`. `custom_id` must match `^[a-zA-Z0-9._@-]+$` (Latin letters, digits and `.` `_` `@` `-` only) and be 1–255 characters. Anything else — spaces, `+`, `:`, `/`, non-Latin characters — returns HTTP 422 `{"message": "...", "errors": {"custom_id": [...]}}` (no `code` key). Slugify or hash your app's user id before sending it.
3. Return the `customer-id` and `access-token` for that user
4. No duplicate handling is needed. `POST /service/customers` is an **idempotent find-or-create**: reposting an existing `custom_id` returns the same customer, the same access-token record and the same token; a soft-deleted customer is restored with its original id. Use `GET /service/customers/custom-id/{custom_id}` only when you want to look credentials up without a write (404 `{"message": "Customer not found", "code": "CustomerNotFound"}` if the user was never provisioned).

5. Prefix every `custom_id` with a namespace naming the app **and** environment (`MUBERT_NAMESPACE`, e.g. `myapp-prod`). Because `custom_id` is unique per company and creation is find-or-create, a staging deployment that derives the same `custom_id` as production silently shares one customer, one access token and one usage counter.

Save `MUBERT_COMPANY_ID`, `MUBERT_LICENSE_TOKEN` and `MUBERT_NAMESPACE` to `.env` (but NOT customer credentials — those are per-user). If a single-user `MUBERT_CUSTOMER_ID` / `MUBERT_ACCESS_TOKEN` pair is already in `.env` from an earlier setup, remove it or clearly mark it unused: anything that reads it serves every user from one customer.

### Before scaling past a few hundred users

Check the licence's customer cap first — `GET /service/licenses`, then `data[0].license_limits.customers_count_limit` (`-1` = unlimited) against `customers_count`. `403 {"code": "LicenseLimitUsersCount"}` on create means the cap is reached.

`customers_count` is **monotonic**: deleting a customer does not decrement it (verified — create took 131→132, delete left it at 132, while the `GET /service/customers` total went 78→79→78). On a capped licence, provisioning churn permanently consumes cap, so do not treat delete as a way to reclaim headroom.

**Per-user limits cannot be enforced through Mubert.** Every fresh customer gets `-1` (unlimited) for all 25 `customer_limits`, and there is no API to change them — the licence's `customer_*_limit` fields are not copied down. One user can therefore spend the whole licence unless your app caps them itself.

For that cap, meter usage in your own database. Do not enforce against `access.customer_limits`' daily/monthly counters: they reset lazily and drift (an observed customer carried a `monthly_reset_at` a full month in the past). The `total_*` counters are monotonic and reliable — use those for reconciliation only, and note each read costs a service API call, so cache it rather than calling per request.

After generating the module, tell the user:

> Your Mubert provisioning service is ready! Each user of your app will get their own credentials with separate usage limits.
>
> Service credentials are saved to `.env`. Customer credentials are created dynamically per user.

## Security

- **Never commit `.env` to git.** Make sure `.gitignore` includes `.env`.
- **Keep credentials safe.** Don't share them publicly or hardcode in client-side code.
- **Service credentials are sensitive.** They can list, create, update and delete every customer on the license (and read/update the license itself). Only use them server-side.
- If `.gitignore` doesn't include `.env`, offer to add it.
