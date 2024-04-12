Another chatbot that calls OpenAI models, with some

## features

- Chat messages are stored locally
- Chats have sessions, which are group of messages
- Multi-line input with `"""` or `'''`
- `\file` input mode to enter long input
- Support local LLM via [ollama](https://github.com/jmorganca/ollama)

## Install
```
bash build_release.sh
chmod +x ./dist/chat
mv ./dist/chat /usr/local/bin
```

## Usage

```
export OPENAI_API_KEY=<your openai API key>
export ANTHROPIC_API_KEY=<you Anthropic API key if using an Anthropic model>
```

Run the chatbot

```
chat
```

switch model

```
\model <model_name>

e.g.
\model gpt-3.5-turbo
\model gpt-4
\model opus
```

check `config.json` for available models

Ask a single question, get an answer then terminate

```
CHATGPT_CLI_MODEL=gpt-3.5-turbo chat -q '<question>'
```

### For long text input

#### '\file' input mode 

Instead of typing long input into a console, the `\file` command can be used, which open a file in the `vim` text editor. After saving the file, its content will be submitted as a message. You can override the text editor by setting environment variable `CHATGPT_CLI_TEXT_EDITOR`

If you have to paste long text into the input, use this option.

#### Multiline input

To start multi-line input, begin the text with `'''` or `"""`, then terminate input with the equivalent block opener.

#### `-f` flag

The message can be written to a file, like `question`, for example. Then run this to submit the content of the file as the message.

```
CHATGPT_CLI_MODEL=gpt-3.5-turbo chat -f question
```

## Models


There are 2 models listed in `config.json`. Update that config file to add more models.

To use a local LLM via `ollama`, add a new entry to `config.json` and add key `"backend": "ollama"`. For example:

```
{
  "models": [
    ...
    {
      "name": "openhermes2.5-mistral:7b",
      "max_tokens": 8000,
      "backend": "ollama"
    }
  ]
}
```


To switch models, in the chat prompt, type `\model <model_name>`. You can use `Tab` to autocomplete the input.


## Sessions

Messages in the same session are sent to OpenAI API together.

`\new_session` to switch to a new session

`\new_session <name>` to switch to a new session with the given name. If you have an old session that you want to switch to, you can also use this command to do that. Use `Tab` to auto complete the session name.

`\rename_session <new name>` to rename the current session to some name. By default, every conversation has a session, with a random hash name. You can `\rename_session` to mark it for use later.

`\sessions` to list all your named sessions.

`\messages` to see messages in the current session.

`\last_session [previous index]` to switch to previous sessions. If no parameter is provided, then the parameter is `1` by default. `\last_session 1` will switch to the previous session. `\last_session 2` will switch to the session before the previous session. So on and so forth.

## Development

### DB Migration

Used this tool: `https://github.com/pressly/goose`

Usage:

```bash
goose -dir migration/ sqlite3 ./convo_db.sqlite.db status
goose -dir migration/ sqlite3 ./convo_db.sqlite.db up-by-one
goose -dir migration/ sqlite3 ./convo_db.sqlite.db up
goose -dir migration/ sqlite3 ./convo_db.sqlite.db down
```

### Known Issues

### pasting long text into the terminal does not work properly

Workaround is using the `\file` command in the console mode or the `-f` flag in the CLI mode.
