-- +goose Up
-- +goose StatementBegin
CREATE TABLE IF NOT EXISTS conversation_entries (
    id INTEGER PRIMARY KEY,
    role VARCHAR(50),
    content VARCHAR(255),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    session_id INTEGER,
    FOREIGN KEY(session_id) REFERENCES session (id)
);
-- +goose StatementEnd


-- +goose Down
-- +goose StatementBegin
DROP TABLE conversation_entries;
-- +goose StatementEnd
