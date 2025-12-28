# 🚀 AI Recruitment & Interview Tool

**Transform Job Descriptions into Professional Interview Questions & Automate Candidate Scoring.**

![Project Status](https://img.shields.io/badge/Status-Active-success)
![Python](https://img.shields.io/badge/Python-3.9+-blue)
![Flask](https://img.shields.io/badge/Framework-Flask-green)
![Vercel](https://img.shields.io/badge/Deployment-Vercel-black)
![Neon](https://img.shields.io/badge/Database-Neon%20Postgres-orange)

## 🌟 Overview

This tool streamlines the recruitment process by leveraging AI to:
1.  **Generate Interview Questions**: Analyze job descriptions and create tailored technical, behavioral, and situational questions.
2.  **Automate Applications**: Create Google Forms automatically that sync responses to your dashboard.
3.  **Score Candidates**: AI analyzes resumes against the job description, providing a match score (0-100%) and detailed feedback.
4.  **Rank Applicants**: View a leaderboard of candidates based on their suitability.

---

## ⚡ Recent Advancements (v2.0)

We have significantly upgraded the architecture for scalability and reliability:

*   **☁️ Serverless Deployment (Vercel)**: The backend now runs on Vercel's robust serverless infrastructure, ensuring high availability and zero maintenance.
*   **🗄️ Persistent Database (Neon Postgres)**: Replaced local JSON storage with a cloud-hosted PostgreSQL database (Neon) to persist candidate data across serverless function restarts.
*   **🤖 Intelligent Resume Parsing**: 
    *   Handles **Google Drive** file uploads directly from Google Forms.
    *   Automatically converts private Drive files to accessible links for the AI scorer.
    *   Falls back to robust text extraction if file download fails.
*   **🔄 Real-time Webhooks**: Seamless integration between Google Forms and the Python backend via a custom Google Apps Script.

---

## 🛠️ Installation & Setup

We have moved the detailed installation instructions to a dedicated guide.

👉 **[CLICK HERE FOR THE COMPLETE SETUP GUIDE](SETUP_GUIDE.md)** 👈

The guide covers:
1.  **Local Development**: Running the Flask app on your machine.
2.  **Database Setup**: Creating a free Postgres database on Neon.
3.  **Cloud Deployment**: Deploying to Vercel in minutes.
4.  **Google Forms Integration**: Setting up the automation script.

---

## 🧩 Tech Stack

*   **Backend**: Python (Flask)
*   **Frontend**: HTML5, CSS3 (Glassmorphism UI), JavaScript
*   **Database**: PostgreSQL (via Neon.tech)
*   **AI Engine**: Perplexity AI (Default), OpenAI GPT-4, or Claude 3.5
*   **Hosting**: Vercel (Serverless)
*   **Integration**: Google Apps Script (Forms & Sheets)

---

## 📂 Project Structure

```
├── app.py                  # Main Flask Application & Webhook Handler
├── services/               # Core Logic Modules
│   ├── ai_service.py       # AI Question Generation & Scoring
│   ├── storage_service.py  # Database Interactions (Postgres)
│   ├── resume_parser.py    # PDF/DOCX Text Extraction
│   └── candidate_scorer.py # Scoring Algorithm
├── static/                 # CSS & JavaScript
├── templates/              # HTML Templates
├── final_google_script.js  # Google Apps Script for Forms Integration
├── SETUP_GUIDE.md          # Detailed Installation Instructions
└── requirements.txt        # Python Dependencies
```

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
