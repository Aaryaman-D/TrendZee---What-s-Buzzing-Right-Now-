# TrendZee 🔥
### Social Signal Intelligence Platform

> *Social Media Optimized for Engagement. We Optimize for Insight.*

TrendZee is a production-ready Django SaaS platform that aggregates trending social media signals and presents them in a structured, AI-enhanced intelligence dashboard.

---

## 🚀 Quick Start

### 1. Create Virtual Environment

```bash
cd trendzee
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your GEMINI_API_KEY
```

### 4. Run Migrations

```bash
python manage.py migrate
```

### 5. Seed Sample Data

```bash
python manage.py seed_trends
```

### 6. Create Superuser

```bash
python manage.py createsuperuser
```

### 7. Run Development Server

```bash
python manage.py runserver
```

Visit: http://localhost:8000

---

## 🏗️ Project Structure

```
trendzee/
├── manage.py
├── requirements.txt
├── .env.example
│
├── trendzee/           # Django project config
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── accounts/           # Custom auth app
│   ├── models.py       # CustomUser model
│   ├── views.py        # Register, Login, Verify
│   ├── forms.py        # Auth forms
│   ├── validators.py   # Strong password validator
│   └── urls.py
│
├── trends/             # Core trends app
│   ├── models.py       # Trend, SavedTrend, Subscription
│   ├── views.py        # Dashboard, Detail, Chatbot
│   ├── urls.py
│   └── management/
│       └── commands/
│           └── seed_trends.py
│
├── core/               # Landing, upgrade, about
│   ├── views.py
│   └── urls.py
│
├── services/           # Business logic layer
│   ├── auth_service.py     # Email verification
│   ├── trend_service.py    # Trend filtering, context
│   └── gemini_service.py   # AI integration
│
├── templates/          # HTML templates
│   ├── base.html
│   ├── accounts/
│   ├── trends/
│   └── core/
│
└── static/
    ├── css/main.css    # Full design system
    └── js/main.js      # Chatbot, save toggle
```

---

## 🔑 Key Features

### Authentication
- Email-based login (not username)
- Custom `CustomUser` model with `is_premium` / `is_verified`
- Strong password validation (uppercase, lowercase, digit, special char)
- Email verification with token-based links
- CSRF protection + secure session cookies

### Trend Intelligence
- 7 platforms tracked: TikTok, Instagram, Twitter/X, YouTube, Reddit, LinkedIn, Threads
- 11 categories: Entertainment, Tech, Sports, Politics, Fashion, Music, Gaming, Food, Business, Science, Other
- Velocity indicators: Exploding 🔥 / Rising 📈 / Steady ➡️ / Declining 📉
- Filter by category, platform, search
- Top 10 sidebar with live scoring

### AI Layer (Gemini)
- **Trend Explanation**: Why is this trend gaining traction?
- **Creator Insights** (Premium): Hashtags, caption format, target audience, engagement strategy
- **Restricted Chatbot**: Keyword extraction → context injection → Gemini response
  - Refuses off-topic questions with a polite message
  - Multi-turn conversation history support

### Premium Gating
- Creator insights blurred for non-premium users
- Upgrade page with pricing
- `is_premium` flag on user model

---

## 🤖 AI Setup (Gemini)

1. Get a free API key at https://ai.google.dev/
2. Add to `.env`: `GEMINI_API_KEY=your-key-here`
3. Install SDK: `pip install google-generativeai`

The platform works in **demo mode** without an API key — mock responses are returned.

---

## 🚢 Production Deployment

### Environment Changes
```python
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
```

### Use PostgreSQL
Uncomment the PostgreSQL config in `settings.py` and set DB env vars.

### Static Files
```bash
python manage.py collectstatic
```

### Gunicorn + Nginx
```bash
gunicorn trendzee.wsgi:application --workers 4 --bind 0.0.0.0:8000
```

### Render/Railway (Quick Deploy)
- Set all environment variables
- Run: `python manage.py migrate && python manage.py seed_trends`
- Start command: `gunicorn trendzee.wsgi:application`

---

## 🏆 Architecture Principles

- **Thin views** — all business logic in `services/`
- **Service layer** — `auth_service`, `trend_service`, `gemini_service`
- **AI governance** — chatbot restricted to trend context only
- **Security first** — PBKDF2 hashing, CSRF, email verification, env vars
- **Scalable structure** — PostgreSQL-ready, Redis-ready, JWT-ready

---

## 📋 Admin Panel

Visit `/admin/` — manage users, trends, subscriptions directly.

To give a user premium access:
1. Go to `/admin/accounts/customuser/`
2. Select user → check `is_premium` → Save

---

Built with Django 4+ | Gemini AI | Bootstrap-free custom CSS
