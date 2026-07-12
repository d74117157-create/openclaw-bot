# 🛒 KingLulu Shop — Temu Clone

A visual e-commerce app built for fun and learning. Part of the KingLulu Digital Empire.

## Quick Start

```bash
# Terminal 1: Backend
cd temu_clone
python backend.py
# → http://localhost:8001

# Terminal 2: Frontend
cd temu_clone
npm install
npm run dev
# → http://localhost:5173
```

## Features
- 🎨 Dark theme with neon accents
- 🔍 Real-time search
- 🏷️ Category filtering
- 🛒 Shopping cart
- ⭐ Product ratings
- 📱 Responsive design

## Products
All products are digital empire tools:
- AI Bot Starter Kit ($29.99)
- Empire Blueprint ($97.00)
- Trading Signals Pro ($49.99)
- YouTube Automation Pack ($39.99)
- Telegram Mini App Template ($59.99)
- Chess Mastery Course ($79.99)
- Discord Bot Swarm ($149.99)
- Passive Income Hacks 2026 ($19.99)

## Tech Stack
- **Backend**: Python FastAPI + SQLite
- **Frontend**: React 18 + Vite
- **Styling**: Pure CSS (no frameworks)
- **Icons**: Lucide React

## API Endpoints
- `GET /api/products` — List products (optional: ?category=, ?search=)
- `GET /api/products/{id}` — Get single product
- `POST /api/orders` — Create order
- `GET /api/orders` — List orders
- `GET /api/stats` — Shop stats
- `GET /api/health` — Health check

## Claude Code Integration
This project is designed to be built and extended using Claude Code in VS Code or GitHub Codespaces.

Ask Claude:
- "Add a checkout page with Stripe integration"
- "Make the product cards animate on hover"
- "Add user authentication with JWT"
- "Create an admin dashboard for orders"
- "Add dark/light mode toggle"

## Empire Context
This is a fun side project within the KingLulu Digital Empire. The real money is in the bot swarm, but this teaches e-commerce skills that scale.

**Money while you sleep. Bots never sleep.**
