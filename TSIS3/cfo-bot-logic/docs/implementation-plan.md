# Implementation Plan

1. Read user input values:
   - instances
   - storage_gb
   - visitors
   - db_storage_gb

2. Normalize missing values to zero.

3. Validate that all input values are numeric.

4. Validate that all input values are non-negative.

5. Convert visitors into outbound traffic:
   1 visitor = 2 MB

6. Convert MB into GB:
   egress_gb = (visitors × 2) / 1024

7. Calculate compute cost using the predefined monthly billing cycle.

8. Calculate storage cost using price per GB.

9. Apply free egress tier of 5 GB before charging network cost.

10. Calculate database instance and database storage cost.

11. Sum all components into total monthly cost.

12. Round intermediate values to 4 decimal places.

13. Round final output values to 2 decimal places.

14. Return a deterministic JSON result.

15. Show warnings for unusually large inputs.