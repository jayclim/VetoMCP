-- Drop the veto_users view that aliases the "user" table
DROP VIEW IF EXISTS veto_users;

-- Drop existing foreign key constraints (they reference text columns, need to be recreated for UUID)
ALTER TABLE "transaction" DROP CONSTRAINT IF EXISTS transaction_user_id_fkey;
ALTER TABLE budget_category DROP CONSTRAINT IF EXISTS budget_category_user_id_fkey;
ALTER TABLE budget_rule DROP CONSTRAINT IF EXISTS budget_rule_user_id_fkey;

-- Rename existing tables to veto_* naming convention
ALTER TABLE "user" RENAME TO veto_users;
ALTER TABLE "transaction" RENAME TO veto_transactions;
ALTER TABLE budget_category RENAME TO veto_budget_categories;
ALTER TABLE budget_rule RENAME TO veto_budget_rules;

-- Fix veto_users: convert id to UUID with auto-generation
ALTER TABLE veto_users
  ALTER COLUMN id SET DATA TYPE UUID USING id::uuid,
  ALTER COLUMN id SET DEFAULT gen_random_uuid();

-- Fix veto_transactions: convert id and user_id to UUID
ALTER TABLE veto_transactions
  ALTER COLUMN id SET DATA TYPE UUID USING id::uuid,
  ALTER COLUMN id SET DEFAULT gen_random_uuid(),
  ALTER COLUMN user_id SET DATA TYPE UUID USING user_id::uuid;

-- Fix veto_budget_categories: convert id and user_id to UUID
ALTER TABLE veto_budget_categories
  ALTER COLUMN id SET DATA TYPE UUID USING id::uuid,
  ALTER COLUMN id SET DEFAULT gen_random_uuid(),
  ALTER COLUMN user_id SET DATA TYPE UUID USING user_id::uuid;

-- Fix veto_budget_rules: convert id and user_id to UUID, config to JSONB
ALTER TABLE veto_budget_rules
  ALTER COLUMN id SET DATA TYPE UUID USING id::uuid,
  ALTER COLUMN id SET DEFAULT gen_random_uuid(),
  ALTER COLUMN user_id SET DATA TYPE UUID USING user_id::uuid,
  ALTER COLUMN config SET DATA TYPE JSONB USING config::jsonb;

-- Re-add foreign key constraints
ALTER TABLE veto_transactions
  ADD CONSTRAINT fk_transactions_user FOREIGN KEY (user_id) REFERENCES veto_users(id) ON DELETE CASCADE;

ALTER TABLE veto_budget_categories
  ADD CONSTRAINT fk_categories_user FOREIGN KEY (user_id) REFERENCES veto_users(id) ON DELETE CASCADE;

ALTER TABLE veto_budget_rules
  ADD CONSTRAINT fk_rules_user FOREIGN KEY (user_id) REFERENCES veto_users(id) ON DELETE CASCADE;

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_transactions_user_id ON veto_transactions(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_date ON veto_transactions(date DESC);
CREATE INDEX IF NOT EXISTS idx_budget_categories_user_id ON veto_budget_categories(user_id);
CREATE INDEX IF NOT EXISTS idx_budget_rules_user_id ON veto_budget_rules(user_id);
