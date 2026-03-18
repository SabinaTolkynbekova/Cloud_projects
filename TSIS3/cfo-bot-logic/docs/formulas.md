# CFO Bot Formulas

## Input Variables
- instances (n)
- storage_gb (S)
- visitors
- db_storage_gb (Sdb)

## Pricing Constants
- Compute hourly rate = 0.0475 USD/hour
- Storage price = 0.10 USD/GB/month
- Egress price = 0.12 USD/GB
- Database instance rate = 0.025 USD/hour
- Database storage price = 0.08 USD/GB/month
- Billing cycle = 730 hours/month
- Free egress tier = 5 GB

## Derived Variable
1 visitor = 2 MB

egress_gb = (visitors × 2) / 1024

## Compute Cost
compute_cost = instances × (0.0475 × 730)

## Storage Cost
storage_cost = storage_gb × 0.10

## Network Cost
network_cost = max(0, egress_gb - 5) × 0.12

## Database Cost
database_cost = (0.025 × 730) + (db_storage_gb × 0.08)

## Total Cost
total_cost = compute_cost + storage_cost + network_cost + database_cost