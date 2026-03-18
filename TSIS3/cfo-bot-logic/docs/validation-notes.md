# Validation Notes

## Confirmed Rules
- All inputs must be numeric
- Negative values must trigger an error
- Missing values default to 0
- Intermediate values use 4 decimal places
- Final output uses 2 decimal places
- The system must be deterministic
- The system must use only predefined pricing constants

## Output Contract
{
  "compute_cost": number,
  "storage_cost": number,
  "network_cost": number,
  "database_cost": number,
  "total_cost": number
}

## Important SSOT Observation
There is a possible inconsistency between:
- database formula
- zero-input test case

If database cost is always charged as:
database_cost = (0.025 × 730) + (db_storage_gb × 0.08)

then zero input may still produce a non-zero database cost.
This should be clarified with the Analyst before final defense.