TSIS 3. CFO Bot (Cloud Economics) - Chat bot app.
Team members:
Muktar Riana 23B031379
Tolkynbekova Sabina 23B031157
Yerkin Samal 23B031850
Tajimagambetova Symbat 23B031448


CFO Bot System Specification (SSOT)
Version: 1.0
Project Phase: Phase 1 (Requirements Engineering)
Role: Analyst
Purpose: Define all requirements, logic, and constraints for the CFO Bot cloud cost calculator.

1. System Overview & Scope
The CFO Bot is a web-based calculator agent designed to estimate monthly cloud expenditures for a standard 3-tier application architecture.
1.2 In-Scope Components
The system must support cost calculation for:
Compute: Virtual Machine instances (on-demand)


Storage: Persistent block storage (GB/month)


Networking: External data egress (outbound bandwidth)


Database: Managed relational database (instance + storage)
1.3 Out-of-Scope
The system must not include:
Internal networking (ingress/internal traffic)


SaaS pricing (e.g., productivity tools, AI APIs)


Reserved Instances or Spot pricing models


Real-time pricing APIs



2. Mathematical Cost Models (SSOT Core Logic)
2.1 Pricing Constants 
The following constants must be used:
Compute hourly rate (r) = 0.0475 USD/hour
Storage price (Ps) = 0.10 USD/GB/month
Egress price (Pe) = 0.12 USD/GB
Database instance rate (Idb) = 0.025 USD/hour
Database storage price (Pdb) = 0.08 USD/GB/month
Billing cycle = 730 hours/month
Free egress tier = 5 GB

2.2 Compute Cost
Costcompute=n×(r×730)
Where:
n = number of instances
r = hourly rate
2.3 Storage Cost
Coststorage=SPs
Where:
S = storage in GB
Ps = price per GB
2.4 Networking (Egress) Cost

Costnetwork= max(0, (E-5)) Pe
Where:
E = total outbound traffic (GB)
First 5GB are free
2.5 Database Cost
Costdb = (Idb 730) + (SdbPdb)
Where:
Idb = hourly DB instance rate
Sdb= database storage


2.6 Total Cost
Total = Costcompute+Coststorage+Costnetwork+ Costdb

3. Input Specification & Derived Variables
3.1 User Inputs
Parameter
Type
Constraint
instances (n)
number
≥ 0
storage_gb (S)
number
≥ 0
visitors
number
≥ 0
db_storage_gb (Sdb)
number
≥ 0


3.2 Derived Variable
The system must convert visitors into bandwidth:
Assumption: 1 visitor = 2 MB of data transfer
E(GB)= visitors  2 /1024

4. User Flow & Interaction Logic
4.1 Conversation Flow
Phase A — Onboarding
Bot asks for project scale: Small / Medium / Enterprise
System sets default values


Phase B — Data Collection
User provides:
Number of instances
Storage (GB)
Monthly visitors
Database storage


Phase C — Verification
Bot displays summary: “You selected 2 instances and 500GB storage. Confirm?”
Phase D — Result
System returns:
Full cost breakdown
Total monthly cost



5. Validation & Error Handling
5.1 Validation Rules
All inputs must be numeric
Negative values must trigger error
Missing values must default to 0 
5.2 Error Handling
Case
Response
Negative input
"Invalid input: value must be ≥ 0"
Non-numeric
"Invalid input: numeric value required"
Missing field
Default to 0
Extremely large (>10,000,000)
Show warning


5.3 Rounding Rules
Intermediate values: 4 decimal places
Final output: 2 decimal places



6. System Constraints
The system must:
Be fully deterministic
Use only predefined constants
Follow all formulas exactly


The system must not:
Use randomness
Call external APIs
Modify pricing logic dynamically
This document overrides any implementation inconsistencies.

7. Output Contract
The system must return:
{
 "compute_cost": number,
 "storage_cost": number,
 "network_cost": number,
 "database_cost": number,
 "total_cost": number
}
All values must be in USD/month.

8. UI/UX Requirements
The application must:
Be a responsive web app
Support mobile and desktop


The UI must include:
Input fields or chatbot interface
“Calculate” action
Cost breakdown display (table or cards)


The UI must show:
Errors
Warnings
Updated results dynamically
8.1 State Management
The system must maintain session state.
Users must be able to update a single parameter without restarting the flow.
Example: "Change storage to 1TB" → recalculates instantly

9. Verification Constraints (Testable Conditions)
9.1 Deterministic Test Cases
Case 1 — Compute
Input:
 n = 2
 Expected:
 2 × (0.0475 × 730) = 69.35 USD
Case 2 — Free Tier
Input:
 E = 3 GB
 Expected:
 0 USD
Case 3 — Paid Egress
Input:
 E = 10 GB
 Expected:
 (10 - 5) × 0.12 = 0.60 USD
Case 4 — Zero Input
All inputs = 0
 Expected:
 Total = 0 USD


