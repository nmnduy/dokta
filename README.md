Another chatbot

Setup
```
pip3 install -r requirements.txt
```

Usage 

```
export OPENAI_API_KEY=<your openai API key>
```

then start the chat with

```
CHATGPT_CLI_MODEL=gpt-4 python chat.py
```

or

```
CHATGPT_CLI_MODEL=gpt-3.5-turbo python chat.py
```

## Models


There are 2 models listed in `config.json`. Update that config file to add more models.


## DB Migration

Used this tool: `https://github.com/pressly/goose`

Usage:

```bash
goose -dir migration/ sqlite3 ./convo_db.sqlite.db status
goose -dir migration/ sqlite3 ./convo_db.sqlite.db up-by-one
goose -dir migration/ sqlite3 ./convo_db.sqlite.db up
goose -dir migration/ sqlite3 ./convo_db.sqlite.db down
```
