
# 🚀 Setup Guide: Acceleration Robotics Recruitment Tool

This is the **Official Setup Guide** for installing, configuring, and deploying the Recruitment Tool. 
For a general overview of the project features and architecture, please see [PROJECT_INFO.md](PROJECT_INFO.md).

**New Features (v2.0):**
*   ✨ **Glassmorphism UI:** Modern, sleek interface with blur effects and gradients.
*   🧠 **Advanced AI Scoring:** Improved accuracy with "Relevance" and "Technical Depth" metrics.
*   📧 **Gmail Integration:** One-click "Compose" button pre-fills candidate details.
*   ⚖️ **Fairer Ranking:** Penalties for keyword stuffing and AI-generated answers.

---

## 📋 Table of Contents
1.  [Prerequisites](#1-prerequisites)
2.  [Installation](#2-installation)
3.  [Configuration (.env)](#3-configuration-env)
4.  [Option A: Local Deployment (Recommended for Testing)](#4-option-a-local-deployment-recommended-for-testing)
5.  [Option B: Cloud Deployment (Recommended for Production)](#5-option-b-cloud-deployment-recommended-for-production)
6.  [Google Forms Integration (Crucial Step)](#6-google-forms-integration-crucial-step)
7.  [How to Use the Dashboard](#7-how-to-use-the-dashboard)
8.  [Troubleshooting](#8-troubleshooting)

---

## 1. Prerequisites

Before you start, make sure you have these installed on your computer:

1.  **Python (Version 3.8 or higher)**
    *   Download: [python.org/downloads](https://www.python.org/downloads/)
    *   **IMPORTANT:** During installation on Windows, check the box **"Add Python to PATH"**.
2.  **VS Code (Code Editor)**
    *   Download: [code.visualstudio.com](https://code.visualstudio.com/)
3.  **Git (Optional but recommended)**
    *   Download: [git-scm.com](https://git-scm.com/downloads)
4.  **Ngrok Account (For Local Testing)**
    *   Sign up: [ngrok.com](https://ngrok.com)
    *   Get your **Authtoken** from the dashboard.

---

## 2. Installation

1.  **Download the Code**
    *   If using Git:
        ```bash
        git clone https://github.com/your-repo/web_job_ar.git
        cd web_job_ar
        ```
    *   If downloading ZIP: Extract the folder and open it in VS Code.

2.  **Open Terminal in VS Code**
    *   Press `Ctrl + ~` (tilde) to open the terminal.

3.  **Create a Virtual Environment**
    *   This keeps your project dependencies separate from your system.
    *   **Windows:**
        ```bash
        python -m venv .venv
        .venv\Scripts\activate
        ```
    *   **Mac/Linux:**
        ```bash
        python3 -m venv .venv
        source .venv/bin/activate
        ```
    *   *You should see `(.venv)` appear at the start of your terminal line.*

4.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

---

## 3. Configuration (.env)

You need to set up your API keys and passwords.

1.  Create a new file named `.env` in the root folder (same place as `app.py`).
2.  Copy and paste the following content into it:

```ini
# --- AI Configuration ---
# Choose your AI provider: perplexity (default), openai, or claude
AI_PROVIDER=perplexity

# 1. Perplexity (Default) - Get key: https://www.perplexity.ai/settings/api
PERPLEXITY_API_KEY=pplx-xxxxxxxxxxxxxxxxxxxxxxxx

# 2. OpenAI (Optional) - Get key: https://platform.openai.com/api-keys
# OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxx
# OPENAI_MODEL=gpt-4o  # Optional: Change model (e.g., gpt-4o-mini)

# 3. Claude (Optional) - Get key: https://console.anthropic.com/settings/keys
# ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxx
# CLAUDE_MODEL=claude-3-5-sonnet-20240620  # Optional: Change model

# --- Server Configuration ---
FLASK_ENV=development
PORT=5000

# --- Email Configuration (Gmail) ---
# 1. Go to Google Account -> Security -> 2-Step Verification (Enable it)
# 2. Go to "App Passwords" (search for it in security settings)
# 3. Create a new app password named "Recruitment App"
# 4. Copy the 16-character code below (remove spaces)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SENDER_EMAIL=your_email@gmail.com
SENDER_PASSWORD=your_16_char_app_password
SENDER_NAME=Your Company Name
ADMIN_EMAIL=your_email@gmail.com

# --- Database Configuration ---
# Leave this commented out for Local Testing (it will use a local file)
# DATABASE_URL=postgresql://...
```

---

## 4. Option A: Local Deployment (Recommended for Testing)

This runs the app on your computer. You must keep the terminal open for it to work.

1.  **Start the App with Ngrok**
    *   Run this command in your terminal:
        ```bash
        python start_with_ngrok.py
        ```
    *   If it asks for your Ngrok Authtoken, paste it (right-click to paste in some terminals) and press Enter.

2.  **Copy the Webhook URL**
    *   The terminal will display a box like this:
        ```
        ============================================================
         NGROK TUNNEL ESTABLISHED
         Public URL: https://a1b2-c3d4.ngrok-free.app
         Webhook URL: https://a1b2-c3d4.ngrok-free.app/api/webhook/application
        ============================================================
        ```
    *   **COPY the `Webhook URL`**. You need it for the Google Forms step.
    *   **KEEP THE TERMINAL OPEN.**

3.  **Go to [Section 6: Google Forms Integration](#6-google-forms-integration-crucial-step)** to finish setup.

---

## 5. Option B: Cloud Deployment (Recommended for Production)

This runs the app 24/7 on the cloud. We use **Neon** for the database and **Vercel** for hosting.

### **Why these tools?**
*   **Neon:** Gives you a real PostgreSQL database (better than the local file).
*   **Vercel:** Hosts your Python code for free.
*   **Note:** Vercel is "Serverless". This means it might be slightly slower to "wake up" than your local computer, but it's free and always on.

1.  **Database Setup (Neon)**
    *   Go to [Neon.tech](https://neon.tech) and create a free project.
    *   Copy the **Connection String** (e.g., `postgres://user:pass@...`).
    *   **Important:** Ensure the URL ends with `?sslmode=require` (Neon usually adds this automatically).

2.  **Deploy to Vercel**
    *   Push your code to GitHub.
    *   Go to [Vercel](https://vercel.com) -> Add New Project -> Import your repo.
    *   **Environment Variables:** Add all the variables from your `.env` file:
        *   `AI_PROVIDER` (e.g., `perplexity`)
        *   `PERPLEXITY_API_KEY` (or others)
        *   `SMTP_SERVER`, `SMTP_PORT`, `SENDER_EMAIL`, `SENDER_PASSWORD`, `SENDER_NAME`, `ADMIN_EMAIL`
        *   **`DATABASE_URL`**: Paste your Neon connection string here.
    *   Click **Deploy**.

3.  **Get Webhook URL**
    *   Once deployed, your URL will be `https://your-project.vercel.app`.
    *   Your Webhook URL is `https://your-project.vercel.app/api/webhook/application`.

4.  **Go to [Section 6: Google Forms Integration](#6-google-forms-integration-crucial-step)** to finish setup.

---

## 6. Google Forms Integration (Crucial Step)

This connects Google Forms to your Python app.

1.  **Create a Google Script**
    *   Go to [script.google.com](https://script.google.com/home).
    *   Click **+ New Project**.

2.  **Paste the Code**
    *   Open `final_google_script.js` in your VS Code.
    *   Copy **ALL** the code.
    *   Paste it into the Google Script editor (delete any existing code there).

3.  **Update the Webhook URL**
    *   Look at line 22 in the Google Script:
        ```javascript
        var WEBHOOK_URL = "PASTE_YOUR_WEBHOOK_URL_HERE";
        ```
    *   Replace the text with the URL you got from **Option A** (Ngrok) or **Option B** (Vercel).

4.  **Run Setup Trigger**
    *   In the toolbar dropdown, select **`setupTrigger`**.
    *   Click **Run** (▶️).
    *   **Permissions:**
        *   Click "Review Permissions".
        *   Select your account.
        *   Click "Advanced" -> "Go to (unsafe)" -> "Allow".
    *   Wait for it to finish.

5.  **Deploy as Web App**
    *   Click **Deploy** (blue button) -> **New deployment**.
    *   Select type: **Web app**.
    *   Description: "Job App".
    *   Execute as: **Me**.
    *   Who has access: **Anyone** (Important!).
    *   Click **Deploy**.
    *   **Copy the Web App URL**.

---

## 7. How to Use the Dashboard

1.  **Access the Dashboard**
    *   **Local:** `http://127.0.0.1:5000/ranking`
    *   **Cloud:** `https://your-project.vercel.app/ranking`

2.  **View Candidates**
    *   Candidates appear in a list sorted by **AI Score**.                           
    *   **Score Breakdown:** Hover over the score to see details (Skills, Experience, Relevance, Depth).
    *   **Click on a candidate** to open the **Detailed View**:
        *   **Pros & Cons:** Displayed side-by-side for quick comparison.
        *   **Resume:** Embedded view of the candidate's CV.
        *   **Email:** Click the email address to open a **Gmail Compose** window with the subject and body pre-filled.

3.  **Kanban Board**
    *   Click **"Kanban View"** to see the board.
    *   **Drag and Drop** candidates to change their status:
        *   **Applied** -> **Interview Scheduled**: Opens a modal to send a Google Calendar invite.
        *   **Any** -> **Rejected**: Prompts to send a rejection email.

---

## 8. Troubleshooting

*   **"Webhook URL not working"**:
    *   Check if Ngrok is still running. The URL changes every time you restart Ngrok (unless you have a paid account).
    *   Update the URL in Google Apps Script if it changed.
*   **"No candidates showing"**:
    *   Check the terminal logs for "WEBHOOK RECEIVED".
    *   If using Vercel, check the "Logs" tab in the Vercel dashboard.
*   **"Email not sending"**:
    *   Verify your App Password in `.env`.
    *   Check if `SMTP_PORT` is 587.

# AI Interview Question Generator

A powerful web application that transforms job descriptions into professional interview questions using advanced AI models. It features seamless integration with Google Sheets and Forms for a complete recruitment workflow.

Acceleration Robotics

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
