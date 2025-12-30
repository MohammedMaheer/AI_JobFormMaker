import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import os
import threading
from queue import Queue
from datetime import datetime


class EmailService:
    """
    Email service with background sending support.
    Emails are queued and sent in a background thread to avoid blocking the main request.
    """
    
    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', 587))
        self.sender_email = os.getenv('SENDER_EMAIL')
        self.sender_password = os.getenv('SENDER_PASSWORD')
        self.sender_name = os.getenv('SENDER_NAME', 'Recruitment Team')
        self.admin_email = os.getenv('ADMIN_EMAIL')
        self.enabled = bool(self.sender_email and self.sender_password)
        
        # Background email queue
        self.email_queue = Queue()
        self.worker_thread = None
        self.is_running = False
        
        # Email stats
        self.stats = {
            'queued': 0,
            'sent': 0,
            'failed': 0,
            'last_error': None
        }
    
    def _start_worker(self):
        """Start background worker thread if not running"""
        if self.worker_thread is None or not self.worker_thread.is_alive():
            self.is_running = True
            self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
            self.worker_thread.start()
            print("📧 Email worker thread started")
    
    def _process_queue(self):
        """Process emails from queue in background"""
        while self.is_running:
            try:
                # Wait for email with timeout to allow graceful shutdown
                email_task = self.email_queue.get(timeout=5)
                if email_task is None:  # Shutdown signal
                    break
                
                to_email, subject, body, is_html = email_task
                success = self._send_email_sync(to_email, subject, body, is_html)
                
                if success:
                    self.stats['sent'] += 1
                else:
                    self.stats['failed'] += 1
                    
                self.email_queue.task_done()
            except Exception as e:
                # Queue.get timeout - just continue
                if 'Empty' not in str(type(e)):
                    print(f"Email worker error: {e}")
    
    def _send_email_sync(self, to_email, subject, body, is_html=False):
        """Synchronously send an email (used by background worker)"""
        if not self.enabled:
            print("Email service disabled (credentials not set).")
            return False

        try:
            msg = MIMEMultipart()
            msg['From'] = formataddr((self.sender_name, self.sender_email))
            msg['To'] = to_email
            msg['Subject'] = subject

            msg.attach(MIMEText(body, 'html' if is_html else 'plain'))

            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            text = msg.as_string()
            server.sendmail(self.sender_email, to_email, text)
            server.quit()
            print(f"✅ Email sent to {to_email}")
            return True
        except Exception as e:
            print(f"❌ Failed to send email to {to_email}: {e}")
            self.stats['last_error'] = str(e)
            return False
    
    def send_email(self, to_email, subject, body, is_html=False, background=True):
        """
        Send an email - queued for background sending by default.
        
        Args:
            to_email: Recipient email address
            subject: Email subject
            body: Email body (plain text or HTML)
            is_html: Whether body is HTML
            background: If True, queue for async sending. If False, send synchronously.
        """
        if not self.enabled:
            print("Email service disabled (credentials not set).")
            return False
        
        if background:
            # Queue for background sending
            self._start_worker()
            self.email_queue.put((to_email, subject, body, is_html))
            self.stats['queued'] += 1
            print(f"📬 Email queued for {to_email} (queue size: {self.email_queue.qsize()})")
            return True  # Queued successfully
        else:
            # Send synchronously (blocking)
            return self._send_email_sync(to_email, subject, body, is_html)
    
    def send_email_async(self, to_email, subject, body, is_html=False):
        """Explicitly send email in background (alias for send_email with background=True)"""
        return self.send_email(to_email, subject, body, is_html, background=True)
    
    def send_email_sync(self, to_email, subject, body, is_html=False):
        """Explicitly send email synchronously (blocking)"""
        return self.send_email(to_email, subject, body, is_html, background=False)
    
    def get_queue_status(self):
        """Get current email queue status"""
        return {
            'queue_size': self.email_queue.qsize(),
            'worker_running': self.worker_thread.is_alive() if self.worker_thread else False,
            'stats': self.stats
        }
    
    def shutdown(self):
        """Gracefully shutdown the email worker"""
        self.is_running = False
        if self.worker_thread and self.worker_thread.is_alive():
            self.email_queue.put(None)  # Shutdown signal
            self.worker_thread.join(timeout=5)

    def send_candidate_confirmation(self, candidate_email, candidate_name, job_title=None):
        if not candidate_email:
            return False
        
        job_mention = f" for the <strong>{job_title}</strong> position" if job_title else ""
        subject = f"Application Received{' - ' + job_title if job_title else ''} - Next Steps"
        body = f"""
        <html>
        <body>
            <h2>Hi {candidate_name},</h2>
            <p>Thanks for applying{job_mention}! We have successfully received your application.</p>
            <p>Our AI-powered system is currently reviewing your profile. We will get back to you shortly with the next steps.</p>
            <br>
            <p>Best regards,</p>
            <p><strong>{self.sender_name}</strong></p>
        </body>
        </html>
        """
        return self.send_email(candidate_email, subject, body, is_html=True)

    def send_rejection_email(self, candidate_email, candidate_name, job_title=None):
        if not candidate_email:
            return False
        
        job_mention = f" for the <strong>{job_title}</strong> position" if job_title else ""
        subject = f"Update on your application{' - ' + job_title if job_title else ''}"
        body = f"""
        <html>
        <body>
            <h2>Hi {candidate_name},</h2>
            <p>Thank you for your interest in joining our team and for taking the time to apply{job_mention}.</p>
            <p>After careful review of your application and qualifications, we have decided to move forward with other candidates who more closely match our current requirements.</p>
            <p>We will keep your resume on file for future openings that may be a good fit.</p>
            <br>
            <p>We wish you the best in your job search.</p>
            <p>Best regards,</p>
            <p><strong>{self.sender_name}</strong></p>
        </body>
        </html>
        """
        return self.send_email(candidate_email, subject, body, is_html=True)

    def send_interview_invitation(self, candidate_email, candidate_name, interview_details):
        if not candidate_email:
            return False
        
        job_title = interview_details.get('job_title', '')
        job_mention = f" for the <strong>{job_title}</strong> position" if job_title else ""
        subject = f"Interview Invitation{': ' + job_title if job_title else ''} - {interview_details.get('title', 'Interview')}"
        
        # Construct Google Calendar Link
        # Format: https://calendar.google.com/calendar/render?action=TEMPLATE&text={title}&dates={start}/{end}&details={details}&location={location}
        
        title = interview_details.get('title', 'Interview')
        start_time = interview_details.get('start_time') # Expecting ISO string or datetime object
        duration_minutes = int(interview_details.get('duration', 30))
        interview_type = interview_details.get('type', 'Video Call')
        
        # Simple date handling (assuming ISO strings passed from frontend)
        # Frontend sends: 2023-12-28T10:00
        # GCal needs: 20231228T100000Z (UTC)
        # For simplicity, we will trust the frontend to pass the correct UTC strings or handle it here.
        # Let's assume the frontend sends the raw ISO string and we format it for GCal link display.
        
        # Better approach: The link is for the USER to click.
        # But here we are sending an email to the CANDIDATE.
        # The candidate needs a link to ADD to THEIR calendar.
        
        gcal_link = interview_details.get('gcal_link', '#')
        meeting_link = interview_details.get('meeting_link', '')
        
        meeting_link_html = ""
        if meeting_link:
            meeting_link_html = f"""
            <div style="margin-top: 15px; padding: 10px; background-color: #e8f0fe; border-radius: 5px;">
                <strong>Meeting Link:</strong> <a href="{meeting_link}">{meeting_link}</a>
            </div>
            """
        
        body = f"""
        <html>
        <body>
            <h2>Hi {candidate_name},</h2>
            <p>We were impressed with your application{job_mention} and would like to invite you to an interview.</p>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #007bff; margin: 20px 0;">
                {f'<p><strong>Position:</strong> {job_title}</p>' if job_title else ''}
                <p><strong>Topic:</strong> {title}</p>
                <p><strong>Date & Time:</strong> {interview_details.get('date_display')}</p>
                <p><strong>Duration:</strong> {duration_minutes} minutes</p>
                <p><strong>Type:</strong> {interview_type}</p>
                {meeting_link_html}
            </div>
            
            <p>Please click the button below to add this to your Google Calendar and confirm your attendance:</p>
            
            <p>
                <a href="{gcal_link}" style="background-color: #007bff; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">
                    Add to Google Calendar
                </a>
            </p>
            
            <p>If this time doesn't work for you, please reply to this email to reschedule.</p>
            
            <br>
            <p>Best regards,</p>
            <p><strong>{self.sender_name}</strong></p>
        </body>
        </html>
        """
        return self.send_email(candidate_email, subject, body, is_html=True)

    def send_admin_notification(self, candidate_data, base_url=None):
        if not self.admin_email:
            return False
            
        score = candidate_data.get('total_score', 0)
        # Handle different key names
        name = candidate_data.get('candidate_name') or candidate_data.get('name') or 'Unknown'
        email = candidate_data.get('candidate_email') or candidate_data.get('email') or 'N/A'
        phone = candidate_data.get('candidate_phone') or candidate_data.get('phone') or 'N/A'
        
        # Construct Resume URL
        resume_link = candidate_data.get('resume_url')
        file_url = candidate_data.get('file_url')
        
        # Use file_url if resume_url is not set
        if not resume_link and file_url:
            resume_link = file_url
        
        # If it's already a full URL (starts with http), use it directly
        # Otherwise, construct a local file URL with base_url
        if resume_link and not resume_link.startswith('http'):
            if base_url:
                base = base_url.rstrip('/')
                path = resume_link.lstrip('/')
                resume_link = f"{base}/{path}"
        
        # High Score Alert Logic
        if score > 70:
            subject = f"🔥 HIGH SCORE ALERT: {name} ({score}/100)"
            header_color = "#d32f2f" # Red for alert
            header_text = "High Potential Candidate Detected!"
        else:
            subject = f"New Candidate: {name} (Score: {score}/100)"
            header_color = "#2c3e50" # Standard blue/grey
            header_text = "New Application Received"
        
        skills_html = "<ul>"
        for skill in candidate_data.get('skills', []):
            skills_html += f"<li>{skill}</li>"
        skills_html += "</ul>"
        
        body = f"""
        <html>
        <body>
            <h2 style="color: {header_color};">{header_text}</h2>
            <p><strong>Name:</strong> {name}</p>
            <p><strong>Email:</strong> {email}</p>
            <p><strong>Phone:</strong> {phone}</p>
            <p><strong>Total Score:</strong> <span style="font-size: 1.2em; font-weight: bold; color: {header_color};">{score}/100</span></p>
            
            <h3>Skills Detected:</h3>
            {skills_html}
            
            <p><a href="{resume_link}">View Resume</a></p>
        </body>
        </html>
        """
        return self.send_email(self.admin_email, subject, body, is_html=True)
