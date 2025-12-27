# Acceleration Robotics Recruitment Tool

A robust, AI-powered recruitment platform that automates candidate screening, resume parsing, and scoring. It integrates seamlessly with Google Forms to collect applications and uses LLMs to rank candidates against job descriptions.

## Features
*   **AI-Powered Scoring:** Automatically ranks candidates based on skills, experience, and education match.
*   **Resume Parsing:** Extracts details from PDF, DOCX, TXT, and HTML resumes.
*   **Google Forms Integration:** Automatically creates job application forms and syncs responses.
*   **Candidate Dashboard:** A dark-themed, professional dashboard to view and manage applicants.
*   **Intelligent Analysis:** Generates pros/cons and executive summaries for every candidate.

---

## ⚠️ CRITICAL: Keeping the App Running

**If you are running this on your local computer (laptop/desktop):**

1.  **Do Not Close the Terminal:** The window running `python start_with_ngrok.py` must stay open at all times. If you close it, the website goes offline.
2.  **Disable Sleep Mode:** Your computer must **not** go to sleep or hibernate.
    *   *Windows:* Settings > System > Power & sleep > Set "Sleep" to "Never".
    *   *Mac:* System Settings > Lock Screen > Set "Turn display off" to "Never" (or use an app like Amphetamine).
3.  **Stable Internet:** Your computer needs a continuous internet connection.

**For 24/7 Availability (Recommended for Production):**
If you need the app to run for days without keeping your computer on, you should deploy it to a cloud provider like **Render**, **Railway**, or **AWS**.

---

## 🛠️ Setup Guide

### 1. Prerequisites
*   Python 3.8 or higher installed.
*   A Google Account (for Forms/Sheets).
*   An Ngrok Account (free) for public access.

### 2. Local Installation
1.  **Clone the repository:**
    ```bash
    git clone https://github.com/acceleration-robotics/recruitment-tool.git
    cd recruitment-tool
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    # Windows
    .venv\Scripts\activate
    # Mac/Linux
    source .venv/bin/activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### 3. Ngrok Setup (Required for Public Access)
1.  Sign up at [ngrok.com](https://ngrok.com).
2.  Get your **Authtoken** from the dashboard.
3.  **Run the application:**
    ```bash
    python start_with_ngrok.py
    ```
4.  Copy the **Public URL** (e.g., `https://xyz.ngrok-free.app`) displayed in the terminal.

### 4. Google Apps Script Integration
This connects your Google Form to the Python backend.

1.  Open the App in your browser and click **"Google Apps Script Setup"**.
2.  **Copy the Code** provided in the modal.
3.  Go to your Google Form/Sheet -> **Extensions** -> **Apps Script**.
4.  Paste the code, replacing everything else.
5.  **Update the Configuration:**
    *   Find `var WEBHOOK_URL = "..."` at the top.
    *   Replace it with your Ngrok URL + `/api/webhook/application`.
    *   Example: `https://your-ngrok-url.ngrok-free.app/api/webhook/application`
6.  **Save** the script.
7.  **Run the Setup Trigger (CRITICAL):**
    *   Select `setupTrigger` from the function dropdown menu.
    *   Click **Run**.
    *   **Review Permissions:** You will be asked to grant access.
    *   **IMPORTANT:** You MUST allow access to **"See, edit, create, and delete all of your Google Drive files"**. This is required to make resume uploads accessible to the AI.
8.  **Deploy as Web App:**
    *   Click **Deploy** > **New deployment**.
    *   Select type: **Web app**.
    *   Execute as: **Me**.
    *   Who has access: **Anyone**.
    *   Click **Deploy**.

---

## 🚀 Usage Workflow

1.  **Create a Job:**
    *   Go to the app homepage.
    *   Paste a Job Description.
    *   Click **"Generate Questions"**.
2.  **Create the Form:**
    *   Review the AI-generated questions.
    *   Click **"Create Google Form"**.
    *   The script will generate a form with Resume Upload, Date pickers, and your questions.
3.  **Candidates Apply:**
    *   Share the Form URL.
    *   Candidates fill it out and upload resumes.
4.  **View Rankings:**
    *   Go to the **"Candidate Ranking"** page in the app.
    *   Click **"Refresh Candidates"**.
    *   See AI scores, summaries, and contact details.

## 🔧 Troubleshooting

*   **Skills Match is 0%?**
    *   Ensure the resume is readable. The system now uses a hybrid AI + Keyword approach. If it persists, the resume might be an image scan (OCR is not currently supported).
*   **Google Drive Warning?**
    *   The system automatically handles Google's virus scan warnings for large files.
*   **"ScriptError: Authorization is required"?**
    *   You didn't run `setupTrigger` or didn't accept the permissions. Go back to the Apps Script editor and run `setupTrigger` again.

