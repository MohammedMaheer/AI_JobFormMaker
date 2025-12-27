# 🚀 AI Recruitment Platform - Complete Setup Guide

This platform automates the entire recruitment lifecycle:
1.  **Generates Interview Questions** from Job Descriptions using AI.
2.  **Creates Google Forms** automatically for candidates to apply.
3.  **Scores Candidates** by analyzing their Resumes and Answers against the Job Description.
4.  **Ranks Candidates** in a dashboard.

---

## 📋 Prerequisites

1.  **Python 3.8+** installed.
2.  **Ngrok Account** (Free) for exposing your local server to Google Forms.
3.  **Google Account** for Google Forms & Sheets.

---

## 🛠️ Step 1: Local Environment Setup

1.  **Clone/Download** this repository.
2.  **Open a terminal** in the project folder.
3.  **Create a Virtual Environment** (Recommended):
    ```bash
    python -m venv venv
    # Windows:
    venv\Scripts\activate
    # Mac/Linux:
    source venv/bin/activate
    ```
4.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```

---

## 🌐 Step 2: Ngrok Setup (Crucial for Webhooks)

Since Google Forms needs to send data to your local computer, we use Ngrok.

1.  **Sign up** at [ngrok.com](https://ngrok.com).
2.  **Get your Authtoken** from the dashboard.
3.  **Run the Start Script**:
    ```bash
    python start_with_ngrok.py
    ```
4.  **Enter your Authtoken** when prompted (first time only).
5.  **Copy the Public URL** displayed in the terminal (e.g., `https://your-domain.ngrok-free.dev`).
    *   *Note: Keep this terminal running!*

---

## 📜 Step 3: Google Apps Script Setup

This script acts as the bridge between Google Forms and your Python App.

1.  **Copy the Code**:
    *   Open `final_google_script.js` in this project.
    *   Copy the **entire content**.

2.  **Create Google Script**:
    *   Go to [script.google.com](https://script.google.com/home).
    *   Click **New Project**.
    *   Paste the code into the editor (replace existing code).

3.  **Configure URL**:
    *   Find the line: `var WEBHOOK_URL = "..."`
    *   Replace it with your **Ngrok URL** + `/api/webhook/application`.
    *   *Example:* `var WEBHOOK_URL = "https://your-domain.ngrok-free.dev/api/webhook/application";`

4.  **Deploy as Web App**:
    *   Click **Deploy** (top right) > **New deployment**.
    *   Select type: **Web app**.
    *   Description: "Job App v1".
    *   **Execute as**: "Me" (your email).
    *   **Who has access**: **Anyone** (Important!).
    *   Click **Deploy**.
    *   **Authorize** the script:
        1. Click **Review Permissions**.
        2. Choose your account.
        3. Click **Advanced** > **Go to ... (unsafe)**.
        4. Click **Allow**.
    *   **⚠️ CRITICAL:** You MUST grant **ALL** permissions requested, especially **Google Drive** access. This allows the script to share resume files so the AI can read them.

5.  **Copy the Script URL**:
    *   Copy the **Web App URL** (ends in `/exec`).

---

## 🚀 Step 4: Running the Workflow

1.  **Open the App**:
    *   Go to your Ngrok URL in your browser.

2.  **Generate Questions**:
    *   Enter a **Job Title** (e.g., "Marketing Manager").
    *   Paste the **Job Description**.
    *   Click **Generate Questions**.

3.  **Create the Form**:
    *   Scroll down to **"Create Job Application Form"**.
    *   Enter **Company Name**.
    *   Paste the **Google Apps Script URL** (from Step 3).
    *   Click **Create Form**.

4.  **Distribute & Apply**:
    *   Click the **"Open Form"** link generated.
    *   Fill it out as a candidate (Upload a Resume!).
    *   Submit.

5.  **View Scores**:
    *   Go back to your App's **Dashboard** (or `/candidates` page).
    *   You will see the candidate scored and ranked based on their Resume and Answers!

---

## 🧠 How the "Intelligence" Works

*   **Smart Parsing**: The Google Script uses a weighted scoring system to find "Name", "Phone", and "Resume" fields even if you rename them (e.g., "Upload CV" instead of "Resume").
*   **AI Scoring**: The Python backend uses AI to extract skills, experience, and education from the resume and compares them against the Job Description to calculate a match percentage (0-100%).

---

## ⚠️ Troubleshooting

*   **"Skills Match 0%"**: Ensure the Job Description has clear keywords. The system matches Resume Skills vs JD Keywords.
*   **"Ngrok Error"**: Restart `python start_with_ngrok.py`. Free Ngrok URLs change every time you restart unless you have a static domain.
*   **"Script Error"**: If you change the Ngrok URL, you MUST update the `WEBHOOK_URL` in the Google Apps Script and **Deploy > Manage Deployments > Edit > New Version**.

---

## 📂 Project Structure

*   `app.py`: Main Flask backend.
*   `final_google_script.js`: The Google Apps Script code.
*   `services/`: Helper modules for AI, Scoring, and File Processing.
*   `templates/`: HTML frontend.

