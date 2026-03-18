# Test Specification

## Test 1 — Compute
Input:
{
  "instances": 2,
  "storage_gb": 0,
  "visitors": 0,
  "db_storage_gb": 0
}

Expected:
- compute_cost = 69.35

Reason:
2 × (0.0475 × 730) = 69.35

---

## Test 2 — Free Egress
Input:
{
  "instances": 0,
  "storage_gb": 0,
  "visitors": 1536,
  "db_storage_gb": 0
}

Expected:
- network_cost = 0.00

Reason:
1536 visitors × 2 MB = 3072 MB = 3 GB
First 5 GB are free

---

## Test 3 — Paid Egress
Input:
{
  "instances": 0,
  "storage_gb": 0,
  "visitors": 5120,
  "db_storage_gb": 0
}

Expected:
- network_cost = 0.60

Reason:
5120 visitors × 2 MB = 10240 MB = 10 GB
(10 - 5) × 0.12 = 0.60

---

## Test 4 — Negative Input
Input:
{
  "instances": -1,
  "storage_gb": 0,
  "visitors": 0,
  "db_storage_gb": 0
}

Expected:
- Error: Invalid input: value must be ≥ 0 for instances

---

## Test 5 — Non-Numeric
Input:
{
  "instances": "abc",
  "storage_gb": 0,
  "visitors": 0,
  "db_storage_gb": 0
}

Expected:
- Error: Invalid input: numeric value required for instances

---

## Test 6 — Missing Fields
Input:
{
  "instances": 2
}

Expected:
- storage_gb defaults to 0
- visitors defaults to 0
- db_storage_gb defaults to 0