import { PRICING } from './pricing.constants';

export interface CFOBotInput {
  instances?: number;
  storage_gb?: number;
  visitors?: number;
  db_storage_gb?: number;
}

export interface CFOBotResult {
  compute_cost: number;
  storage_cost: number;
  network_cost: number;
  database_cost: number;
  total_cost: number;
  warnings?: string[];
}

function round4(value: number): number {
  return Number(value.toFixed(4));
}

function round2(value: number): number {
  return Number(value.toFixed(2));
}

function normalize(value: unknown, field: string): number {
  if (value === undefined || value === null || value === '') {
    return 0;
  }

  if (typeof value !== 'number' || Number.isNaN(value)) {
    throw new Error(`Invalid input: numeric value required for ${field}`);
  }

  if (value < 0) {
    throw new Error(`Invalid input: value must be ≥ 0 for ${field}`);
  }

  return value;
}

export function calculateCloudCost(input: CFOBotInput): CFOBotResult {
  const warnings: string[] = [];

  const instances = normalize(input.instances, 'instances');
  const storage_gb = normalize(input.storage_gb, 'storage_gb');
  const visitors = normalize(input.visitors, 'visitors');
  const db_storage_gb = normalize(input.db_storage_gb, 'db_storage_gb');

  for (const [key, value] of Object.entries({
    instances,
    storage_gb,
    visitors,
    db_storage_gb
  })) {
    if (value > PRICING.LARGE_INPUT_THRESHOLD) {
      warnings.push(`Warning: unusually large value detected for ${key}`);
    }
  }

  const egress_gb = round4(
    (visitors * PRICING.DATA_PER_VISITOR_MB) / 1024
  );

  const compute_cost = round4(
    instances * (PRICING.COMPUTE_HOURLY_RATE * PRICING.BILLING_CYCLE_HOURS)
  );

  const storage_cost = round4(
    storage_gb * PRICING.STORAGE_PRICE_PER_GB
  );

  const network_cost = round4(
    Math.max(0, egress_gb - PRICING.FREE_EGRESS_GB) * PRICING.EGRESS_PRICE_PER_GB
  );

  const database_cost = round4(
    (PRICING.DB_INSTANCE_RATE * PRICING.BILLING_CYCLE_HOURS) +
    (db_storage_gb * PRICING.DB_STORAGE_PRICE_PER_GB)
  );

  const total_cost = round2(
    compute_cost + storage_cost + network_cost + database_cost
  );

  return {
    compute_cost: round2(compute_cost),
    storage_cost: round2(storage_cost),
    network_cost: round2(network_cost),
    database_cost: round2(database_cost),
    total_cost,
    warnings: warnings.length ? warnings : undefined
  };
}