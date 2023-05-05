-- +goose Up
-- +goose StatementBegin
SELECT 'up SQL query';
CREATE TABLE session (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) DEFAULT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL
);
-- +goose StatementEnd

-- +goose Down
-- +goose StatementBegin
SELECT 'down SQL query';
DROP TABLE session;
-- +goose StatementEnd
