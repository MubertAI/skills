# Installation

## Getting API Credentials

1. Get your API key at [mubert.com/api](https://mubert.com/api)
2. You will receive a `company-id` and `license-token` (service-level credentials)
3. Use the service API to create customers and obtain `customer-id` + `access-token` pairs

## Environment Variables

```bash
export MUBERT_CUSTOMER_ID="your-customer-id"
export MUBERT_ACCESS_TOKEN="your-access-token"
```

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
