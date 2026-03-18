# Interface Contract (Logic ↔ Frontend)

## Input to Calculation Logic

The frontend must send the following object:

```json
{
  "instances": number,
  "storage_gb": number,
  "visitors": number,
  "db_storage_gb": number
}


## Example Request

```json
{
  "instances": 2,
  "storage_gb": 100,
  "visitors": 5000,
  "db_storage_gb": 50
}

## Example Response

```json
{
  "compute_cost": 69.35,
  "storage_cost": 10.00,
  "network_cost": 0.60,
  "database_cost": 4.60,
  "total_cost": 84.55
}




# CFO Bot Logic

## What this module does
Calculates cloud costs based on user input.

## Input fields
instances, storage_gb, visitors, db_storage_gb

## Where to look
- logic/ → calculation code
- docs/interface-contract.md → API contract
- docs/test-spec.md → validation tests