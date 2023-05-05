-- +goose Up
ALTER TABLE conversation_entries ADD COLUMN session_id INTEGER DEFAULT NULL;
CREATE INDEX idx_conversation_entries_session_id ON conversation_entries (session_id);

-- +goose Down
DROP INDEX IF EXISTS idx_conversation_entries_session_id;
ALTER TABLE conversation_entries DROP COLUMN IF EXISTS session_id;
