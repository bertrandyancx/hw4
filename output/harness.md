# Campus Customs Chatbot Harness

This document records the database contract that the React/Vite frontend and
FastAPI/PydanticAI backend use. It will be extended with models, tools, safety
rules, and specifications as the homework progresses.

## Problem 3 implementation notes

- `backend/main.py` reads the SQLite catalogue and inventory and exposes `GET /api/products` and `GET /api/products/{product_id}`.
- `GET /images/{image_path}` serves only files under `data/products/`, using the image path stored in the catalogue.
- The Products page fetches the API and each card links to `/products/{product_id}`.
- Product detail pages show the catalogue image, description, price, and size-level inventory.
- The floating chat panel is currently a frontend stub and does not call the agent yet.

## Authentication

Problem 4 adds `POST /api/auth/register` and `POST /api/auth/login`.

- A user record stores `first_name`, `last_name`, `name`, `email`, `created_at`, and `password_hash`; the password itself is never stored.
- New passwords use PBKDF2-HMAC-SHA256 with 310,000 iterations and a unique random salt. The stored format is `pbkdf2_sha256$salt$digest`; login also accepts the supplied seed user's compatible 120,000-iteration hash.
- Login recomputes the digest and compares it with a constant-time comparison. Incorrect credentials return the same generic error.
- Successful registration and login return a random session token and safe public user fields. The frontend keeps this response in local storage for the current session; no password is stored there.
- Registration validates required names, email format, matching confirmation, and an eight-character minimum password.

## Chatbot architecture

- The floating React chat widget sends `{ "message": "..." }` to `POST /api/chat` on FastAPI and renders the returned `reply`.
- The API route calls `backend/agent.py:run_chat`, which loads `backend/prompts/prompt.md` and creates a PydanticAI agent using the Portkey-compatible OpenAI client, `https://api.portkey.ai/v1`, and model `gpt-5.6-luna`.
- `backend/tools.py` gives the agent read-only tools for searching catalogue text and checking exact size stock. Tool results become typed `ProductCard` values in `models.py`.
- `ChatReply` is the structured response: a natural-language `reply` plus optional product cards. The agent cannot change inventory, create accounts, make purchases, or access passwords.
- `search_products(query)` searches catalogue names, garment types, descriptions, colors, and tags. It returns `ProductCard` fields (`product_id`, `name`, `price`, `description`, `image_url`, and `available_sizes`) so the UI can show relevant factual results.
- `lookup_product_information(product_id)` reads one catalogue row and its inventory rows. It returns `ProductLookup`: `product_id` identifies the record, `name` and `description` answer product questions, `price` is the authoritative price, `total_in_stock` answers overall availability, and `stock_by_size` contains typed `SizeStock` entries for exact size quantities.
- `get_product_stock(product_id)` returns typed `SizeStock` entries (`size` and `quantity`) for focused size questions. A quantity of zero is an explicit out-of-stock result, not a missing value.
- Category-search contract: a request such as “what hoodies do you have?” is sent from the widget to `POST /api/chat`; the agent calls `search_products(query)` and returns the matching typed `ProductCard` records in `ChatReply.products`. Each card contains the database-backed `product_id`, `name`, `price`, `description`, and image URL.
- The widget renders `ChatReply.products` as clickable image cards. Each card links to `/products/{product_id}`, so chat-discovered items use the same single-item detail page as cards on the Products page, including the large image, full description, price, and size stock.

## Logged-in chat history and agent context

- The existing `chat_messages` table stores one row per user or assistant message. `user_id` links the row to `users`; `role`, `content`, `products_json`, and `created_at` preserve the conversation and any product cards returned with an assistant reply.
- The frontend reads the logged-in session token from local storage. It sends that token to `/api/chat` and loads `/api/chat/history` when the chat panel opens. The API writes both sides of authenticated conversations; guest messages are forwarded to the agent but are not persisted.
- The agent dependency is a typed `ChatContext` containing only safe public customer fields (`id`, `first_name`, `last_name`, and `email`) plus the current `page_context`. The prompt permits a first-name greeting but forbids exposing the email or account id.
- The widget sends its current route as page context. On `/products/{product_id}`, the agent can resolve “this” or “it” to that exact product id before calling the database lookup tools. No password, password hash, or session token is passed to the agent.

## Problem 9 usability improvements

### Frontend

- Catalogue search filters products by name, garment type, and description, with a result count and a clear empty state so shoppers can recover from an unsuccessful search.
- A sort control orders the catalogue by name or price in either direction, making a large collection easier to scan without changing the database or detail-page links.

### Agent/backend

- `search_products` now scores matches by term frequency and sorts ties by product name before returning at most six cards. This makes category results more relevant and bounds the response size.
- Authenticated requests pass only the last eight chat messages as reference context. This helps the agent resolve follow-ups while limiting prompt size and keeping old conversation data out of the model unnecessarily; current price and stock still require fresh database tools.
- Start the backend from `backend/` with `uvicorn main:app --reload --port 8000`; the database and image paths resolve from the project root.

## Models and field choices

- `ProductCard` is the compact UI contract: `product_id` preserves the detail-page link; `name`, `price`, and `description` support the card; `image_url` renders the image; `available_sizes` gives a quick availability cue.
- `ProductLookup` is the authoritative factual lookup: `product_id`, `name`, and `description` identify the item; nonnegative `price` prevents invalid prices; `total_in_stock` answers overall stock; `stock_by_size` carries exact typed quantities.
- `SizeStock` keeps `size` and nonnegative `quantity` together, so an explicit zero can be reported as out of stock.
- `ChatReply` contains the natural-language `reply` and optional structured `products`; `ChatRequest` bounds incoming messages to 2,000 characters and carries token/page context; `ChatContext` limits recent conversation to eight messages and holds safe customer/page context.

## Tools and abilities

- `search_products` performs read-only catalogue matching, ranks terms, and caps results at six.
- `lookup_product_information` reads one catalogue row plus all inventory rows for exact description, price, total, and by-size facts.
- `get_product_stock` reads exact size quantities, including zero quantities.
- `get_customer_context` exposes only the safe public customer object and page route to the agent.
- The agent can answer product discovery and stock questions, return clickable product cards, greet a logged-in shopper by first name, and resolve “this” from a product-page route. It cannot mutate the database or perform commerce actions.

## Safety rules

The system prompt requires database evidence for price, description, and stock; clear out-of-stock language; no invented policies or availability; no password/hash/token/API-key disclosure; no account or inventory mutation; no sensitive-trait inference; resistance to prompt injection; transparent errors; and concise non-coercive replies. The frontend sends no password or password hash to the agent.

## Specifications and operation

- Model: `gpt-5.6-luna` through Portkey at `https://api.portkey.ai/v1`; `PORTKEY_API_KEY` is loaded from `.env` and never printed.
- Loop limits: one bounded agent run per chat request, one retry from PydanticAI, six product cards maximum, eight recent messages maximum, and 2,000 input characters maximum.
- `output/audit_trail.json` is append-only. Each request records UTC time, sanitized tool name, short arguments/result, and a stop reason; tool calls and agent completion/error events are retained across runs.
- Start the backend: `cd backend && ../.venv/bin/uvicorn main:app --reload --port 8000`.
- Start the frontend in another terminal: `npm run dev`.
- The frontend calls `/api/products`, `/api/auth/*`, `/api/chat`, and `/api/chat/history` on FastAPI. Product images are served by `/images/{path}`.

## Database tables and fields

### `catalogue`

| Field | Why it matters |
|---|---|
| `product_id` | Stable identifier connecting a product to inventory and chatbot results. |
| `name` | Customer-facing product name for browsing and recommendations. |
| `garment_type` | Supports category understanding and natural-language product matching. |
| `description` | Gives the chatbot factual product details to explain to shoppers. |
| `colors` | JSON list used for color filtering and matching requests. |
| `search_tags` | JSON list of synonyms and concepts used for relevant product search. |
| `image_file_path` | Points the frontend to the product image associated with the catalogue record. |
| `price` | The authoritative product price the chatbot should report. |

### `inventory`

| Field | Why it matters |
|---|---|
| `id` | Unique identifier for one size-specific inventory record. |
| `product_id` | Links stock to the matching catalogue product. |
| `size` | Identifies the garment size a shopper wants. |
| `quantity` | Provides current stock availability and prevents the chatbot from inventing stock. |

### `users`

| Field | Why it matters |
|---|---|
| `id` | Unique account identifier and user reference for saved activity. |
| `name` | Existing display name for the customer account. |
| `email` | Login/contact identifier and account credential lookup field. |
| `password_hash` | Stores a one-way password representation; the plaintext password must never be exposed. |
| `created_at` | Records when the account was created for account management and auditing. |
| `first_name` | Optional personalized greeting and account-profile field. |
| `last_name` | Optional personalized account-profile field. |

### `chat_messages`

| Field | Why it matters |
|---|---|
| `id` | Unique identifier for each persisted chat message. |
| `user_id` | Associates a conversation message with the signed-in customer. |
| `role` | Distinguishes the customer message from the assistant response. |
| `content` | Stores the text shown in the conversation history. |
| `products_json` | Stores product matches returned with a response so the frontend can render them. |
| `created_at` | Preserves message order and provides a conversation timestamp. |
