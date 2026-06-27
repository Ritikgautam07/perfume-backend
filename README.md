# Perfume AI — Backend

FastAPI backend for the futuristic perfume store: products & categories, AI Scent Finder,
Pack Builder, first-order discount logic, Razorpay checkout, and loyalty points.

## Stack
FastAPI · Supabase (Postgres + Auth) · Razorpay · matches the tech stack you specified.

## 1. Setup

```bash
cd perfume-backend
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # then fill in your real keys
```

## 2. Database

1. Create a project at supabase.com (free tier is fine to start).
2. Open **SQL Editor** in the Supabase dashboard, paste the contents of `supabase_schema.sql`, and run it.
   This creates all tables, sets up Row Level Security, and seeds:
   - 5 categories (Daily, Premium, Combo, Trending, AI Recommended)
   - 1 pack tier (any 3 items -> ₹500)
   - the `WELCOME15` first-order discount code
   - 3 sample products (Cyber Oud, Ocean Mist, Silver Noir) matching your example
3. Copy your **Project URL**, **service_role key**, and **JWT Secret** from
   Project Settings -> API into `.env`. Use the service_role key here (backend-only,
   never ship it to the frontend) — it's what lets the API bypass Row Level Security.

## 3. Razorpay

Grab test keys from the Razorpay Dashboard -> Settings -> API Keys and put them in `.env`.
For the webhook (optional but recommended), point Settings -> Webhooks at:
`https://your-api-domain.com/payments/webhook`

## 4. Run

```bash
uvicorn app.main:app --reload --port 8000
```

Interactive API docs: `http://localhost:8000/docs`

## How the frontend talks to this

The frontend uses **Supabase Auth** directly (sign up / log in via `supabase-js`), then sends
the resulting access token on every request:

```js
const { data } = await supabase.auth.getSession();
fetch("http://localhost:8000/orders", {
  method: "POST",
  headers: {
    "Content-Type": "application/json",
    Authorization: `Bearer ${data.session.access_token}`,
  },
  body: JSON.stringify({ items: [{ product_id: "...", quantity: 1 }] }),
});
```

The API verifies that token itself (`app/utils/security.py`) — no separate login endpoint needed here.

## API Reference

| Endpoint | Method | Purpose |
|---|---|---|
| `/categories` | GET | Smart category cards (Daily/Premium/Combo/Trending/AI) |
| `/products` | GET | Product list — filter by `category_id`, `min_price`, `max_price`, `trending`, `ai_recommended`, `search` |
| `/products/{id}` | GET | Single product detail for the product card (luxury %, freshness %, duration) |
| `/scent-finder` | POST | AI Scent Finder quiz — body `{ "moods": ["fresh", "luxury"] }` |
| `/scent-finder/chatbot` | POST | "Find my scent" chatbot — body `{ "message": "I want something romantic" }` |
| `/pack-builder/tiers` | GET | Available pack pricing tiers |
| `/pack-builder/calculate` | POST | Bundle pricing — body `{ "product_ids": [...] }` |
| `/discounts/welcome` | GET | Checks first-order eligibility for the WELCOME15 banner |
| `/discounts/validate` | POST | Validate any discount code at checkout |
| `/orders` | POST | Create order + Razorpay order (checkout step 1) |
| `/orders/verify` | POST | Verify Razorpay signature, mark paid, award loyalty points (checkout step 2) |
| `/orders` | GET | Logged-in user's order history |
| `/orders/{id}` | GET | Single order detail |
| `/loyalty` | GET | Points balance + transaction history |
| `/loyalty/redeem-preview` | POST | Preview ₹ value before redeeming points at checkout |
| `/payments/webhook` | POST | Razorpay server-to-server confirmation |

## 5. Deploy

First, push this folder to a GitHub repo (deploys are usually connected to a repo, not a local
folder) — `git init`, `git add .`, `git commit -m "perfume backend"`, then push to a new repo
on GitHub. I can't run these git/deploy commands for you from here since this sandbox has no
network access, but here's exactly what to run on your machine.

### Option A — Railway (recommended: simplest, runs as a normal always-on server)

1. Go to railway.app -> **New Project -> Deploy from GitHub repo** -> select this repo.
2. Railway auto-detects the `Procfile` and runs `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.
3. Go to the **Variables** tab and add everything from your `.env` (`SUPABASE_URL`,
   `SUPABASE_SERVICE_KEY`, `SUPABASE_JWT_SECRET`, `RAZORPAY_KEY_ID`, `RAZORPAY_KEY_SECRET`,
   `FRONTEND_URL`).
4. Railway gives you a live URL like `https://your-app.up.railway.app` — that's your API base URL.

### Option B — Render (also simple, free tier available)

1. Go to render.com -> **New -> Web Service** -> connect this repo.
2. Build command: `pip install -r requirements.txt`
3. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add the same environment variables as above in the **Environment** tab.
5. Note: Render's free tier spins the service down after ~15 min idle, so the first
   request after a quiet period will be slow (~30s cold start). Fine for testing, upgrade
   to a paid instance before launch if that matters to you.

### Option C — Vercel (matches your original stack list)

This repo includes `vercel.json` and `api/index.py` so it deploys as-is, but note: Vercel runs
FastAPI as **serverless functions**, not a persistent server. That's totally fine for this API
(no websockets or long-lived connections here), just know that each request can have a small
cold-start delay.

1. Install the CLI: `npm i -g vercel`
2. From this folder, run `vercel` and follow the prompts (link to a new project).
3. Add env vars: `vercel env add SUPABASE_URL`, repeat for each variable, or paste them into
   the project's **Settings -> Environment Variables** on vercel.com.
4. `vercel --prod` to ship it.

### After deploying (any option)

- Update `FRONTEND_URL` to your real frontend domain once that's deployed too, so CORS allows it.
- Update the Razorpay webhook URL in their dashboard to `https://<your-live-domain>/payments/webhook`.
- Visit `https://<your-live-domain>/docs` to confirm it's live and click through the endpoints.

## Notes & next steps

- **Admin auth**: `POST/PUT/DELETE /products` and `POST /categories` aren't auth-gated yet —
  add an admin check (e.g. a `role` column on `profiles`) before deploying.
- **Chatbot**: `extract_moods_from_text` is a simple keyword matcher so the bot works out of
  the box with zero extra API keys. Swap it for a real LLM call (Anthropic/OpenAI) in
  `app/services/recommendation.py` once you want it to understand more nuanced phrasing.
- **Images**: `image_url` on each product is just a link — host your renders on Supabase
  Storage, Cloudinary, or anywhere with a public URL.
- **Limited-edition countdown**: not in the schema yet — add an `available_until` timestamp
  column to `products` and filter on it if you want that feature server-side too.
