# 🛠️ Complete Setup & Deployment Guide

This guide covers the end-to-end process of setting up the **AI Recruitment Tool** for both **local development** and **production deployment** on Vercel with Neon PostgreSQL.

---

## 📋 Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Local Development Setup](#2-local-development-setup)
3. [Database Setup (Neon Postgres)](#3-database-setup-neon-postgres)
4. [Redis Caching Setup (Upstash)](#4-redis-caching-setup-upstash)
5. [Deployment to Vercel](#5-deployment-to-vercel)
6. [Google Apps Script Integration](#6-google-apps-script-integration)
7. [Email Setup (Gmail SMTP)](#7-email-setup-gmail-smtp)
8. [Testing the Full Flow](#8-testing-the-full-flow)
9. [Troubleshooting](#9-troubleshooting)

---

## 1. Prerequisites

Before starting, ensure you have:

| Requirement | Purpose | Get It |
|-------------|---------|--------|
| **Python 3.11+** | Run the application | [python.org](https://python.org) |
| **Git** | Version control | [git-scm.com](https://git-scm.com) |
| **GitHub Account** | Host your code | [github.com](https://github.com) |
| **Vercel Account** | Host the application | [vercel.com](https://vercel.com) |
| **Neon Account** | PostgreSQL database | [neon.tech](https://neon.tech) |
| **Upstash Account** | Redis caching (optional) | [upstash.com](https://upstash.com) |
| **Google Account** | Forms & Sheets | [google.com](https://google.com) |
| **Perplexity API Key** | AI analysis | [perplexity.ai/settings/api](https://www.perplexity.ai/settings/api) |

---

## 2. Local Development Setup

### Step 1: Clone and Setup Environment

```powershell
# Clone the repository
git clone https://github.com/YOUR_USERNAME/AI_JobFormMaker.git
cd AI_JobFormMaker

# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Mac/Linux)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Step 2: Configure Environment Variables

```powershell
# Copy the example file
copy .env.example .env
```

Edit `.env` with your values:

```ini
# AI Provider
AI_PROVIDER=perplexity
PERPLEXITY_API_KEY=pplx-your-actual-key

# Google Apps Script URL (get this in Step 5)
GOOGLE_SCRIPT_URL=https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec

# Ngrok for local webhooks (get from https://dashboard.ngrok.com)
NGROK_AUTH_TOKEN=your_ngrok_authtoken

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_app_password
SENDER_NAME=Recruitment Team
```

### Step 3: Run Locally

```powershell
# Start with Ngrok tunnel (for Google Form webhooks)
python app.py

# Start without Ngrok (no webhooks)
python app.py --no-ngrok
```

Access the app at: **http://localhost:5000**

> **Note**: Local development uses **SQLite** automatically. No database setup needed!

---

## 3. Database Setup (Neon Postgres)

Vercel's serverless functions have ephemeral storage - files disappear after requests. We use Neon PostgreSQL for persistent data in production.

### Step 1: Create Neon Project

1. Go to [Neon Console](https://console.neon.tech/)
2. Click **"New Project"**
3. Name: `recruitment-db`
4. Region: Choose closest to your users

### Step 2: Get Connection String

1. On Dashboard, find **"Connection Details"**
2. Select **"Pooled connection"** (IMPORTANT for serverless!)
3. Copy the connection string

```
postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
```

### Step 3: Test Locally (Optional)

To test PostgreSQL locally before deploying:

```ini
# In .env
DATABASE_URL=postgresql://user:password@ep-xxx.us-east-2.aws.neon.tech/neondb?sslmode=require
FORCE_POSTGRES=1
```

Run the app - it will now use your Neon database.

---

## 4. Redis Caching Setup (Upstash) - OPTIONAL

> ⚠️ **This step is completely optional!** Your app works perfectly without Redis.
> 
> **Without Redis:** Uses in-memory caching (works great for development and small deployments)
> 
> **With Redis:** Faster responses, cache persists across serverless function restarts (recommended for production)

Upstash provides **free serverless Redis** that works perfectly with Vercel. This makes your API responses 10-50x faster.

### Skip This Section If:
- You're just testing locally
- You don't need persistent caching
- You want to set it up later

The app automatically falls back to in-memory caching if Redis is not configured.

---

### Step 1: Create Upstash Account

1. Go to [Upstash Console](https://console.upstash.com/)
2. Sign up with GitHub/Google (free tier = 10,000 commands/day)

### Step 2: Create a Redis Database

1. Click **"Create Database"**
2. Name: `recruitment-cache`
3. Region: Choose closest to your Vercel deployment (e.g., `ap-southeast-1` for Singapore)
4. Type: **Regional** (free tier)

### Step 3: Get Credentials

1. On the database page, scroll to **"REST API"** section
2. Copy these two values:
   - `UPSTASH_REDIS_REST_URL`
   - `UPSTASH_REDIS_REST_TOKEN`

### Step 4: Add to Environment

**For Local Development** (`.env`):
```ini
# Upstash Redis (OPTIONAL - for caching)
UPSTASH_REDIS_REST_URL=https://your-database.upstash.io
UPSTASH_REDIS_REST_TOKEN=AXxxxx...
```

**For Vercel**: Add these in Dashboard → Settings → Environment Variables

### What Gets Cached?

| Data | TTL | Benefit |
|------|-----|---------|
| Job listings | 5 min | Fast dashboard loads |
| Candidate lists | 1 min | Snappy candidate views |
| Analytics data | 5 min | Instant charts |
| AI scores | 24 hrs | Never re-calculate |

### Verify Caching

Check `/api/health` endpoint:
```json
{
  "cache": "redis",  // Shows "memory" if Redis not configured
  "status": "healthy"
}
```

---

## 5. Deployment to Vercel

### Step 1: Push to GitHub

```powershell
git add .
git commit -m "Ready for Vercel deployment"
git push origin main
```

### Step 2: Import to Vercel

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click **"Add New..."** → **"Project"**
3. Import your GitHub repository
4. **Framework Preset**: Select **"Other"**
5. Leave Build/Output settings as default

### Step 3: Configure Environment Variables

Add these in Vercel Dashboard → Project → Settings → Environment Variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `AI_PROVIDER` | `perplexity` | or `openai`, `claude` |
| `PERPLEXITY_API_KEY` | `pplx-xxx...` | Your API key |
| `DATABASE_URL` | `postgresql://...` | Neon **Pooled** connection string |
| `UPSTASH_REDIS_REST_URL` | `https://xxx.upstash.io` | Optional - for caching |
| `UPSTASH_REDIS_REST_TOKEN` | `AXxxx...` | Optional - for caching |
| `GOOGLE_SCRIPT_URL` | `https://script.google.com/...` | From Step 6 |
| `SMTP_SERVER` | `smtp.gmail.com` | Optional - for emails |
| `SMTP_PORT` | `587` | Optional |
| `SENDER_EMAIL` | `your@gmail.com` | Optional |
| `SENDER_PASSWORD` | `app-password` | Optional - See Step 7 |
| `SENDER_NAME` | `Recruitment Team` | Optional |

### Step 4: Deploy

1. Click **"Deploy"**
2. Wait for build to complete
3. Get your URL: `https://your-app.vercel.app`

### Step 5: Verify Deployment

Visit these endpoints:
- `https://your-app.vercel.app/` - Dashboard
- `https://your-app.vercel.app/api/health` - Should show `"database": "postgresql"` and `"cache": "redis"`

---

## 6. Google Apps Script Integration

This connects Google Forms to your application for automatic candidate processing.

### ⚠️ Understanding the Two URLs

There are **TWO different URLs** that work together:

| URL | Where to Set | Example | Purpose |
|-----|--------------|---------|---------|
| **GOOGLE_SCRIPT_URL** | Vercel Environment Variables | `https://script.google.com/macros/s/xxx/exec` | Your app calls this to CREATE forms |
| **WEBHOOK_URL** | Inside Google Apps Script | `https://your-app.vercel.app/api/webhook/application` | Form submissions go HERE |

**Flow Diagram:**
```
Your Vercel App ──(GOOGLE_SCRIPT_URL)──► Google Apps Script ──► Creates Form
                                                                    │
Candidate fills form ──► Form Submit ──(WEBHOOK_URL)──► Your Vercel App ──► Scores candidate
```

---

### Step 1: Create Google Apps Script

1. Go to [Google Apps Script](https://script.google.com/)
2. Click **"New Project"**
3. Delete any existing code
4. Copy the entire content of `final_google_script.js` from this repo
5. Paste into the script editor

### Step 2: Configure WEBHOOK_URL (in Google Script)

Find this line near the top of the script:
```javascript
var WEBHOOK_URL = "https://YOUR_VERCEL_APP_URL/api/webhook/application";
```

Replace with your **actual Vercel app URL**:
```javascript
var WEBHOOK_URL = "https://recruitment-tool-ar1.vercel.app/api/webhook/application";
```

> ⚠️ This URL points TO your Vercel app. When candidates submit the form, data goes here.

### Step 3: Deploy as Web App

1. Click **"Deploy"** → **"New deployment"**
2. **Type**: Web app
3. **Execute as**: Me
4. **Who has access**: **Anyone** (Important!)
5. Click **"Deploy"**
6. **Copy the Web App URL** - This is your `GOOGLE_SCRIPT_URL`

> 📋 The URL looks like: `https://script.google.com/macros/s/AKfycbx.../exec`

### Step 4: Authorize Permissions

1. Click **"Authorize access"**
2. Select your Google account
3. Click **"Advanced"** → **"Go to (project name) (unsafe)"**
4. Click **"Allow"**

### Step 5: Add GOOGLE_SCRIPT_URL to Vercel

Go to Vercel Dashboard → Project → Settings → Environment Variables:

| Variable | Value |
|----------|-------|
| `GOOGLE_SCRIPT_URL` | `https://script.google.com/macros/s/YOUR_SCRIPT_ID/exec` |

> ⚠️ This URL points FROM your Vercel app TO Google. It's used to create forms.

### Step 6: Redeploy After Changes

If you update the Google Apps Script code:
1. Click **Deploy** → **Manage deployments**
2. Click the **pencil icon** (edit)
3. Change version to **"New version"**
4. Click **Deploy**

---

## 6. Email Setup (Gmail SMTP)

Optional: Enable automated emails for candidate notifications.

### Step 1: Enable 2-Step Verification

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification**

### Step 2: Create App Password

1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Select app: **Mail**
3. Select device: **Other** → Name it "Recruitment App"
4. Click **Generate**
5. Copy the 16-character password (e.g., `abcd efgh ijkl mnop`)

### Step 3: Configure in App

```ini
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=abcdefghijklmnop  # No spaces
SENDER_NAME=Recruitment Team
```

---

## 7. Testing the Full Flow

### Test 1: Create a Job

1. Go to your app's dashboard
2. Click **"Create New Job"**
3. Enter job title and description
4. Click **"Generate Questions"**
5. Click **"Create Application Form"**
6. Copy the Google Form URL

### Test 2: Submit an Application

1. Open the Google Form URL
2. Fill in candidate details
3. Upload a test resume
4. Submit the form

### Test 3: Verify in Dashboard

1. Go to your app's dashboard
2. Click on the job
3. Switch to **Kanban View**
4. The candidate should appear in the **"Applied"** column

---

## 8. Troubleshooting

### Database Issues

| Problem | Solution |
|---------|----------|
| "Connection refused" | Check DATABASE_URL uses **Pooled** connection |
| "SSL required" | Ensure `?sslmode=require` in connection string |
| "Table not found" | Restart app to auto-create tables |

### Google Form Issues

| Problem | Solution |
|---------|----------|
| "Webhook not triggered" | Run `setupTrigger` function in Apps Script |
| "Permission denied" | Re-authorize the script |
| "500 error" | Check Vercel logs for details |

### Candidate Not Appearing

| Problem | Solution |
|---------|----------|
| Shows in List but not Kanban | Fixed! Status mapping now handles `processed` |
| Resume "Not Found" | Google Drive sharing permissions issue |
| Score is 0 | Check AI API key is valid |

### Email Not Sending

| Problem | Solution |
|---------|----------|
| "Authentication failed" | Use App Password, not regular password |
| "SMTP error" | Ensure 2FA is enabled on Gmail |
| No errors but no email | Check spam folder |

---

## 🚀 Quick Reference

### Local Development
```powershell
# Activate environment
.venv\Scripts\activate

# Start with webhooks
python app.py

# Start without webhooks
python app.py --no-ngrok
```

### Environment Summary

| Environment | Database | Webhooks | URL |
|-------------|----------|----------|-----|
| **Local** | SQLite | Ngrok tunnel | `http://localhost:5000` |
| **Vercel** | Neon PostgreSQL | Direct | `https://your-app.vercel.app` |

### Key URLs (Production)

- **Dashboard**: `https://your-app.vercel.app/`
- **Health Check**: `https://your-app.vercel.app/api/health`
- **Webhook**: `https://your-app.vercel.app/api/webhook/application`

---

## 📁 Project Structure

```
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── vercel.json           # Vercel configuration
├── runtime.txt           # Python version for Vercel
├── .env.example          # Environment template
├── final_google_script.js # Google Apps Script code
├── services/
│   ├── ai_service.py     # AI analysis (Perplexity/OpenAI/Claude)
│   ├── cache_service.py  # Redis/memory caching (Upstash)
│   ├── candidate_scorer.py # Scoring algorithm
│   ├── storage_service.py  # Database (SQLite/PostgreSQL)
│   ├── email_service.py   # Background email queue
│   └── file_processor.py  # Resume parsing
├── static/
│   ├── css/              # Stylesheets
│   └── js/               # Frontend JavaScript
└── templates/            # HTML templates
```

---

**Need help?** Check the Vercel logs or open an issue on GitHub.
