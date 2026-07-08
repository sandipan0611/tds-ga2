import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Layer 1: hardcoded defaults
DEFAULTS = {
    "port": 8000,
    "workers": 1,
    "debug": False,
    "log_level": "info",
    "api_key": "default-secret-000",
}

# Layer 2: config.<env>.yaml
YAML_LAYER = {
    "workers": 14,
}

# Layer 3: .env file (NUM_WORKERS aliases to `workers`)
ENV_FILE_LAYER = {
    "workers": 16,       # from NUM_WORKERS
    "api_key": "key-fawdhqnm99",
}

# Layer 4: OS-level environment variables (APP_* prefix).
# Falls back to the assigned values if the real env vars aren't set on the host.
OS_ENV_DEFAULTS = {
    "port": "8085",
    "workers": "9",
    "debug": "true",
    "log_level": "info",
}
OS_ENV_LAYER = {
    "port": os.environ.get("APP_PORT", OS_ENV_DEFAULTS["port"]),
    "workers": os.environ.get("APP_WORKERS", OS_ENV_DEFAULTS["workers"]),
    "debug": os.environ.get("APP_DEBUG", OS_ENV_DEFAULTS["debug"]),
    "log_level": os.environ.get("APP_LOG_LEVEL", OS_ENV_DEFAULTS["log_level"]),
}


def to_bool(v) -> bool:
    if isinstance(v, bool):
        return v
    return str(v).strip().lower() in ("true", "1", "yes", "on")


def coerce(key: str, value):
    if key in ("port", "workers"):
        return int(value)
    if key == "debug":
        return to_bool(value)
    return str(value)


@app.get("/effective-config")
async def effective_config(request: Request):
    merged: dict = {}
    for layer in (DEFAULTS, YAML_LAYER, ENV_FILE_LAYER, OS_ENV_LAYER):
        merged.update(layer)

    # Layer 5: CLI overrides via repeatable ?set=key=value query params (highest precedence)
    for set_val in request.query_params.getlist("set"):
        if "=" in set_val:
            k, v = set_val.split("=", 1)
            merged[k] = v

    result = {
        "port": coerce("port", merged.get("port")),
        "workers": coerce("workers", merged.get("workers")),
        "debug": coerce("debug", merged.get("debug")),
        "log_level": coerce("log_level", merged.get("log_level")),
    }
    result["api_key"] = "****"
    return result
