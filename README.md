# Overview

Genderize API.

## Endpoint

### GET `/api/classify?name={name}`

Example request:

```bash
curl "http://127.0.0.1:8000/api/classify?name=john"
```

Success response (`200`):

```json
{
  "status": "success",
  "data": {
    "name": "john",
    "gender": "male",
    "probability": 0.99,
    "sample_size": 1234,
    "is_confident": true,
    "processed_at": "2026-04-01T12:00:00Z"
  }
}
```

## Rules Implemented

- Extracts `gender`, `probability`, and `count` from Genderize response.
- Renames `count` to `sample_size`.
- Computes `is_confident` as:
  - `true` only when `probability >= 0.7` and `sample_size >= 100`
  - `false` otherwise
- Generates `processed_at` dynamically on each request in UTC ISO 8601 format.
- Returns `Access-Control-Allow-Origin: *` via CORS middleware.

## Local Run

```bash
uv sync
# Windows PowerShell
.\.venv\Scripts\Activate.ps1
uvicorn main:app --port 8000
```

## Quick Checks

```bash
# success
curl "http://127.0.0.1:8000/api/classify?name=john"

# missing name -> 400
curl "http://127.0.0.1:8000/api/classify"

# empty name -> 400
curl "http://127.0.0.1:8000/api/classify?name="
```
