# 🚀 AI Recruitment & Interview Tool

**Transform Job Descriptions into Professional Interview Questions & Automate Candidate Scoring.**

![Project Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.11+-blue)
![Flask](https://img.shields.io/badge/Framework-Flask-green)
![Vercel](https://img.shields.io/badge/Deployment-Vercel-black)
![Neon](https://img.shields.io/badge/Database-Neon%20Postgres-orange)

## 🌟 Overview

This tool streamlines the recruitment process by leveraging AI to:
1.  **Generate Interview Questions**: Analyze job descriptions and create tailored technical, behavioral, and situational questions.
2.  **Automate Applications**: Create Google Forms automatically that sync responses to your dashboard.
3.  **Score Candidates**: AI analyzes resumes against the job description, providing a match score (0-100%) with detailed breakdown.
4.  **Kanban Board**: Track candidates through stages (Applied → Interview → Rejected) with drag-and-drop.

---

## ⚡ Features

### Core Features
*   **☁️ Dual Deployment**: Run locally (SQLite) or deploy to Vercel (Neon PostgreSQL)
*   **🤖 Multi-AI Support**: Perplexity (default), OpenAI GPT-4, or Claude 3.5
*   **📊 Intelligent Scoring**: 9-dimension analysis with red flag detection
*   **📧 Background Emails**: Non-blocking email queue with threading
*   **🔗 LinkedIn Integration**: Detect LinkedIn profiles and apply scoring penalty if missing
*   **⚡ Redis Caching**: Upstash Redis for blazing-fast API responses
*   **📋 Bulk Operations**: Select multiple candidates for bulk reject/delete
*   **📄 Resume Preview**: View resumes in-app without downloading

### Scoring System (v2.0)
*   **Skills Match** (20%): Technical skills alignment
*   **Job Relevance** (25%): Overall fit for the role
*   **Technical Depth** (15%): Expertise level assessment
*   **Project Complexity** (10%): Quality of past projects
*   **Experience** (10%): Years and relevance
*   **Communication** (5%): Writing quality in answers
*   **Culture Fit** (5%): Team compatibility signals
*   **Education** (5%): Academic background
*   **Keywords** (5%): Job-specific terminology

### Penalties & Bonuses
*   **-2 points**: Missing LinkedIn profile
*   **-5 points per red flag**: Employment gaps, job hopping, etc.
*   **-12 points**: AI-generated answers detected
*   **+8 points**: Unicorn candidate (perfect match)
*   **+5 points**: Strong leadership indicators

---

## 🚀 Quick Start

### Local Development

```powershell
# Clone and setup
git clone https://github.com/YOUR_USERNAME/AI_JobFormMaker.git
cd AI_JobFormMaker
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt

# Configure
copy .env.example .env
# Edit .env with your API keys

# Run
python app.py
```

Access at: **http://localhost:5000**

### Production Deployment

See **[SETUP_GUIDE.md](SETUP_GUIDE.md)** for complete instructions on:
- Neon PostgreSQL setup
- Vercel deployment
- Google Apps Script integration
- Email configuration

---

## 🧩 Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11, Flask |
| **Frontend** | HTML5, CSS3 (Glassmorphism), JavaScript |
| **Database** | SQLite (local) / PostgreSQL (production) |
| **Caching** | Upstash Redis (serverless) / In-memory fallback |
| **AI** | Perplexity AI, OpenAI, Claude |
| **Hosting** | Vercel (serverless) |
| **Integration** | Google Apps Script |

---

## 📂 Project Structure

```
├── app.py                  # Main Flask application
├── requirements.txt        # Python dependencies
├── vercel.json            # Vercel configuration
├── .env.example           # Environment template
├── final_google_script.js  # Google Forms integration
├── services/
│   ├── ai_service.py      # AI analysis
│   ├── cache_service.py   # Redis/memory caching
│   ├── candidate_scorer.py # Scoring algorithm
│   ├── storage_service.py  # Database (SQLite/PostgreSQL)
│   ├── email_service.py   # Background email queue
│   └── file_processor.py  # Resume parsing
├── static/
│   ├── css/               # Stylesheets
│   └── js/                # Frontend JavaScript
└── templates/             # HTML templates
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
