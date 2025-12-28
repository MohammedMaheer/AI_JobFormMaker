# 🛠️ Complete Setup & Deployment Guide

This guide covers the end-to-end process of setting up the **AI Recruitment Tool**, connecting it to a **Neon PostgreSQL** database, deploying it to **Vercel**, and integrating it with **Google Forms**.

---

## 📋 Table of Contents
1.  [Prerequisites](#1-prerequisites)
2.  [Local Development Setup](#2-local-development-setup)
3.  [Database Setup (Neon Postgres)](#3-database-setup-neon-postgres)
4.  [Deployment to Vercel](#4-deployment-to-vercel)
5.  [Google Forms Integration](#5-google-forms-integration)
6.  [Troubleshooting](#6-troubleshooting)

---

## 1. Prerequisites

Before starting, ensure you have the following accounts and tools:

*   **GitHub Account**: To host your code.
*   **Vercel Account**: For hosting the application (Free tier is sufficient).
*   **Neon Console Account**: For the PostgreSQL database (Free tier is sufficient).
*   **Google Account**: For Google Forms and Sheets.
*   **Python 3.9+**: Installed on your local machine.
*   **Git**: Installed on your local machine.

---

## 2. Local Development Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/YOUR_USERNAME/AI_JobFormMaker.git
    cd AI_JobFormMaker
    ```

2.  **Create a Virtual Environment**
    ```bash
    # Windows
    python -m venv .venv
    .venv\Scripts\activate

    # Mac/Linux
    python3 -m venv .venv
    source .venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Configure Environment Variables**
    Create a `.env` file in the root directory:
    ```ini
    # AI Provider (perplexity, openai, or claude)
    AI_PROVIDER=perplexity
    PERPLEXITY_API_KEY=your_perplexity_key
    
    # Database (Will be filled in Step 3)
    DATABASE_URL=
    
    # Security
    SECRET_KEY=your_secret_key
    ```

5.  **Run Locally**
    ```bash
    python app.py
    ```
    Access the app at `http://localhost:5000`.

---

## 3. Database Setup (Neon Postgres)

Since Vercel is serverless and has ephemeral storage (files disappear after requests), we need a persistent database to store candidate data.

1.  **Create a Neon Project**
    *   Go to [Neon Console](https://console.neon.tech/).
    *   Click **"New Project"**.
    *   Name it `recruitment-db`.
    *   Region: Choose one close to you (e.g., US East).

2.  **Get Connection String**
    *   On the Dashboard, look for **"Connection Details"**.
    *   Select **"Pooled connection"** (Important for serverless!).
    *   Copy the Connection String (e.g., `postgres://user:pass@ep-xyz.us-east-2.aws.neon.tech/neondb?sslmode=require`).

3.  **Update Local Configuration**
    *   Paste this string into your local `.env` file as `DATABASE_URL`.

4.  **Initialize the Database**
    *   Run the application locally once (`python app.py`).
    *   The app automatically checks for the database tables and creates them if they don't exist.
    *   You should see logs like `Database initialized successfully`.

---

## 4. Deployment to Vercel

1.  **Push to GitHub**
    Ensure your latest code is on GitHub.
    ```bash
    git add .
    git commit -m "Ready for deployment"
    git push origin main
    ```

2.  **Import Project in Vercel**
    *   Go to [Vercel Dashboard](https://vercel.com/dashboard).
    *   Click **"Add New..."** > **"Project"**.
    *   Import your GitHub repository.

3.  **Configure Project Settings**
    *   **Framework Preset**: Select **"Other"**.
    *   **Root Directory**: `./` (default).
    *   **Build Command**: Leave empty (Vercel handles Python automatically via `vercel.json`).
    *   **Output Directory**: Leave empty.

4.  **Environment Variables**
    Add the following variables in the Vercel dashboard:
    *   `AI_PROVIDER`: `perplexity` (or your choice)
    *   `PERPLEXITY_API_KEY`: `your_key`
    *   `DATABASE_URL`: **Paste your Neon Pooled Connection String here.**
    *   `FLASK_ENV`: `production`
    *   `VERCEL`: `1`

5.  **Deploy**
    *   Click **"Deploy"**.
    *   Wait for the build to finish.
    *   Once deployed, you will get a domain (e.g., `https://ai-job-maker.vercel.app`).

---

## 5. Google Forms Integration

Now we connect Google Forms to your deployed Vercel app.

1.  **Create a Google Form**
    *   Go to Google Forms and create a new blank form.
    *   Give it a title (e.g., "Senior Developer Application").

2.  **Open Script Editor**
    *   Click the **three dots (⋮)** in the top right.
    *   Select **"Script editor"** (or Extensions > Apps Script).

3.  **Install the Script**
    *   Delete any code in `Code.gs`.
    *   Copy the content of `final_google_script.js` from this repository.
    *   Paste it into the script editor.

4.  **Configure the Script**
    *   Find the line: `var WEBHOOK_URL = "..."`
    *   Replace it with your **Vercel App URL** + `/api/webhook/application`.
    *   Example: `var WEBHOOK_URL = "https://your-app.vercel.app/api/webhook/application";`

5.  **Deploy as Web App**
    *   Click **"Deploy"** (blue button) > **"New deployment"**.
    *   **Select type**: "Web app".
    *   **Description**: "v1".
    *   **Execute as**: "Me".
    *   **Who has access**: **"Anyone"** (Crucial for the form to work publicly).
    *   Click **"Deploy"**.

6.  **Authorize & Setup Trigger**
    *   In the script editor, select the function `setupTrigger` from the dropdown menu.
    *   Click **"Run"**.
    *   Grant the necessary permissions (Drive, Forms, External Requests).
    *   *Note: You might see a "Google hasn't verified this app" warning. Click "Advanced" > "Go to (unsafe)" since it's your own script.*

7.  **Test It!**
    *   Fill out your Google Form.
    *   Upload a dummy resume.
    *   Submit.
    *   Check your Vercel App Dashboard (`/ranking` page) to see the candidate appear!

---

## 6. Troubleshooting

### Resume "Not Found" (404)
*   **Cause**: Vercel cannot store files locally.
*   **Solution**: The system now saves the **original Google Drive URL** instead of a local path. Ensure your Google Script is updated to the latest version which handles file permissions correctly.

### Webhook Error 500
*   **Cause**: Database connection issues or invalid data.
*   **Solution**: Check Vercel Logs. Ensure `DATABASE_URL` is correct and uses the "Pooled" connection string from Neon.

### "Script function not found"
*   **Cause**: You didn't save the script before running.
*   **Solution**: Press Ctrl+S in the Google Apps Script editor before clicking Run.
