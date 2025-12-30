# 🛠️ Complete Setup & Deployment Guide

A comprehensive, step-by-step guide to set up the **AI Recruitment Tool** from scratch. This guide assumes you're starting with nothing and walks you through every single step.

**Estimated Time:** 45-60 minutes for complete setup

---

## 📋 Table of Contents

| Section | Description | Time |
|---------|-------------|------|
| [1. Prerequisites](#1-prerequisites) | Tools you need to install | 10 min |
| [2. Get Your API Keys](#2-get-your-api-keys) | Perplexity AI access | 5 min |
| [3. Clone & Local Setup](#3-clone--local-setup) | Get the code running locally | 10 min |
| [4. Database Setup (Neon)](#4-database-setup-neon-postgres) | PostgreSQL for production | 5 min |
| [5. Redis Caching (Optional)](#5-redis-caching-setup-upstash---optional) | Speed up your app | 5 min |
| [6. Deploy to Vercel](#6-deploy-to-vercel) | Put it online | 10 min |
| [7. Google Apps Script](#7-google-apps-script-integration) | Connect Google Forms | 10 min |
| [8. Email Setup (Gmail)](#8-email-setup-gmail-smtp) | Automated notifications | 5 min |
| [9. Test Everything](#9-test-the-complete-flow) | Verify it all works | 5 min |
| [10. Troubleshooting](#10-troubleshooting) | Fix common issues | As needed |

---

# 1. Prerequisites

Before we start, you need to install some tools on your computer.

## 1.1 Install Python 3.11+

**Why:** The backend is written in Python.

### Windows:
1. Go to [python.org/downloads](https://www.python.org/downloads/)
2. Download Python 3.11 or newer
3. **IMPORTANT:** Check ✅ "Add Python to PATH" during installation
4. Click "Install Now"

### Verify Installation:
```powershell
python --version
# Should show: Python 3.11.x or higher
```

## 1.2 Install Git

**Why:** To download and manage the code.

### Windows:
1. Go to [git-scm.com/download/win](https://git-scm.com/download/win)
2. Download the installer
3. Run installer with default settings
4. Restart your terminal/PowerShell

### Verify Installation:
```powershell
git --version
# Should show: git version 2.x.x
```

## 1.3 Create Required Accounts

You'll need accounts on these platforms (all have free tiers):

| Platform | Purpose | Sign Up Link |
|----------|---------|--------------|
| **GitHub** | Host your code | [github.com/signup](https://github.com/signup) |
| **Vercel** | Host your app online | [vercel.com/signup](https://vercel.com/signup) (use GitHub to sign up) |
| **Neon** | PostgreSQL database | [neon.tech](https://neon.tech) (use GitHub to sign up) |
| **Perplexity** | AI for analyzing resumes | [perplexity.ai](https://www.perplexity.ai/) |
| **Upstash** | Redis caching (optional) | [upstash.com](https://upstash.com) |

> 💡 **Tip:** Sign up for Vercel and Neon using your GitHub account - it's faster and easier!

---

# 2. Get Your API Keys

## 2.1 Perplexity AI API Key

This powers the AI analysis of candidates.

1. Go to [perplexity.ai](https://www.perplexity.ai/) and log in
2. Click your profile icon (top right) → **Settings**
3. Click **API** in the left sidebar
4. Click **"Generate"** to create a new API key
5. Copy the key (starts with `pplx-`)

> ⚠️ **Save this key somewhere safe!** You'll need it later.

Example key format: `pplx-a1b2c3d4e5f6g7h8i9j0...`

---

# 3. Clone & Local Setup

## 3.1 Fork the Repository

1. Go to the original repository on GitHub
2. Click the **"Fork"** button (top right)
3. This creates a copy in your GitHub account

## 3.2 Clone to Your Computer

Open PowerShell (Windows) or Terminal (Mac/Linux):

```powershell
# Navigate to where you want the project
cd Desktop

# Clone YOUR forked repository (replace YOUR_USERNAME)
git clone https://github.com/YOUR_USERNAME/AI_JobFormMaker.git

# Enter the project folder
cd AI_JobFormMaker
```

## 3.3 Create Virtual Environment

A virtual environment keeps project dependencies isolated:

```powershell
# Create virtual environment
python -m venv .venv

# Activate it (Windows PowerShell)
.venv\Scripts\activate

# Activate it (Mac/Linux)
# source .venv/bin/activate
```

> ✅ You should see `(.venv)` at the start of your command prompt now.

## 3.4 Install Dependencies

```powershell
pip install -r requirements.txt
```

This installs all required Python packages. Wait for it to complete.

## 3.5 Create Environment File

```powershell
# Windows
copy .env.example .env

# Mac/Linux
# cp .env.example .env
```

## 3.6 Configure Your .env File

Open `.env` in a text editor (VS Code, Notepad++, etc.) and fill in:

```ini
# ====================================
# AI PROVIDER (Required)
# ====================================
AI_PROVIDER=perplexity
PERPLEXITY_API_KEY=pplx-YOUR_KEY_HERE

# ====================================
# FLASK SETTINGS
# ====================================
FLASK_ENV=development
PORT=5000

# ====================================
# NGROK (For local webhook testing)
# Get token from: https://dashboard.ngrok.com/get-started/your-authtoken
# ====================================
NGROK_AUTH_TOKEN=your_ngrok_token_here

# ====================================
# DATABASE (Leave empty for local SQLite)
# We'll add this after setting up Neon
# ====================================
# DATABASE_URL=

# ====================================
# REDIS CACHING (Optional)
# We'll add this after setting up Upstash
# ====================================
# UPSTASH_REDIS_REST_URL=
# UPSTASH_REDIS_REST_TOKEN=

# ====================================
# GOOGLE APPS SCRIPT
# We'll add this after setting up the script
# ====================================
# GOOGLE_SCRIPT_URL=

# ====================================
# EMAIL (Optional - for notifications)
# We'll configure this in Step 8
# ====================================
# SMTP_SERVER=smtp.gmail.com
# SMTP_PORT=587
# SENDER_EMAIL=
# SENDER_PASSWORD=
# SENDER_NAME=Recruitment Team
# ADMIN_EMAIL=
```

## 3.7 Run Locally (First Test)

```powershell
python app.py
```

You should see:
```
 * Running on http://127.0.0.1:5000
```

Open your browser and go to: **http://localhost:5000**

🎉 **If you see the dashboard, congratulations! The app is running locally.**

Press `Ctrl+C` to stop the server.

---

# 4. Database Setup (Neon Postgres)

**Why Neon?** When you deploy to Vercel, files don't persist between requests. We need a real database.

## 4.1 Create Neon Account

1. Go to [console.neon.tech](https://console.neon.tech/)
2. Click **"Sign in with GitHub"** (easiest)
3. Authorize the connection

## 4.2 Create a New Project

1. Click **"New Project"** button
2. Fill in:
   - **Project name:** `recruitment-db`
   - **Postgres version:** Leave default (16)
   - **Region:** Choose closest to you (e.g., `Singapore` for Asia)
3. Click **"Create Project"**

## 4.3 Get Your Connection String

After project creation:

1. You'll see the **Connection Details** panel
2. **IMPORTANT:** Click the dropdown and select **"Pooled connection"**
   - This is required for serverless deployments like Vercel!
3. Copy the connection string

It looks like this:
```
postgresql://username:password@ep-xxx-yyy-12345.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

## 4.4 Add to Your .env File

Open your `.env` file and add:

```ini
# DATABASE
DATABASE_URL=postgresql://username:password@ep-xxx-yyy-12345.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

## 4.5 Test Database Connection

```powershell
python app.py
```

Check the console output. You should see:
```
Using PostgreSQL database
```

Visit `http://localhost:5000/api/health` - it should show:
```json
{
  "database": "postgresql",
  "status": "healthy"
}
```

---

# 5. Redis Caching Setup (Upstash) - OPTIONAL

> ⚠️ **This step is completely optional!** 
> 
> Skip this if:
> - You're just testing
> - You want to set it up later
> - You don't need faster performance
>
> The app works perfectly without Redis (uses in-memory caching).

## 5.1 Why Redis?

| Without Redis | With Redis |
|---------------|------------|
| Pages load in ~200ms | Pages load in ~20ms |
| Cache resets on each request | Cache persists |
| Good for development | Recommended for production |

## 5.2 Create Upstash Account

1. Go to [console.upstash.com](https://console.upstash.com/)
2. Click **"Sign Up"** → Use GitHub/Google
3. You're in!

## 5.3 Create Redis Database

1. Click **"Create Database"**
2. Fill in:
   - **Name:** `recruitment-cache`
   - **Type:** `Regional` (free tier)
   - **Region:** Same as your Neon database (e.g., `ap-southeast-1`)
3. Click **"Create"**

## 5.4 Get Your Credentials

On the database page:

1. Scroll down to **"REST API"** section
2. You'll see two values:
   - `UPSTASH_REDIS_REST_URL` - Copy this
   - `UPSTASH_REDIS_REST_TOKEN` - Click "Show" then copy

## 5.5 Add to Your .env File

```ini
# REDIS CACHING (OPTIONAL)
UPSTASH_REDIS_REST_URL=https://casual-duck-12345.upstash.io
UPSTASH_REDIS_REST_TOKEN=AUTFAAxxxxxxxxxxxxxxxx
```

## 5.6 Install Redis Package

```powershell
pip install upstash-redis
```

## 5.7 Test Redis Connection

```powershell
python app.py
```

Check console for:
```
✅ Upstash Redis connected successfully
```

Visit `http://localhost:5000/api/health`:
```json
{
  "cache": "redis",
  "status": "healthy"
}
```

---

# 6. Deploy to Vercel

Now let's put your app online!

## 6.1 Push Code to GitHub

First, commit any changes:

```powershell
git add .
git commit -m "Ready for Vercel deployment"
git push origin main
```

## 6.2 Import Project to Vercel

1. Go to [vercel.com/dashboard](https://vercel.com/dashboard)
2. Click **"Add New..."** → **"Project"**
3. Find your repository (`AI_JobFormMaker`) and click **"Import"**

## 6.3 Configure Project Settings

On the configuration page:

1. **Framework Preset:** Select **"Other"**
2. **Root Directory:** Leave as `.` (default)
3. **Build Command:** Leave empty
4. **Output Directory:** Leave empty

**DON'T CLICK DEPLOY YET!** We need to add environment variables first.

## 6.4 Add Environment Variables

Scroll down to **"Environment Variables"** and add each one:

| Name | Value | Required? |
|------|-------|-----------|
| `AI_PROVIDER` | `perplexity` | ✅ Yes |
| `PERPLEXITY_API_KEY` | `pplx-your-key-here` | ✅ Yes |
| `DATABASE_URL` | `postgresql://...` (your Neon URL) | ✅ Yes |
| `UPSTASH_REDIS_REST_URL` | `https://xxx.upstash.io` | ❌ Optional |
| `UPSTASH_REDIS_REST_TOKEN` | `AUTFxxx...` | ❌ Optional |
| `GOOGLE_SCRIPT_URL` | (We'll add this in Step 7) | ⏳ Later |
| `SMTP_SERVER` | `smtp.gmail.com` | ❌ Optional |
| `SMTP_PORT` | `587` | ❌ Optional |
| `SENDER_EMAIL` | `your@gmail.com` | ❌ Optional |
| `SENDER_PASSWORD` | `app-password` | ❌ Optional |
| `SENDER_NAME` | `Recruitment Team` | ❌ Optional |

## 6.5 Deploy

1. Click **"Deploy"**
2. Wait 1-2 minutes for build to complete
3. You'll get a URL like: `https://ai-job-form-maker.vercel.app`

## 6.6 Verify Deployment

Visit your new URL:
- `https://YOUR-APP.vercel.app/` - Should show dashboard
- `https://YOUR-APP.vercel.app/api/health` - Should show healthy status

🎉 **Your app is now live on the internet!**

---

# 7. Google Apps Script Integration

This connects Google Forms to your application. When candidates submit forms, their data automatically flows to your app.

## 7.1 Understanding the Flow

```
┌─────────────────┐      ┌──────────────────┐      ┌─────────────────┐
│  Your Vercel    │─────►│  Google Apps     │─────►│  Google Form    │
│  App            │      │  Script          │      │  (Created)      │
└─────────────────┘      └──────────────────┘      └─────────────────┘
        ▲                                                   │
        │                                                   │
        │         ┌──────────────────────┐                  │
        └─────────│  Candidate submits   │◄─────────────────┘
                  │  form → Webhook      │
                  └──────────────────────┘
```

**Two Important URLs:**
1. **GOOGLE_SCRIPT_URL** - Your app calls this to CREATE forms
2. **WEBHOOK_URL** - Form submissions go TO your app

## 7.2 Create the Google Apps Script

1. Go to [script.google.com](https://script.google.com/)
2. Click **"New Project"**
3. Click on "Untitled project" at the top and rename it to `Recruitment Form Creator`

## 7.3 Add the Script Code

1. Delete all existing code in the editor
2. Open the file `final_google_script.js` from your project folder
3. Copy the ENTIRE contents
4. Paste into the Google Apps Script editor

## 7.4 Configure the Webhook URL

Find this line near the top of the script (around line 5):

```javascript
var WEBHOOK_URL = "https://YOUR_VERCEL_APP_URL/api/webhook/application";
```

Replace with YOUR actual Vercel URL:

```javascript
var WEBHOOK_URL = "https://ai-job-form-maker.vercel.app/api/webhook/application";
```

> ⚠️ Make sure to include `/api/webhook/application` at the end!

## 7.5 Save the Script

Press `Ctrl+S` or click the floppy disk icon to save.

## 7.6 Deploy as Web App

1. Click **"Deploy"** button (top right)
2. Click **"New deployment"**
3. Click the gear icon ⚙️ next to "Select type"
4. Choose **"Web app"**

Configure the deployment:
- **Description:** `Initial deployment`
- **Execute as:** `Me (your-email@gmail.com)`
- **Who has access:** **Anyone** ⚠️ (This is important!)

5. Click **"Deploy"**

## 7.7 Authorize Permissions

A popup will ask for permissions:

1. Click **"Authorize access"**
2. Choose your Google account
3. You'll see a warning: "Google hasn't verified this app"
4. Click **"Advanced"** (bottom left)
5. Click **"Go to Recruitment Form Creator (unsafe)"**
6. Click **"Allow"**

## 7.8 Copy the Web App URL

After authorization, you'll see:
- **Web app URL:** `https://script.google.com/macros/s/AKfycbx.../exec`

**Copy this URL!** This is your `GOOGLE_SCRIPT_URL`.

## 7.9 Add to Vercel Environment Variables

1. Go to [Vercel Dashboard](https://vercel.com/dashboard)
2. Click on your project
3. Go to **Settings** → **Environment Variables**
4. Add new variable:
   - **Name:** `GOOGLE_SCRIPT_URL`
   - **Value:** `https://script.google.com/macros/s/AKfycbx.../exec`
5. Click **Save**

## 7.10 Redeploy Vercel

After adding the environment variable:

1. Go to **Deployments** tab
2. Click the three dots `...` on the latest deployment
3. Click **"Redeploy"**
4. Confirm

## 7.11 Set Up Form Trigger (Important!)

Back in Google Apps Script:

1. Click on the function dropdown (says `onFormSubmit` or similar)
2. Select **`setupTrigger`**
3. Click the **Run** button (▶️)
4. Authorize if prompted again

This sets up automatic form submission handling.

---

# 8. Email Setup (Gmail SMTP)

Enable automated emails to candidates (confirmations, rejections, interview invites).

## 8.1 Enable 2-Step Verification

Gmail requires this for app passwords:

1. Go to [myaccount.google.com/security](https://myaccount.google.com/security)
2. Under "Signing in to Google", click **"2-Step Verification"**
3. Follow the steps to enable it

## 8.2 Create an App Password

1. Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
2. You may need to sign in again
3. Under "Select app", choose **"Mail"**
4. Under "Select device", choose **"Other (Custom name)"**
5. Enter: `Recruitment App`
6. Click **"Generate"**

You'll see a 16-character password like: `abcd efgh ijkl mnop`

**Copy this password** (ignore the spaces).

## 8.3 Add to Vercel Environment Variables

Go to Vercel → Your Project → Settings → Environment Variables:

| Name | Value |
|------|-------|
| `SMTP_SERVER` | `smtp.gmail.com` |
| `SMTP_PORT` | `587` |
| `SENDER_EMAIL` | `your-email@gmail.com` |
| `SENDER_PASSWORD` | `abcdefghijklmnop` (no spaces) |
| `SENDER_NAME` | `Recruitment Team` |
| `ADMIN_EMAIL` | `your-email@gmail.com` |

## 8.4 Redeploy

Redeploy your Vercel app for changes to take effect.

---

# 9. Test the Complete Flow

Let's verify everything works end-to-end!

## 9.1 Test Job Creation

1. Go to your Vercel app URL
2. Click **"Create New Job"** (or **"+"** button)
3. Fill in:
   - **Job Title:** `Test Software Engineer`
   - **Job Description:** Paste any job description
4. Click **"Generate Questions"**
5. Wait for AI to generate questions
6. Click **"Create Application Form"**

✅ **Success:** You should get a Google Form URL

## 9.2 Test Form Submission

1. Open the Google Form URL in a new tab/incognito window
2. Fill out the application:
   - Name: `Test Candidate`
   - Email: `test@example.com`
   - Phone: `1234567890`
   - Upload a test resume (any PDF)
   - Answer the questions
3. Submit the form

## 9.3 Verify Candidate Appears

1. Go back to your dashboard
2. Click on the job you created
3. Click **"Refresh Candidates"** button
4. The test candidate should appear!

✅ **If you see the candidate with a score, everything is working!**

## 9.4 Test Email (Optional)

If you set up email:
1. Check the candidate's email (or your admin email)
2. You should receive a confirmation email

---

# 10. Troubleshooting

## Database Issues

| Problem | Solution |
|---------|----------|
| "Connection refused" | Make sure you're using **Pooled connection** from Neon |
| "SSL required" error | Add `?sslmode=require` to your DATABASE_URL |
| Tables not created | The app auto-creates tables on first run. Restart the app. |

## Google Form Issues

| Problem | Solution |
|---------|----------|
| Form not created | Check GOOGLE_SCRIPT_URL is correct in Vercel |
| Webhook not working | Make sure WEBHOOK_URL in Google Script points to YOUR Vercel app |
| "Permission denied" | Re-run authorization in Google Apps Script |
| Submissions not appearing | Run `setupTrigger` function in Apps Script |

## Candidate Not Appearing

| Problem | Solution |
|---------|----------|
| Candidate stuck as "pending" | AI processing may take 10-30 seconds. Refresh the page. |
| Score is 0 | Check your PERPLEXITY_API_KEY is valid |
| Resume shows "Not Found" | Check Google Drive sharing permissions |

## Email Issues

| Problem | Solution |
|---------|----------|
| "Authentication failed" | Use App Password, NOT your regular Gmail password |
| "Less secure apps" error | Enable 2FA and use App Password instead |
| Email not received | Check spam folder |

## Vercel Deployment Issues

| Problem | Solution |
|---------|----------|
| Build failed | Check Vercel logs for specific error |
| 500 Internal Error | Check Vercel Function Logs for details |
| Environment variable not working | Redeploy after adding variables |

## Check Logs

**Vercel Logs:**
1. Go to Vercel Dashboard → Your Project
2. Click **"Logs"** tab
3. Filter by "Functions" to see API errors

**Google Apps Script Logs:**
1. In Apps Script, click **"Executions"** (left sidebar)
2. View recent execution logs

---

# 📋 Quick Reference

## Environment Variables Summary

```ini
# Required
AI_PROVIDER=perplexity
PERPLEXITY_API_KEY=pplx-xxx...
DATABASE_URL=postgresql://...

# Optional - Caching
UPSTASH_REDIS_REST_URL=https://xxx.upstash.io
UPSTASH_REDIS_REST_TOKEN=AUTFxxx...

# Optional - Google Forms
GOOGLE_SCRIPT_URL=https://script.google.com/macros/s/xxx/exec

# Optional - Email
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your@gmail.com
SENDER_PASSWORD=app-password
SENDER_NAME=Recruitment Team
ADMIN_EMAIL=your@gmail.com
```

## Key URLs

| URL | Purpose |
|-----|---------|
| `https://YOUR-APP.vercel.app/` | Main Dashboard |
| `https://YOUR-APP.vercel.app/api/health` | Check app status |
| `https://YOUR-APP.vercel.app/api/webhook/application` | Webhook endpoint |

## Local Development Commands

```powershell
# Activate virtual environment
.venv\Scripts\activate

# Run app (with ngrok for webhooks)
python app.py

# Run app (without ngrok)
python app.py --no-ngrok

# Install new package
pip install package-name

# Update requirements
pip freeze > requirements.txt
```

---

# 📁 Project Structure

```
AI_JobFormMaker/
├── app.py                    # Main Flask application (1600+ lines)
├── requirements.txt          # Python dependencies
├── vercel.json              # Vercel serverless config
├── runtime.txt              # Python version for Vercel
├── .env                     # Your local environment variables (DO NOT COMMIT!)
├── .env.example             # Template for environment variables
├── final_google_script.js   # Copy this to Google Apps Script
│
├── services/
│   ├── ai_service.py        # AI analysis (Perplexity/OpenAI/Claude)
│   ├── cache_service.py     # Redis/memory caching
│   ├── candidate_scorer.py  # 9-dimension scoring algorithm
│   ├── email_service.py     # Background email queue
│   ├── file_processor.py    # Resume text extraction
│   ├── resume_parser.py     # Parse resume content
│   └── storage_service.py   # Database operations (SQLite/PostgreSQL)
│
├── static/
│   ├── css/
│   │   ├── style.css        # Main styles
│   │   ├── kanban.css       # Kanban board styles
│   │   └── gas-styles.css   # Additional styles
│   └── js/
│       ├── app.js           # Main frontend JavaScript
│       └── job_details.js   # Job details page logic
│
├── templates/
│   ├── dashboard.html       # Main dashboard
│   ├── index.html           # Job creation page
│   ├── job_details.html     # View candidates for a job
│   ├── ranking.html         # Candidate ranking page
│   └── analytics.html       # Analytics dashboard
│
└── data/                    # Local SQLite database (auto-created)
    └── recruitment.db
```

---

# 🎉 You're Done!

Congratulations! You now have a fully functional AI-powered recruitment tool:

✅ **Dashboard** - View all your jobs at a glance  
✅ **AI Question Generation** - Automatically create interview questions  
✅ **Google Forms Integration** - Candidates apply through forms  
✅ **Automatic Scoring** - AI analyzes and ranks candidates  
✅ **Kanban Board** - Track candidates through hiring stages  
✅ **Email Notifications** - Automated candidate communications  
✅ **Redis Caching** - Lightning-fast performance  

---

**Need Help?**
- Check the [Troubleshooting](#10-troubleshooting) section
- Review Vercel logs for errors
- Open an issue on GitHub

**Happy Recruiting! 🚀**
