# Installation

## Getting API Credentials

1. Sign up and choose a plan at [mubert.com/api](https://mubert.com/api)
2. Check your email — you'll receive `company-id` and `license-token` in the confirmation letter
3. Use the service API to create customers and obtain `customer-id` + `access-token` pairs

## Environment Variables

```bash
export MUBERT_CUSTOMER_ID="your-customer-id"
export MUBERT_ACCESS_TOKEN="your-access-token"
```

## Creating a Customer via Service API

```bash
curl -X POST "https://music-api.mubert.com/api/v3/service/customers" \
  -H "company-id: $MUBERT_COMPANY_ID" \
  -H "license-token: $MUBERT_LICENSE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"custom_id": "my-app-user-1"}'
```

The response contains `access.id` (customer-id) and `access.token` (access-token) for public endpoint usage.

## Python

```bash
pip install requests
```

```python
import os
import requests

HEADERS = {
    "customer-id": os.environ["MUBERT_CUSTOMER_ID"],
    "access-token": os.environ["MUBERT_ACCESS_TOKEN"],
    "Content-Type": "application/json",
}
```

## TypeScript / Node.js

No additional packages needed — uses the built-in `fetch` API (Node.js 18+).

```typescript
const BASE = "https://music-api.mubert.com/api/v3";

const HEADERS = {
  "customer-id": process.env.MUBERT_CUSTOMER_ID!,
  "access-token": process.env.MUBERT_ACCESS_TOKEN!,
  "Content-Type": "application/json",
};
```

## Swagger Documentation

Full interactive API docs: `https://music-api.mubert.com/api/v3/swagger`