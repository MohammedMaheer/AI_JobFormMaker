// State management
let currentQuestions = [];
let currentJobTitle = '';

// DOM Elements
const jobForm = document.getElementById('job-form');
const fileInput = document.getElementById('file-input');
const fileUploadArea = document.getElementById('file-upload-area');
const fileInfo = document.getElementById('file-info');
const fileName = document.getElementById('file-name');
const removeFileBtn = document.getElementById('remove-file');
const generateBtn = document.getElementById('generate-btn');

const inputSection = document.getElementById('input-section');
const loadingSection = document.getElementById('loading-section');
const resultsSection = document.getElementById('results-section');
const successSection = document.getElementById('success-section');
const questionsList = document.getElementById('questions-list');

// File Upload Handling
fileUploadArea.addEventListener('click', () => fileInput.click());

fileUploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    fileUploadArea.classList.add('dragover');
});

fileUploadArea.addEventListener('dragleave', () => {
    fileUploadArea.classList.remove('dragover');
});

fileUploadArea.addEventListener('drop', (e) => {
    e.preventDefault();
    fileUploadArea.classList.remove('dragover');
    
    const files = e.dataTransfer.files;
    if (files.length > 0) {
        handleFileSelect(files[0]);
    }
});

fileInput.addEventListener('change', (e) => {
    if (e.target.files.length > 0) {
        handleFileSelect(e.target.files[0]);
    }
});

removeFileBtn.addEventListener('click', () => {
    fileInput.value = '';
    fileUploadArea.style.display = 'block';
    fileInfo.style.display = 'none';
});

function handleFileSelect(file) {
    const allowedTypes = ['.pdf', '.docx', '.txt'];
    const fileExt = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!allowedTypes.includes(fileExt)) {
        showToast('Please upload a PDF, DOCX, or TXT file', 'error');
        return;
    }
    
    if (file.size > 16 * 1024 * 1024) {
        showToast('File size must be less than 16MB', 'error');
        return;
    }
    
    fileName.textContent = file.name;
    fileUploadArea.style.display = 'none';
    fileInfo.style.display = 'flex';
}

// AI Settings Toggle
document.getElementById('ai-settings-toggle').addEventListener('click', () => {
    const content = document.getElementById('ai-settings-content');
    const toggle = document.getElementById('ai-settings-toggle');
    
    if (content.style.display === 'none') {
        content.style.display = 'block';
        toggle.classList.add('active');
    } else {
        content.style.display = 'none';
        toggle.classList.remove('active');
    }
});

// Form Submission
jobForm.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const jobTitle = document.getElementById('job-title').value.trim();
    const jobDescription = document.getElementById('job-description').value.trim();
    const numQuestions = document.getElementById('num-questions').value;
    const questionTypes = document.getElementById('question-types').value;
    const aiProvider = document.getElementById('ai-provider').value;
    const apiKey = document.getElementById('api-key').value.trim();
    const file = fileInput.files[0];
    
    if (!jobTitle) {
        showToast('Please enter a job title', 'error');
        return;
    }
    
    if (!file && !jobDescription) {
        showToast('Please upload a file or enter a job description', 'error');
        return;
    }
    
    // Show loading
    inputSection.style.display = 'none';
    loadingSection.style.display = 'block';
    
    try {
        const formData = new FormData();
        formData.append('job_title', jobTitle);
        formData.append('num_questions', numQuestions);
        formData.append('question_types', questionTypes);
        formData.append('ai_provider', aiProvider);
        if (apiKey) {
            formData.append('api_key', apiKey);
        }
        
        if (file) {
            formData.append('file', file);
        } else {
            formData.append('job_description', jobDescription);
        }
        
        const response = await fetch('/api/process', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        currentQuestions = data.questions;
        currentJobTitle = data.job_title;
        
        displayQuestions(currentQuestions);
        
        loadingSection.style.display = 'none';
        resultsSection.style.display = 'block';
        
        showToast(`Generated ${currentQuestions.length} questions!`, 'success');
        
    } catch (error) {
        loadingSection.style.display = 'none';
        inputSection.style.display = 'block';
        showToast(error.message || 'Failed to generate questions', 'error');
    }
});

// Display Questions
function displayQuestions(questions) {
    questionsList.innerHTML = questions.map((q, index) => `
        <div class="question-item">
            <div class="question-header">
                <span class="question-number">${index + 1}</span>
                <span class="question-text">${escapeHtml(q.question)}</span>
            </div>
            <div class="question-meta">
                <span class="question-tag tag-category">${q.category || 'general'}</span>
                <span class="question-tag tag-difficulty ${q.difficulty || 'medium'}">${q.difficulty || 'medium'}</span>
                ${q.expected_skills ? `<span class="question-skills">${q.expected_skills.slice(0, 3).join(', ')}</span>` : ''}
            </div>
        </div>
    `).join('');
}

// Regenerate Button
document.getElementById('regenerate-btn').addEventListener('click', () => {
    resultsSection.style.display = 'none';
    inputSection.style.display = 'block';
});

// Copy Questions
document.getElementById('copy-btn').addEventListener('click', () => {
    const questionsText = currentQuestions.map((q, i) => 
        `${i + 1}. ${q.question}\n   Category: ${q.category} | Difficulty: ${q.difficulty}`
    ).join('\n\n');
    
    navigator.clipboard.writeText(questionsText).then(() => {
        showToast('Questions copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy questions', 'error');
    });
});

// Download JSON
document.getElementById('download-json-btn').addEventListener('click', () => {
    const data = {
        job_title: currentJobTitle,
        generated_at: new Date().toISOString(),
        questions: currentQuestions
    };
    
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    downloadFile(blob, `interview-questions-${currentJobTitle.toLowerCase().replace(/\s+/g, '-')}.json`);
    showToast('JSON downloaded!', 'success');
});

// Download CSV
document.getElementById('download-csv-btn').addEventListener('click', async () => {
    try {
        const response = await fetch('/api/export/csv', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                questions: currentQuestions,
                job_title: currentJobTitle
            })
        });
        
        if (!response.ok) throw new Error('Export failed');
        
        const blob = await response.blob();
        downloadFile(blob, `interview-questions-${currentJobTitle.toLowerCase().replace(/\s+/g, '-')}.csv`);
        showToast('CSV downloaded! You can open this in Excel or Google Sheets.', 'success');
    } catch (error) {
        showToast('Failed to export CSV', 'error');
    }
});

// Download TXT
document.getElementById('download-txt-btn').addEventListener('click', async () => {
    try {
        const response = await fetch('/api/export/txt', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                questions: currentQuestions,
                job_title: currentJobTitle
            })
        });
        
        if (!response.ok) throw new Error('Export failed');
        
        const blob = await response.blob();
        downloadFile(blob, `interview-questions-${currentJobTitle.toLowerCase().replace(/\s+/g, '-')}.txt`);
        showToast('Text file downloaded!', 'success');
    } catch (error) {
        showToast('Failed to export text file', 'error');
    }
});

// Helper function to download files
function downloadFile(blob, filename) {
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// Send to Zapier
document.getElementById('send-zapier-btn').addEventListener('click', async () => {
    const webhookUrl = document.getElementById('zapier-webhook').value.trim();
    
    if (!webhookUrl) {
        showToast('Please enter your Webhook URL', 'error');
        return;
    }
    
    // Allow both Zapier and Google Apps Script URLs
    if (!webhookUrl.includes('hooks.zapier.com') && !webhookUrl.includes('script.google.com')) {
        showToast('Please enter a valid Zapier or Google Apps Script URL', 'error');
        return;
    }
    
    const btn = document.getElementById('send-zapier-btn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';
    
    try {
        const response = await fetch('/api/send-to-zapier', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                questions: currentQuestions,
                job_title: currentJobTitle,
                webhook_url: webhookUrl
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Show success
        document.getElementById('success-message').innerHTML = data.message;
        resultsSection.style.display = 'none';
        successSection.style.display = 'block';
        
        // Save webhook URL to history
        saveWebhookUrl(webhookUrl);
        
        showToast('Sent successfully!', 'success');
        
    } catch (error) {
        showToast(error.message || 'Failed to send', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-paper-plane"></i> Save to Sheets';
    }
});

// Back to results
document.getElementById('back-to-results-btn').addEventListener('click', () => {
    successSection.style.display = 'none';
    resultsSection.style.display = 'block';
});

// New questions from success
document.getElementById('new-questions-btn').addEventListener('click', () => {
    resetForm();
});

// Start Over
document.getElementById('start-over-btn').addEventListener('click', () => {
    resetForm();
});

// Create Job Application Form
document.getElementById('create-application-form-btn').addEventListener('click', async () => {
    const webhookUrl = document.getElementById('zapier-webhook-form').value.trim();
    const companyName = document.getElementById('company-name').value.trim();
    
    if (!webhookUrl) {
        showToast('Please enter your Webhook URL', 'error');
        return;
    }
    
    if (!webhookUrl.includes('hooks.zapier.com') && !webhookUrl.includes('script.google.com')) {
        showToast('Please enter a valid Zapier or Google Apps Script URL', 'error');
        return;
    }
    
    const btn = document.getElementById('create-application-form-btn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Creating Form...';
    
    try {
        const response = await fetch('/api/send-to-zapier', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                questions: currentQuestions,
                job_title: currentJobTitle,
                webhook_url: webhookUrl,
                form_type: 'application_form',
                company_name: companyName
            })
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Show success
        document.getElementById('success-message').innerHTML = data.message;
        resultsSection.style.display = 'none';
        successSection.style.display = 'block';
        
        // Save webhook URL to history
        saveWebhookUrl(webhookUrl);
        
        showToast('Job application form created!', 'success');
        
    } catch (error) {
        showToast(error.message || 'Failed to create application form', 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fab fa-wpforms"></i> Create Job Application Form';
    }
});

// Google Forms help link
document.getElementById('zapier-form-help-link').addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('forms-modal').classList.add('active');
});

// Close forms modal
document.getElementById('close-forms').addEventListener('click', () => {
    document.getElementById('forms-modal').classList.remove('active');
});

function resetForm() {
    currentQuestions = [];
    currentJobTitle = '';
    jobForm.reset();
    fileUploadArea.style.display = 'block';
    fileInfo.style.display = 'none';
    document.getElementById('zapier-webhook').value = '';
    document.getElementById('zapier-webhook-form').value = '';
    document.getElementById('company-name').value = '';
    
    successSection.style.display = 'none';
    resultsSection.style.display = 'none';
    inputSection.style.display = 'block';
}

// Modal Handling
document.getElementById('help-link').addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('help-modal').classList.add('active');
});

document.getElementById('zapier-setup-link').addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('zapier-modal').classList.add('active');
});

document.getElementById('zapier-help-link').addEventListener('click', (e) => {
    e.preventDefault();
    document.getElementById('zapier-modal').classList.add('active');
});

// Google Apps Script Modal
const openGasModal = (e) => {
    e.preventDefault();
    document.getElementById('gas-modal').classList.add('active');
};

const gasHelpLink = document.getElementById('gas-help-link');
if (gasHelpLink) gasHelpLink.addEventListener('click', openGasModal);

const gasFormHelpLink = document.getElementById('gas-form-help-link');
if (gasFormHelpLink) gasFormHelpLink.addEventListener('click', openGasModal);

document.getElementById('close-gas').addEventListener('click', () => {
    document.getElementById('gas-modal').classList.remove('active');
});

// Copy Code Button
document.getElementById('copy-gas-code').addEventListener('click', () => {
    const code = document.getElementById('gas-code').textContent;
    navigator.clipboard.writeText(code).then(() => {
        showToast('Code copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy code', 'error');
    });
});

document.getElementById('close-help').addEventListener('click', () => {
    document.getElementById('help-modal').classList.remove('active');
});

document.getElementById('close-zapier').addEventListener('click', () => {
    document.getElementById('zapier-modal').classList.remove('active');
});

// Close modal on outside click
document.querySelectorAll('.modal').forEach(modal => {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.classList.remove('active');
        }
    });
});

// Webhook History Management
function saveWebhookUrl(url) {
    if (!url) return;
    
    let history = JSON.parse(localStorage.getItem('webhookHistory') || '[]');
    
    // Remove if exists (to move to top)
    history = history.filter(item => item !== url);
    
    // Add to top
    history.unshift(url);
    
    // Keep max 5
    if (history.length > 5) history.pop();
    
    localStorage.setItem('webhookHistory', JSON.stringify(history));
    updateWebhookDatalist();
}

function updateWebhookDatalist() {
    const history = JSON.parse(localStorage.getItem('webhookHistory') || '[]');
    const datalist = document.getElementById('webhook-history');
    if (!datalist) return;
    
    datalist.innerHTML = '';
    history.forEach(url => {
        const option = document.createElement('option');
        option.value = url;
        datalist.appendChild(option);
    });
    
    // Auto-fill inputs if empty and history exists
    if (history.length > 0) {
        const inputs = ['zapier-webhook', 'zapier-webhook-form'];
        inputs.forEach(id => {
            const input = document.getElementById(id);
            if (input && !input.value) {
                input.value = history[0];
            }
        });
    }
}

// Initialize history on load
document.addEventListener('DOMContentLoaded', () => {
    updateWebhookDatalist();
});

// Toast Notifications
function showToast(message, type = 'info') {
    let container = document.querySelector('.toast-container');
    if (!container) {
        container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
    }
    
    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    toast.innerHTML = `
        <i class="fas ${type === 'success' ? 'fa-check-circle' : type === 'error' ? 'fa-exclamation-circle' : 'fa-info-circle'}"></i>
        <span>${message}</span>
    `;
    
    container.appendChild(toast);
    
    setTimeout(() => {
        toast.style.animation = 'slideIn 0.3s ease reverse';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

// Utility Functions
function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}
