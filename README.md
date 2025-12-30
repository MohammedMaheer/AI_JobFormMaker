<p align="center">
  <img src="https://acceleration-robotics.com/wp-content/uploads/2023/03/logo-acceleration-robotics.svg" alt="Acceleration Robotics Logo" width="300"/>
</p>

<h1 align="center">🤖 AI-Powered Recruitment Platform</h1>

<p align="center">
  <strong>Intelligent Talent Acquisition for Acceleration Robotics</strong>
</p>

<p align="center">
  <em>Streamline your hiring process with AI-driven candidate scoring, automated interview questions, and seamless Google Forms integration.</em>
</p>

<p align="center">
  <a href="#features">Features</a> •
  <a href="#demo">Demo</a> •
  <a href="#quick-start">Quick Start</a> •
  <a href="#architecture">Architecture</a> •
  <a href="#documentation">Documentation</a>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.11+-3776AB?style=for-the-badge&logo=python&logoColor=white" alt="Python"/>
  <img src="https://img.shields.io/badge/Flask-3.0-000000?style=for-the-badge&logo=flask&logoColor=white" alt="Flask"/>
  <img src="https://img.shields.io/badge/Vercel-Deployed-000000?style=for-the-badge&logo=vercel&logoColor=white" alt="Vercel"/>
  <img src="https://img.shields.io/badge/PostgreSQL-Neon-4169E1?style=for-the-badge&logo=postgresql&logoColor=white" alt="PostgreSQL"/>
  <img src="https://img.shields.io/badge/Redis-Upstash-DC382D?style=for-the-badge&logo=redis&logoColor=white" alt="Redis"/>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Status-Production%20Ready-success?style=flat-square" alt="Status"/>
  <img src="https://img.shields.io/badge/License-MIT-blue?style=flat-square" alt="License"/>
  <img src="https://img.shields.io/badge/PRs-Welcome-brightgreen?style=flat-square" alt="PRs Welcome"/>
</p>

---

## 🎯 About

**Acceleration Robotics** is revolutionizing the robotics industry with cutting-edge hardware acceleration solutions. To build world-class products, we need world-class talent. This AI-powered recruitment platform helps us identify and hire the best candidates efficiently.

### The Challenge

Traditional recruitment is:
- ⏰ **Time-consuming** - Manual resume screening takes hours
- 🎲 **Inconsistent** - Human bias affects candidate evaluation
- 📊 **Unstructured** - No standardized scoring across candidates
- 🔄 **Disconnected** - Forms, emails, and tracking in separate tools

### Our Solution

An end-to-end recruitment automation platform that:
- 🤖 **AI-Powered Scoring** - Objective 9-dimension candidate analysis
- ⚡ **Instant Processing** - Candidates scored in seconds, not days
- 📋 **One Dashboard** - Applications, scoring, and tracking unified
- 🔗 **Seamless Integration** - Google Forms auto-sync with webhooks

---

## ✨ Features

<table>
<tr>
<td width="50%">

### 🧠 AI Intelligence
- **Smart Question Generation** - AI creates role-specific interview questions from job descriptions
- **Resume Analysis** - Deep parsing of skills, experience, and qualifications
- **Match Scoring** - 0-100% compatibility score with detailed breakdown
- **Red Flag Detection** - Automatic identification of concerns

</td>
<td width="50%">

### 📊 Candidate Management
- **Kanban Board** - Visual pipeline (Applied → Interview → Hired)
- **Bulk Operations** - Select multiple candidates for batch actions
- **Resume Preview** - View documents in-app without downloading
- **Advanced Filters** - Search by score, status, skills, or date

</td>
</tr>
<tr>
<td width="50%">

### 🔗 Integrations
- **Google Forms** - Auto-generate application forms
- **Email Automation** - Confirmation, rejection, and interview invites
- **LinkedIn Detection** - Extract and validate LinkedIn profiles
- **Webhook API** - Real-time candidate data sync

</td>
<td width="50%">

### ⚡ Performance
- **Redis Caching** - 10-50x faster API responses
- **Background Jobs** - Non-blocking email queue
- **Serverless Ready** - Optimized for Vercel deployment
- **Dual Database** - SQLite (dev) / PostgreSQL (prod)

</td>
</tr>
</table>

---

## 🏆 Scoring System

Our proprietary 9-dimension scoring algorithm ensures fair, consistent candidate evaluation:

| Dimension | Weight | What We Measure |
|-----------|--------|-----------------|
| **Job Relevance** | 25% | Overall fit for the specific role |
| **Skills Match** | 20% | Technical skills alignment |
| **Technical Depth** | 15% | Expertise level and complexity |
| **Experience** | 10% | Years and relevance of experience |
| **Project Complexity** | 10% | Quality and scale of past work |
| **Communication** | 5% | Writing clarity in responses |
| **Culture Fit** | 5% | Team compatibility signals |
| **Education** | 5% | Academic background relevance |
| **Keywords** | 5% | Industry-specific terminology |

### Modifiers

| Modifier | Impact | Trigger |
|----------|--------|---------|
| 🦄 **Unicorn Bonus** | +8 pts | Perfect skill match + experience |
| 👔 **Leadership** | +5 pts | Management experience detected |
| 🔗 **No LinkedIn** | -2 pts | Missing professional presence |
| 🚩 **Red Flags** | -5 pts each | Gaps, job hopping, inconsistencies |
| 🤖 **AI Answers** | -12 pts | Detected AI-generated responses |

---

## 🖥️ Demo

### Dashboard
> Clean, modern interface showing all jobs at a glance with candidate counts and status indicators.

### Candidate View
> Kanban-style board for tracking candidates through your hiring pipeline with drag-and-drop.

### AI Scoring
> Detailed breakdown of each candidate's strengths and areas of concern.

---

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Git
- A [Perplexity AI](https://www.perplexity.ai/) API key

### Local Development

```bash
# Clone the repository
git clone https://github.com/MohammedMaheer/AI_JobFormMaker.git
cd AI_JobFormMaker

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the application
python app.py
```

🎉 Open **http://localhost:5000** in your browser!

### Production Deployment

For full production setup including:
- ☁️ Vercel serverless deployment
- 🐘 Neon PostgreSQL database
- ⚡ Upstash Redis caching
- 📝 Google Forms integration
- 📧 Gmail SMTP email

**See the comprehensive [SETUP_GUIDE.md](SETUP_GUIDE.md)**

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        FRONTEND                                  │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │  Dashboard  │  │   Kanban    │  │  Analytics  │              │
│  │   (HTML5)   │  │   Board     │  │   Charts    │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     FLASK API (Python)                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Routes    │  │  Services   │  │  Webhooks   │              │
│  │  /api/*     │  │  AI/Email   │  │  /webhook   │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐
│   PostgreSQL    │  │   Upstash       │  │   Perplexity    │
│   (Neon)        │  │   Redis         │  │   AI API        │
│   Database      │  │   Cache         │  │   Analysis      │
└─────────────────┘  └─────────────────┘  └─────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────┐
│                    GOOGLE INTEGRATION                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐              │
│  │   Forms     │  │   Drive     │  │   Apps      │              │
│  │  (Apply)    │  │  (Resumes)  │  │   Script    │              │
│  └─────────────┘  └─────────────┘  └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

---

## 🛠️ Tech Stack

<table>
<tr>
<td align="center" width="96">
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/python/python-original.svg" width="48" height="48" alt="Python" />
  <br>Python 3.11
</td>
<td align="center" width="96">
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/flask/flask-original.svg" width="48" height="48" alt="Flask" />
  <br>Flask
</td>
<td align="center" width="96">
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/postgresql/postgresql-original.svg" width="48" height="48" alt="PostgreSQL" />
  <br>PostgreSQL
</td>
<td align="center" width="96">
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/redis/redis-original.svg" width="48" height="48" alt="Redis" />
  <br>Redis
</td>
<td align="center" width="96">
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/javascript/javascript-original.svg" width="48" height="48" alt="JavaScript" />
  <br>JavaScript
</td>
<td align="center" width="96">
  <img src="https://cdn.jsdelivr.net/gh/devicons/devicon/icons/html5/html5-original.svg" width="48" height="48" alt="HTML5" />
  <br>HTML5
</td>
</tr>
</table>

| Component | Technology | Purpose |
|-----------|------------|---------|
| **Backend** | Python 3.11 + Flask | REST API & business logic |
| **Database** | Neon PostgreSQL | Persistent data storage |
| **Caching** | Upstash Redis | High-speed response caching |
| **AI Engine** | Perplexity AI | Resume analysis & scoring |
| **Hosting** | Vercel | Serverless deployment |
| **Forms** | Google Apps Script | Application form creation |
| **Email** | Gmail SMTP | Candidate notifications |

---

## 📁 Project Structure

```
AI_JobFormMaker/
│
├── 📄 app.py                    # Main Flask application
├── 📄 requirements.txt          # Python dependencies
├── 📄 vercel.json              # Vercel configuration
├── 📄 SETUP_GUIDE.md           # Comprehensive setup guide
│
├── 📁 services/
│   ├── ai_service.py           # AI analysis engine
│   ├── cache_service.py        # Redis/memory caching
│   ├── candidate_scorer.py     # 9-dimension scoring
│   ├── email_service.py        # Background email queue
│   ├── storage_service.py      # Database operations
│   ├── resume_parser.py        # Resume text extraction
│   └── file_processor.py       # File handling utilities
│
├── 📁 templates/
│   ├── dashboard.html          # Main dashboard
│   ├── job_details.html        # Candidate management
│   ├── index.html              # Job creation
│   └── analytics.html          # Analytics & reports
│
├── 📁 static/
│   ├── css/                    # Stylesheets
│   └── js/                     # Frontend JavaScript
│
└── 📁 data/                    # Local SQLite (dev only)
```

---

## 📖 Documentation

| Document | Description |
|----------|-------------|
| [SETUP_GUIDE.md](SETUP_GUIDE.md) | Complete step-by-step setup instructions |
| [PROJECT_INFO.md](PROJECT_INFO.md) | Technical architecture details |

---

## 🔐 Environment Variables

```ini
# Required
AI_PROVIDER=perplexity
PERPLEXITY_API_KEY=pplx-xxx...
DATABASE_URL=postgresql://...

# Optional - Caching (recommended for production)
UPSTASH_REDIS_REST_URL=https://xxx.upstash.io
UPSTASH_REDIS_REST_TOKEN=xxx...

# Optional - Google Forms Integration
GOOGLE_SCRIPT_URL=https://script.google.com/...

# Optional - Email Notifications
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=recruiting@company.com
SENDER_PASSWORD=app-password
```

---

## 🤝 Contributing

We welcome contributions from the community! Here's how you can help:

1. **Fork** the repository
2. **Create** a feature branch (`git checkout -b feature/amazing-feature`)
3. **Commit** your changes (`git commit -m 'Add amazing feature'`)
4. **Push** to the branch (`git push origin feature/amazing-feature`)
5. **Open** a Pull Request

### Development Guidelines

- Follow PEP 8 style guide for Python
- Add docstrings to new functions
- Update tests for new features
- Keep commits atomic and well-described

---

## 📜 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [Perplexity AI](https://www.perplexity.ai/) for powerful language models
- [Neon](https://neon.tech/) for serverless PostgreSQL
- [Upstash](https://upstash.com/) for serverless Redis
- [Vercel](https://vercel.com/) for seamless deployment

---

<p align="center">
  <strong>Built with ❤️ by the Acceleration Robotics Team</strong>
</p>

<p align="center">
  <a href="https://acceleration-robotics.com">Website</a> •
  <a href="https://github.com/acceleration-robotics">GitHub</a> •
  <a href="https://www.linkedin.com/company/acceleration-robotics/">LinkedIn</a>
</p>

<p align="center">
  <sub>© 2024-2025 Acceleration Robotics. All rights reserved.</sub>
</p>
