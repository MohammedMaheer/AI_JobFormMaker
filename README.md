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
