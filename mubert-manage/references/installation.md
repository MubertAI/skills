# Installation

## Getting API Credentials

1. Sign up and choose a plan at [mubert.com/api](https://mubert.com/api)
2. Check your email — you'll receive `company-id` and `license-token` in the confirmation letter

## Environment Variables

```bash
export MUBERT_COMPANY_ID="your-company-id"
export MUBERT_LICENSE_TOKEN="your-license-token"
```

## Python

```bash
pip install requests
```

```python
import os
import requests

HEADERS = {
    "company-id": os.environ["MUBERT_COMPANY_ID"],
    "license-token": os.environ["MUBERT_LICENSE_TOKEN"],
    "Content-Type": "application/json",
}
```

## TypeScript / Node.js

No additional packages needed — uses the built-in `fetch` API (Node.js 18+).

```typescript
const BASE = "https://music-api.mubert.com/api/v3";

const HEADERS = {
  "company-id": process.env.MUBERT_COMPANY_ID!,
  "license-token": process.env.MUBERT_LICENSE_TOKEN!,
  "Content-Type": "application/json",
};
```

## Swagger Documentation

Full interactive API docs: `https://music-api.mubert.com/api/v3/swagger`
