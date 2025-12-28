# 🤖 Acceleration Robotics Recruitment Tool - Project Overview

## 📖 About The Project
The **Acceleration Robotics Recruitment Tool** is an advanced, AI-powered platform designed to streamline the hiring process for technical roles. By leveraging Large Language Models (LLMs) and automation, it eliminates the manual bottleneck of screening resumes and scheduling interviews.

This tool transforms a standard Google Form application into a fully automated recruitment pipeline, complete with candidate scoring, Kanban board management, and automated email communication.

---

## ✨ Key Features

### 1. 🧠 AI-Powered Candidate Scoring
*   **Resume Parsing:** Automatically extracts text from PDF and DOCX resumes.
*   **Contextual Analysis:** Uses Perplexity AI (or OpenAI) to analyze the candidate's experience against the specific Job Description.
*   **Advanced Scoring Engine:** Assigns a 0-100 score based on a weighted mix of:
    *   **Skills Match (25%)**
    *   **Relevance (25%)** - Contextual fit for the specific role.
    *   **Technical Depth (15%)** - Seniority and complexity of work.
    *   **Experience (15%)** - Years of experience.
    *   **Education (10%)**, **Culture Fit (5%)**, and **Keywords (5%)**.
*   **Executive Summary:** Generates a concise "Pros & Cons" list for every applicant.

### 2. 📊 Interactive Kanban Dashboard
*   **Glassmorphism UI:** A modern, clean interface with blur effects and gradients.
*   **Visual Pipeline:** Drag-and-drop candidates between stages:
    *   **Applied:** New candidates (automatically scored).
    *   **Interview Scheduled:** Candidates selected for the next round.
    *   **Rejected:** Candidates who didn't meet the criteria.
*   **Real-time Updates:** Status changes are saved instantly to the database.

### 3. 📧 Automated Communication
*   **Confirmation Emails:** Sent immediately upon application submission.
*   **Interview Invites:** Send Google Calendar invitations directly from the dashboard.
*   **Rejection Emails:** One-click professional rejection emails.
*   **Admin Alerts:** Get notified via email when a "High Potential" candidate (Score > 75) applies.

### 4. ☁️ Hybrid Storage Architecture
*   **Local Mode:** Uses SQLite for easy, zero-config local testing.
*   **Cloud Mode:** Automatically switches to PostgreSQL when deployed to Vercel/Render for persistent storage.

---

## 🛠️ Tech Stack

*   **Backend:** Python (Flask)
*   **Frontend:** HTML, CSS, JavaScript (Vanilla)
*   **AI Engine:** Perplexity API (Sonar Models)
*   **Database:** SQLite (Local) / PostgreSQL (Production)
*   **Integration:** Google Apps Script (for Google Forms Webhooks)
*   **Tunneling:** Ngrok (for exposing local server to Google Forms)

---

## 📂 Project Structure

```
web_job_ar/
├── app.py                 # Main Flask application entry point
├── start_with_ngrok.py    # Launcher script for local testing
├── requirements.txt       # Python dependencies
├── Procfile               # Deployment configuration for Render/Heroku
├── render.yaml            # Infrastructure as Code for Render
│
├── services/              # Business Logic Layer
│   ├── ai_service.py      # Interfaces with Perplexity API
│   ├── candidate_scorer.py# Logic for grading and ranking
│   ├── email_service.py   # SMTP email handling
│   ├── file_processor.py  # Resume downloading and text extraction
│   ├── resume_parser.py   # PDF/DOCX parsing logic
│   └── storage_service.py # Database abstraction (SQLite/Postgres)
│
├── static/                # Frontend Assets
│   ├── css/               # Stylesheets (Kanban, General)
│   └── js/                # Client-side logic
│
├── templates/             # HTML Views
│   ├── index.html         # (Optional) Direct upload form
│   └── ranking.html       # Main Admin Dashboard
│
└── data/                  # Local storage (SQLite DB & JSON)
```
