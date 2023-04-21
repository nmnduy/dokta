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
MAX_TOKENS=4096 CHATGPT_CLI_MODEL=gpt-4 python chat.py
```

or

```
MAX_TOKENS=2048 CHATGPT_CLI_MODEL=gpt-3.5-turbo python chat.py
```
