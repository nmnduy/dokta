import json

CONFIG = {
  "models": [
    {
      "name": "gpt-4o",
      "max_tokens": 4096
    },
    {
      "name": "gpt-4",
      "max_tokens": 8000
    },
    {
      "name": "gpt-3.5-turbo",
      "max_tokens": 3800
    },
    {
      "name": "nous-hermes2-mixtral:8x7b",
      "max_tokens": 4096,
      "backend": "ollama"
    },
    {
      "name": "openhermes2.5-mistral:7b",
      "max_tokens": 8000,
      "backend": "ollama"
    },
    {
      "name": "orca2:latest",
      "max_tokens": 8000,
      "backend": "ollama"
    },
    {
      "name": "orca2:13b",
      "max_tokens": 4096,
      "backend": "ollama"
    },
    {
      "name": "sonnet",
      "max_tokens": 4096,
      "backend": "anthropic"
    },
    {
      "name": "haiku",
      "max_tokens": 4096,
      "backend": "anthropic"
    },
    {
      "name": "opus",
      "max_tokens": 4096,
      "backend": "anthropic"
    },
    {
      "name": "mixtral-8x7b-32768",
      "max_tokens": 32768,
      "backend": "groq"
    },
    {
      "name": "llama3:8b",
      "max_tokens": 8192,
      "backend": "ollama"
    },
    {
      "name": "llama3-70b-8192",
      "max_tokens": 8192,
      "backend": "groq"
    },
    {
      "name": "samantha-mistral:7b-instruct-q4_0",
      "max_tokens": 8000,
      "backend": "ollama"
    }
  ]
}



def get_model_config(model: str):  # -> Dict[str, Any]:
    try:
        model_config = next(m for m in CONFIG["models"] if m['name'] == model)
    except StopIteration:
        raise LookupError(f"Model {model} not found in config.json")
    return model_config
