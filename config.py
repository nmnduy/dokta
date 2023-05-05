import json

CONFIG = json.load(open("config.json"))



def get_model_config(model: str):  # -> Dict[str, Any]:
    try:
        model_config = next(m for m in CONFIG["models"] if m['name'] == model)
    except StopIteration:
        raise LookupError(f"Model {model} not found in config.json")
    return model_config
