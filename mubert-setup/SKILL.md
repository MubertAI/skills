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

Wait for the user to provide their `company-id` and `license-token`.

## Step 3: Ask About Usage Pattern

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
import requests

resp = requests.get("https://music-api.mubert.com/api/v3/service/licenses", headers={
    "company-id": company_id,
    "license-token": license_token,
})
if resp.status_code == 200:
    print("Service credentials are valid!")
    print(f"Licenses: {len(resp.json())} found")
else:
    print(f"Invalid credentials (HTTP {resp.status_code}). Please check and try again.")
```

```typescript
const resp = await fetch("https://music-api.mubert.com/api/v3/service/licenses", {
  headers: {
    "company-id": companyId,
    "license-token": licenseToken,
  },
});
if (resp.ok) {
  const licenses = await resp.json();
  console.log(`Service credentials valid! ${licenses.length} license(s) found.`);
} else {
  console.error(`Invalid credentials (HTTP ${resp.status}). Please check and try again.`);
}
```

If validation fails, tell the user:
> Credentials are invalid. Please double-check them at [mubert.com/api](https://mubert.com/api). If the problem persists, contact support@mubert.com.

### Validate customer credentials (customer-id + access-token)

```python
resp = requests.get("https://music-api.mubert.com/api/v3/public/playlists", headers={
    "customer-id": customer_id,
    "access-token": access_token,
})
if resp.status_code == 200:
    print("Customer credentials are valid!")
else:
    print(f"Invalid customer credentials (HTTP {resp.status_code}).")
```

```typescript
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

If the user chose single-user mode, create a customer automatically:

```python
resp = requests.post("https://music-api.mubert.com/api/v3/service/customers", headers={
    "company-id": company_id,
    "license-token": license_token,
    "Content-Type": "application/json",
}, json={"custom_id": "default-user"})

customer = resp.json()
customer_id = customer["access"]["id"]
access_token = customer["access"]["token"]
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
const customer = await resp.json();
const customerId = customer.access.id;
const accessToken = customer.access.token;
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
2. Call `POST /service/customers` with that ID as `custom_id`
3. Return the `customer-id` and `access-token` for that user
4. Handle the case where a customer already exists (`GET /service/customers/custom-id/{id}`)

Save `MUBERT_COMPANY_ID` and `MUBERT_LICENSE_TOKEN` to `.env` (but NOT customer credentials — those are per-user).

After generating the module, tell the user:

> Your Mubert provisioning service is ready! Each user of your app will get their own credentials with separate usage limits.
>
> Service credentials are saved to `.env`. Customer credentials are created dynamically per user.

## Security

- **Never commit `.env` to git.** Make sure `.gitignore` includes `.env`.
- **Keep credentials safe.** Don't share them publicly or hardcode in client-side code.
- **Service credentials are sensitive.** They can create/delete customers. Only use them server-side.
- If `.gitignore` doesn't include `.env`, offer to add it.
