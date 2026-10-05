# Campus Customs — Homework 4

Campus Customs is a React/Vite/TypeScript storefront with a FastAPI backend
and PydanticAI shopping concierge.

## Local data

Place the supplied local-only data pack at `data/campus_customs.db` and
`data/products/`. These files are intentionally ignored by Git and are not
included in this repository.

Copy `.env.example` to `.env` and put the real `PORTKEY_API_KEY` there. Never
commit the real `.env`.

## Run it

Install backend dependencies in a local environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Start the API from its directory:

```bash
cd backend
../.venv/bin/uvicorn main:app --reload --port 8000
```

In another terminal, start the frontend:

```bash
cd frontend
npm install
npm run dev
```

The frontend uses the API for catalogue data, images, authentication, chat,
and logged-in chat history. See `output/harness.md` for the system contract,
safety rules, and evidence files.
