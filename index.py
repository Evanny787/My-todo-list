import json
import os
import sqlite3
import urllib.request
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

# --- Where is the database? -------------------------------------------------
# On Vercel we use Turso (a hosted SQLite database), configured with two
# environment variables. On your own computer, if those variables are not set,
# we use a plain SQLite file called todos.db instead.
TURSO_URL = os.environ.get("TURSO_DATABASE_URL", "").replace("libsql://", "https://").rstrip("/")
TURSO_TOKEN = os.environ.get("TURSO_AUTH_TOKEN", "")
LOCAL_DB = str(Path(__file__).parent.parent / "todos.db")


def to_arg(value):
    if isinstance(value, int):
        return {"type": "integer", "value": str(value)}
    return {"type": "text", "value": str(value)}


def from_cell(cell):
    if cell["type"] == "null":
        return None
    if cell["type"] == "integer":
        return int(cell["value"])
    return cell["value"]


def run_batch(statements):
    """Run a list of (sql, args) in order. Returns the rows of the LAST one."""
    if TURSO_URL:
        requests = [
            {"type": "execute", "stmt": {"sql": sql, "args": [to_arg(a) for a in args]}}
            for sql, args in statements
        ]
        requests.append({"type": "close"})
        req = urllib.request.Request(
            TURSO_URL + "/v2/pipeline",
            data=json.dumps({"requests": requests}).encode(),
            headers={
                "Authorization": "Bearer " + TURSO_TOKEN,
                "Content-Type": "application/json",
                "User-Agent": "todo-app",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                results = json.load(resp)["results"]
        except Exception as e:
            raise HTTPException(502, f"Could not reach the database: {e}")
        for r in results:
            if r["type"] == "error":
                raise HTTPException(500, r["error"]["message"])
        last = results[len(statements) - 1]["response"]["result"]
        names = [c["name"] for c in last["cols"]]
        return [dict(zip(names, [from_cell(c) for c in row])) for row in last["rows"]]

    # Local mode: a plain SQLite file
    conn = sqlite3.connect(LOCAL_DB)
    conn.row_factory = sqlite3.Row
    try:
        rows = []
        for sql, args in statements:
            rows = [dict(r) for r in conn.execute(sql, args).fetchall()]
        conn.commit()
        return rows
    finally:
        conn.close()


SETUP = ("""CREATE TABLE IF NOT EXISTS todos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    done INTEGER NOT NULL DEFAULT 0,
    position INTEGER NOT NULL
)""", [])
LIST = ("SELECT id, title, done FROM todos ORDER BY position", [])


def change(*statements):
    """Run some changes, then return the fresh todo list."""
    rows = run_batch([SETUP, *statements, LIST])
    return [{"id": r["id"], "title": r["title"], "done": bool(r["done"])} for r in rows]


# --- API routes ---------------------------------------------------------------
class NewTodo(BaseModel):
    title: str


class DoneUpdate(BaseModel):
    done: bool


class Order(BaseModel):
    ids: list[int]


@app.get("/api/todos")
def list_todos():
    return change()


@app.post("/api/todos")
def add_todo(todo: NewTodo):
    title = todo.title.strip()
    if not title:
        raise HTTPException(400, "Title cannot be empty")
    return change((
        "INSERT INTO todos (title, position) "
        "SELECT ?, COALESCE(MAX(position), 0) + 1 FROM todos",
        [title],
    ))


@app.patch("/api/todos/{todo_id}")
def check_todo(todo_id: int, update: DoneUpdate):
    return change(("UPDATE todos SET done = ? WHERE id = ?", [int(update.done), todo_id]))


@app.delete("/api/todos/{todo_id}")
def delete_todo(todo_id: int):
    return change(("DELETE FROM todos WHERE id = ?", [todo_id]))


@app.put("/api/order")
def reorder(order: Order):
    return change(*[
        ("UPDATE todos SET position = ? WHERE id = ?", [pos, todo_id])
        for pos, todo_id in enumerate(order.ids)
    ])
