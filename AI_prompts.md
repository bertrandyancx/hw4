# AI Prompts

## Logging format

- Keep one section per homework problem.
- Include the problem number and title.
- Include at least one prompt I typed, rewritten in my own words as closely as possible.
- Add one follow-up prompt if needed, reflecting what was lacking in the first.
- Keep this file updated with every prompt I give the vibe coder.

## Problem 1 — Set up the Campus Customs project data

### Prompt in my own words

Move the already-unzipped Campus Customs data from the AI-folder into Homework 4. The project needs `data/campus_customs.db` and `data/products/`, with the product image paths matching the catalogue table. Do not commit the database or product images.

### Follow-up prompt

Confirm whether the data has already been unzipped and verify that the database and product images are present in Homework 4.

## Problem 2 — Understand the database and start the harness

### Prompt in my own words

Inspect `data/campus_customs.db` and understand the fields in every table, at minimum `catalogue`, `inventory`, and `users`. Start `output/harness.md`, list each table and field, and add one short explanation of why each field matters for the shop or chatbot. Keep growing the harness in later problems with models, tools, safety, and specifications.

### Follow-up prompt

No follow-up needed yet; the database schema was available and the initial harness has been started.

## Problem 3 — Title to be added

### Prompt in my own words

Scaffold a React + Vite + TypeScript frontend for Campus Customs. Add a top navigation bar linking to Home, Products, About Us, Log in, and Create account. Write original Home and About Us copy informed by the collegiate merchandise style of yalebulldogblue.com, without copying its text. Then, still on Problem 3, connect Products to the SQLite catalogue through a small FastAPI backend: show database image paths, product names, prices, and short descriptions; make cards open single-product pages with full text and size stock; add a floating chat stub; and start `backend/main.py` so it can serve products and images before becoming the agent backend in Problem 5.

### Follow-up prompt

Follow-up prompt: Keep this work under Problem 3 and use the database as the source of truth for catalogue images, product details, and inventory rather than hard-coding the product cards.

## Problem 4 — Create account and login

### Prompt in my own words

Build a normal create-account and login flow. Registration needs first name, last name, email, password, and confirm password; login needs email and password. New accounts must be inserted into the `users` table, and passwords must be stored securely so plaintext passwords are never recoverable. Use the seeded test user to verify login, then verify that a brand-new account can register and log in too. Document the authentication storage and password protection in `output/harness.md`.

### Follow-up prompt

No follow-up needed yet; both seeded-user login and new-account verification are required before this problem is complete.

## Problem 5 — Title to be added

### Prompt in my own words

Build the Campus Customs shop chatbot as a PydanticAI agent behind FastAPI. Keep `backend/main.py` as the Uvicorn entry point and add `backend/prompts/prompt.md`, `backend/agent.py`, `backend/tools.py`, and `backend/models.py`. Expose a chat route that the frontend widget can call, use the Portkey model with the project API key, add Campus Customs voice and safety rules, and document how the frontend talks to FastAPI and how the agent loads its prompt and model. The backend must run from the `backend/` folder with `uvicorn main:app --reload --port 8000`.

### Follow-up prompt

No follow-up needed yet; the initial product-search chatbot wiring is complete and the tools/prompt can expand in later problems.

Follow-up prompt: When a shopper asks about a type of item, return structured product matches from the catalogue so the website can render image cards. Keep those cards linked to the existing single-product detail route, and update the prompt and harness to describe the contract.

## Problem 6 — Title to be added

### Prompt in my own words

To be added when Problem 6 is provided.

### Follow-up prompt

None needed yet.

## Problem 9 — Improve shop and agent usability

### Prompt in my own words

Choose and implement two front-end usability improvements and two agent/backend usability improvements. Make the shop easier to browse and make agent output more accurate, useful, safe, fast, or cost-aware.

### Follow-up prompt

Implement catalogue search with sorting and a helpful empty state on the frontend. Improve backend search relevance with bounded results, and pass only a bounded recent chat context to the agent so follow-up questions work without sending an unnecessarily large history.

## Design polish — Make Campus Customs feel like a real storefront

### Prompt in my own words

Add imaginative storefront design: fonts, color, hierarchy, motion, product presentation, and chat feel. Give the site flair while keeping it useful, then write a short concrete `output/design.md` explaining what changed and why it should help customers stay and buy.

### Follow-up prompt

No follow-up needed; the design pass and rationale document are complete.

## App check — Live-site evidence

### Prompt in my own words

Run the live site and create `output/app_check.html` with clear headings, screenshots, and short captions for an inventory chat answer, dynamic category-result cards, and one Problem 9 usability improvement. Put the linked screenshot files in `output/app_check_images/` using relative paths so the HTML can be double-clicked open.

### Follow-up prompt

No follow-up needed; all three screenshots and the linked grading page were created.

## Audit trail, safety, and harness completion

### Prompt in my own words

Keep an append-only `output/audit_trail.json` for agent-loop activity with time, tool name, short arguments/results, and stop reason. Add practical safety rules to the agent prompt, and finish `output/harness.md` with the model fields and rationale, tools and abilities, safety rules, loop limits, model choice, and front/back run commands.

### Follow-up prompt

No follow-up needed; audit instrumentation, safety guidance, and the complete harness specification are in place.
