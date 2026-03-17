"""Simple JSON-based chat persistence."""

import json
import uuid
from datetime import datetime
from pathlib import Path

from langchain_core.messages import AIMessage, HumanMessage

STORE_PATH = Path(__file__).resolve().parent.parent / "chat_history.json"


def _serialize_history(msgs: list) -> list[dict]:
    """Convert LangChain message objects to JSON-safe dicts."""
    result = []
    for msg in msgs:
        if hasattr(msg, "type") and hasattr(msg, "content"):
            result.append({"type": msg.type, "content": msg.content})
        elif isinstance(msg, dict):
            result.append(msg)
    return result


def _deserialize_history(data: list) -> list:
    """Reconstruct LangChain message objects from stored dicts."""
    constructors = {
        "human": HumanMessage,
        "ai": AIMessage,
    }
    result = []
    for item in data:
        if isinstance(item, dict) and "type" in item and "content" in item:
            cls = constructors.get(item["type"])
            if cls:
                result.append(cls(content=item["content"]))
        # Skip items we can't deserialize (e.g. system, tool messages)
    return result


def _load_store() -> dict:
    if STORE_PATH.exists():
        try:
            return json.loads(STORE_PATH.read_text())
        except (json.JSONDecodeError, OSError):
            return {}
    return {}


def _save_store(store: dict) -> None:
    STORE_PATH.write_text(json.dumps(store, indent=2, default=str))


def create_chat() -> str:
    """Create a new chat and return its ID."""
    store = _load_store()
    chat_id = uuid.uuid4().hex[:8]
    store[chat_id] = {
        "title": "New Chat",
        "created": datetime.now().isoformat(),
        "messages": [],
        "chat_history": [],
    }
    _save_store(store)
    return chat_id


def save_chat(chat_id: str, title: str, messages: list, chat_history: list) -> None:
    """Persist a chat's messages and LangChain history."""
    store = _load_store()
    if chat_id not in store:
        store[chat_id] = {"created": datetime.now().isoformat()}
    store[chat_id]["title"] = title
    store[chat_id]["messages"] = messages
    store[chat_id]["chat_history"] = _serialize_history(chat_history)
    _save_store(store)


def load_chat(chat_id: str) -> dict | None:
    """Load a single chat by ID."""
    store = _load_store()
    data = store.get(chat_id)
    if data is None:
        return None
    # Deserialize chat_history back into LangChain message objects
    data = dict(data)  # shallow copy to avoid mutating the store
    data["chat_history"] = _deserialize_history(data.get("chat_history", []))
    return data


def list_chats() -> list[tuple[str, str, str]]:
    """Return list of (chat_id, title, created) sorted newest first."""
    store = _load_store()
    chats = []
    for cid, data in store.items():
        chats.append((cid, data.get("title", "Untitled"), data.get("created", "")))
    chats.sort(key=lambda x: x[2], reverse=True)
    return chats


def delete_chat(chat_id: str) -> None:
    """Delete a chat by ID."""
    store = _load_store()
    store.pop(chat_id, None)
    _save_store(store)


def derive_title(messages: list) -> str:
    """Derive a short title from the first user message."""
    for msg in messages:
        if msg.get("role") == "user":
            text = msg["content"]
            return text[:50] + ("..." if len(text) > 50 else "")
    return "New Chat"
