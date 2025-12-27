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

## 🛠️ Detailed Setup Guide (Beginner Friendly)

Follow these steps exactly to get the system running on your computer.

### Phase 1: Prepare Your Computer

1.  **Install Python:**
    *   Download Python from [python.org](https://www.python.org/downloads/).
    *   **IMPORTANT:** During installation, check the box that says **"Add Python to PATH"**.
2.  **Install Git (Optional but recommended):**
    *   Download from [git-scm.com](https://git-scm.com/downloads).
3.  **Get an Ngrok Account:**
    *   Go to [ngrok.com](https://ngrok.com) and sign up for a free account.
    *   Go to your dashboard and copy your **Authtoken**.

### Phase 2: Install the Application

1.  **Download the Code:**
    *   If using Git: Open a terminal/command prompt and run:
        ```bash
        git clone https://github.com/acceleration-robotics/recruitment-tool.git
        cd recruitment-tool
        ```
    *   If not using Git: Download the ZIP file from GitHub, extract it, and open that folder in VS Code or your terminal.

2.  **Set up the Python Environment:**
    *   Open your terminal inside the project folder.
    *   Run the following commands one by one:
        ```bash
        # 1. Create a virtual environment (keeps your computer clean)
        python -m venv .venv

        # 2. Activate the environment
        # Windows:
        .venv\Scripts\activate
        # Mac/Linux:
        source .venv/bin/activate

        # 3. Install required libraries
        pip install -r requirements.txt
        ```

### Phase 3: Start the Server

1.  **Run the Start Script:**
    *   In the same terminal, run:
        ```bash
        python start_with_ngrok.py
        ```
    *   If it asks for your Ngrok Authtoken, paste it and press Enter.

2.  **Copy the Public URL:**
    *   The terminal will show a message like:
        ```
        ============================================================
         NGROK TUNNEL ESTABLISHED
         Public URL: https://a1b2-c3d4.ngrok-free.app
         Webhook URL: https://a1b2-c3d4.ngrok-free.app/api/webhook/application
        ============================================================
        ```
    *   **Copy the `Webhook URL`**. You will need this for the next step.
    *   **KEEP THIS TERMINAL OPEN.** Do not close it.

### Phase 4: Connect Google Forms

1.  **Create a New Google Script:**
    *   Go to [script.google.com](https://script.google.com/home).
    *   Click **"+ New Project"** (top left).

2.  **Paste the Code:**
    *   Delete any code currently in the editor (like `function myFunction() {}`).
    *   Open the file `final_google_script.js` from this project folder.
    *   Copy **ALL** the code from that file.
    *   Paste it into the Google Script editor.

3.  **Configure the Webhook:**
    *   Look at the top of the script for line 22:
        ```javascript
        var WEBHOOK_URL = "https://...";
        ```
    *   Replace the URL inside the quotes with the **Webhook URL** you copied in Phase 3.

4.  **Run the Setup Trigger (Crucial Step):**
    *   In the toolbar, look for a dropdown menu that says `createForm` or `myFunction`. Change it to select **`setupTrigger`**.
    *   Click the **Run** button (▶️).
    *   **Grant Permissions:**
        *   A popup will appear saying "Authorization Required". Click **Review Permissions**.
        *   Select your Google Account.
        *   You might see a screen saying "Google hasn't verified this app" (because you just wrote it!).
        *   Click **Advanced** (bottom left).
        *   Click **Go to Untitled project (unsafe)**.
        *   Click **Allow**.
    *   Wait for the execution log to say "Trigger set up successfully".

5.  **Deploy as a Web App:**
    *   Click the blue **Deploy** button (top right) -> **New deployment**.
    *   Click the **Gear Icon** (Select type) -> **Web app**.
    *   **Description:** Enter "Job App".
    *   **Execute as:** Select **"Me"** (your email).
    *   **Who has access:** Select **"Anyone"** (This is important so candidates can access it).
    *   Click **Deploy**.
    *   Copy the **Web App URL** (it ends with `/exec`).

### Phase 5: Use the Tool

1.  **Open the Dashboard:**
    *   Go to your **Public URL** (from Phase 3) in your browser (e.g., `https://a1b2-c3d4.ngrok-free.app`).
2.  **Create a Job:**
    *   Paste a Job Description and click "Generate Questions".
3.  **Link the Form:**
    *   Scroll down to the "Create Job Application Form" section.
    *   Paste the **Web App URL** you copied in Phase 4 (Step 5).
    *   Click **Create Form**.
4.  **Done!**
    *   The system will give you a link to your new Google Form.
    *   Send this link to candidates.
    *   When they apply, their data will instantly appear in your Dashboard under "Candidate Ranking".

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

