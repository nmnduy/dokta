-- +goose Up
ALTER TABLE conversation_entries ADD COLUMN model INTEGER DEFAULT NULL;
CREATE INDEX idx_conversation_entries_model ON conversation_entries (model);

-- +goose Down
DROP INDEX IF EXISTS idx_conversation_entries_model;
ALTER TABLE conversation_entries DROP COLUMN IF EXISTS model;
