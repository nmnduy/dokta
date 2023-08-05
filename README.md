Another chatbot that calls OpenAI models, with some

## features

- Chat messages are stored locally
- Chats have sessions, which are group of messages

## Setup
```
pip3 install -e .
```

## Usage

```
export OPENAI_API_KEY=<your openai API key>
```

then start the chat with

```
CHATGPT_CLI_MODEL=gpt-4 chat
```

or

```
CHATGPT_CLI_MODEL=gpt-3.5-turbo chat
```

## Models


There are 2 models listed in `config.json`. Update that config file to add more models.


To switch models, in the chat prompt, type `\model <model_name>`. You can use `Tab` to autocomplete the input.


## Sessions

Messages in the same session are sent to OpenAI API together.

`\session` to switch to a new session

`\session <name>` to switch to a new session with the given name. If you have an old session that you want to switch to, you can also use this command to do that. Use `Tab` to auto complete the session name.

`\rename_session <new name>` to rename the current session to some name. By default, every conversation has a session, with a random hash name. You can `\rename_session` to mark it for use later.

`\sessions` to list all your named sessions.

`\messages` to see messages in the current session.

## DB Migration

Used this tool: `https://github.com/pressly/goose`

Usage:

```bash
goose -dir migration/ sqlite3 ./convo_db.sqlite.db status
goose -dir migration/ sqlite3 ./convo_db.sqlite.db up-by-one
goose -dir migration/ sqlite3 ./convo_db.sqlite.db up
goose -dir migration/ sqlite3 ./convo_db.sqlite.db down
```


## Terminating input

It's surprisingly complicated to Ctrl+Enter to terminate input.(Maybe it's not that complicated, please submit a PR).

Here are ways to terminate input:

- On a new line, hit `Ctrl+D`
- On a new line, `<` then `Tab`, which will produce `<endofinput>`, then `Enter`
