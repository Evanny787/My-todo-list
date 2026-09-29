import { useState, useEffect } from "react";

// Small helper that talks to our Python backend
async function api(path, method = "GET", body) {
  const res = await fetch("/api" + path, {
    method,
    headers: { "Content-Type": "application/json" },
    body: body ? JSON.stringify(body) : undefined,
  });
  return res.json();
}

export default function App() {
  const [todos, setTodos] = useState([]);
  const [text, setText] = useState("");

  useEffect(() => {
    api("/todos").then(setTodos);
  }, []);

  async function addTodo(e) {
    e.preventDefault();
    if (!text.trim()) return;
    setTodos(await api("/todos", "POST", { title: text }));
    setText("");
  }

  async function toggle(todo) {
    setTodos(await api("/todos/" + todo.id, "PATCH", { done: !todo.done }));
  }

  async function remove(todo) {
    setTodos(await api("/todos/" + todo.id, "DELETE"));
  }

  async function move(index, direction) {
    const ids = todos.map((t) => t.id);
    const target = index + direction;
    [ids[index], ids[target]] = [ids[target], ids[index]];
    setTodos(await api("/order", "PUT", { ids }));
  }

  return (
    <div className="card">
      <h1>My Todo List</h1>
      <form onSubmit={addTodo}>
        <input
          type="text"
          value={text}
          placeholder="What needs doing?"
          onChange={(e) => setText(e.target.value)}
        />
        <button type="submit">Add</button>
      </form>
      {todos.length === 0 && <p className="empty">Nothing here yet. Add your first item!</p>}
      <ul>
        {todos.map((todo, i) => (
          <li key={todo.id} className={todo.done ? "done" : ""}>
            <input type="checkbox" checked={todo.done} onChange={() => toggle(todo)} />
            <span>{todo.title}</span>
            <button className="small" disabled={i === 0} onClick={() => move(i, -1)}>↑</button>
            <button className="small" disabled={i === todos.length - 1} onClick={() => move(i, 1)}>↓</button>
            <button className="small" onClick={() => remove(todo)}>✕</button>
          </li>
        ))}
      </ul>
    </div>
  );
}
