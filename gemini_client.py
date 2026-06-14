"""
gemini_client.py

Small wrapper around the Gemini API. Stores the API key in a local config
file in the user's home directory so it only needs to be entered once.
"""

import json
import os
import urllib.error
import urllib.request
from pathlib import Path


CONFIG_PATH = Path.home() / ".pdfmind_config.json"
MODEL = "gemini-2.5-flash-lite"
API_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={key}"


def get_api_key():
    """Return the stored API key, prompting and saving it if missing."""
    key = _read_stored_key()
    if key:
        return key

    print("No Gemini API key found.")
    print("Get a free key from https://aistudio.google.com/app/apikey")
    key = input("Paste your Gemini API key: ").strip()

    if not key:
        raise RuntimeError("No API key provided.")

    _save_key(key)
    return key


def _read_stored_key():
    if not CONFIG_PATH.exists():
        return None

    try:
        data = json.loads(CONFIG_PATH.read_text())
    except (json.JSONDecodeError, OSError):
        return None

    return data.get("api_key")


def _save_key(key):
    CONFIG_PATH.write_text(json.dumps({"api_key": key}))
    try:
        os.chmod(CONFIG_PATH, 0o600)
    except OSError:
        pass


def update_api_key():
    """Prompt for a new key and overwrite the stored one."""
    key = input("Paste your Gemini API key: ").strip()
    if not key:
        print("No key entered, nothing was changed.")
        return
    _save_key(key)
    print("API key saved.")


def ask_gemini(prompt, temperature=0.4):
    """Send a prompt to Gemini and return the text response."""
    api_key = get_api_key()
    url = API_URL.format(model=MODEL, key=api_key)

    body = json.dumps({
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": temperature},
    }).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as error:
        details = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Gemini API error ({error.code}): {details[:300]}")
    except urllib.error.URLError as error:
        raise RuntimeError(f"Could not reach Gemini API: {error}")

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        raise RuntimeError("Unexpected response shape from Gemini API.")
