# AI Interview Question Generator

A powerful web application that transforms job descriptions into professional interview questions using advanced AI models. It features seamless integration with Google Sheets and Forms for a complete recruitment workflow.

![Acceleration Robotics](https://www.accelerationrobotics.com/img/logo.png)

## ✨ Features

- **🤖 Multi-AI Support**: Choose between Perplexity (default), OpenAI (GPT-4o), or Claude (Haiku) for question generation.
- **📄 Flexible Input**: Upload PDF, DOCX, TXT files or paste job descriptions directly.
- **🎯 Smart Generation**: Creates Technical, Behavioral, Situational, or Mixed questions based on the job role.
- **📝 Job Application Builder**: Automatically creates Google Forms for job applications with the generated interview questions included.
- **📊 Google Sheets Integration**: Save generated questions directly to Google Sheets via Zapier or a free Google Apps Script.
- **💾 Export Options**: Download results as JSON, CSV, or Text files.
- **🔄 Smart History**: Remembers your Webhook URLs for quick access.

## 🚀 Setup Guide

### Prerequisites
- Python 3.8 or higher
- Git

### Local Installation

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd web_job_ar
   ```

2. **Create a virtual environment**
   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Access the app**
   Open your browser and navigate to `http://127.0.0.1:5000`

## 📖 Usage Guide

### 1. Generating Questions
1. Enter the **Job Title** (e.g., "Senior Python Developer").
2. **Upload** a job description file (PDF/DOCX) OR **paste** the text.
3. Select the **Number of Questions** and **Type** (Technical, Behavioral, etc.).
4. (Optional) Open **AI Settings** to choose a specific provider (OpenAI/Claude) or use your own API key.
5. Click **Generate Questions**.

### 2. Saving to Google Sheets (Free Method)
1. Click the **"Get Free Google Apps Script"** link in the app.
2. Copy the provided code.
3. Open your Google Sheet, go to **Extensions > Apps Script**.
4. Paste the code and click **Deploy > New Deployment**.
5. Select **Web App**, set "Who has access" to **"Anyone"**, and deploy.
6. Copy the **Web App URL** and paste it into the website's Webhook URL field.
7. Click **Save to Sheets**.

### 3. Creating a Job Application Form
1. Generate your interview questions first.
2. Scroll to the **"Create Job Application Form"** section.
3. Enter your **Company Name**.
4. Paste your **Google Apps Script URL** (same as above).
5. Click **Create Job Application Form**.
6. The app will generate a Google Form with standard fields (Name, Email, Resume) AND your interview questions, then provide you with the link.

### 4. Using Zapier (Alternative)
If you prefer Zapier:
1. Create a "Catch Hook" trigger in Zapier.
2. Connect it to Google Sheets (Create Row) or Google Forms.
3. Use the Zapier Webhook URL in the application.

## ☁️ Deployment (Render.com)

This app is ready for free hosting on Render:

1. Push your code to GitHub.
2. Sign up at [render.com](https://render.com).
3. Create a **New Web Service**.
4. Connect your repository.
5. Use the following settings:
   - **Runtime**: Python 3
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `gunicorn app:app`
6. Click **Deploy**.

## 🛠️ Tech Stack
- **Backend**: Flask (Python)
- **Frontend**: HTML5, CSS3, JavaScript
- **AI Integration**: Perplexity API, OpenAI API, Anthropic API
- **File Processing**: PyPDF2, python-docx

## 📄 License
MIT License

---

# Automated AI Job Application & Candidate Scoring Platform

## Overview
This project automates the process of generating job application forms, collecting candidate responses, and scoring/ranking candidates using AI. It integrates Google Forms, Google Apps Script, and a Python backend (Flask) with AI-powered resume and answer analysis.

## Features
- **Generate Interview Questions:** Upload or paste a job description to generate tailored interview questions using AI.
- **Auto-Create Google Forms:** Instantly create Google Forms for job applications with all required fields and questions.
- **Webhook Integration:** Google Forms responses are sent to your Python backend for processing.
- **Resume Parsing:** Supports PDF, DOCX, and TXT resumes (uploaded via Google Form file upload).
- **AI Scoring:** Ranks candidates by matching resumes and answers to the job description.
- **Admin Dashboard:** View, score, and rank all candidates in a modern web UI.

## Quick Start

### 1. Clone & Install
```bash
git clone <your-repo-url>
cd web_job_ar
python -m venv .venv
.venv\Scripts\activate  # On Windows
pip install -r requirements.txt
```

### 2. Start the Backend with Ngrok
```bash
python start_with_ngrok.py
```
- Copy the Webhook URL shown (e.g. `https://xxxx.ngrok-free.dev/api/webhook/application`)

### 3. Google Apps Script Setup
- Open `final_google_script.js` in VS Code
- Copy all code
- Go to [script.google.com](https://script.google.com/home) > New Project
- Paste the code, set `WEBHOOK_URL` to your Ngrok URL
- Deploy as **Web App** (execute as Me, access: Anyone)
- Copy the Web App URL

### 4. Create a Job Application Form
- Open your Python app in the browser (Ngrok URL)
- Generate questions and paste the Web App URL in the "Create Job Application Form" section
- Click "Create Job Application Form"
- Open the generated Google Form and test it

## Troubleshooting
- **Resume Parsing Fails:**
  - Make sure the Google Apps Script sets file sharing to "Anyone with the link" for uploads.
  - Only new forms created after the script update will work for public file access.
- **Ngrok Tunnel Issues:**
  - Ensure you use your Ngrok Auth Token and the tunnel is active.
- **Google Script Errors:**
  - Always deploy a new version after updating the script.
  - Grant all permissions (especially Drive access) when prompted.

## Credits
- AI by Perplexity, OpenAI, or Claude (configurable)
- Built with Flask, Google Apps Script, and modern web technologies

## License
MIT

