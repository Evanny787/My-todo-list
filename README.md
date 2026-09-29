# Todo app (React + FastAPI + SQLite/Turso)

## Run on your computer
Terminal 1:  pip install fastapi uvicorn && uvicorn api.index:app --reload --port 8000
Terminal 2:  npm install && npm run dev      (then open the address it prints)

Locally your todos are saved in a file called todos.db.

## Run on Vercel
1. Create a free database at turso.tech, then copy its URL (starts with libsql://)
   and create an auth token for it.
2. Put this folder in a GitHub repo and import it into Vercel.
3. Before deploying, in Vercel > Project Settings > Environment Variables, add:
     TURSO_DATABASE_URL  = the libsql:// URL
     TURSO_AUTH_TOKEN    = the token
4. Deploy. Your todos are now saved permanently.
