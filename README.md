Another chatbot

Setup
```
pip3 install -e .
```

Usage 

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


To switch models, in the chat prompt, type `\model` and then `Enter`. A list of models will show up, type he model name and `Enter` to switch. You can use `Tab` for auto-completing the model name.


## DB Migration

Used this tool: `https://github.com/pressly/goose`

Usage:

```bash
goose -dir migration/ sqlite3 ./convo_db.sqlite.db status
goose -dir migration/ sqlite3 ./convo_db.sqlite.db up-by-one
goose -dir migration/ sqlite3 ./convo_db.sqlite.db up
goose -dir migration/ sqlite3 ./convo_db.sqlite.db down
```
