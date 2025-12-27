// State management
let currentQuestions = [];
let currentJobTitle = '';
let currentJobDescription = '';
let uploadedCandidates = [];

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
        currentJobDescription = data.job_description || jobDescription || 'Job requirements'; // Store for candidate scoring
        
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
        
        // Show success with form link if available
        let successMsg = 'Job application form created successfully!';
        if (data.formUrl) {
            successMsg += `<br><br><a href="${data.formUrl}" target="_blank" class="btn btn-success btn-lg" style="margin-top: 20px;">
                <i class="fab fa-wpforms"></i> Open Google Form
            </a>`;
        } else {
            successMsg += '<br><br>Check your Google Forms dashboard.';
        }
        
        document.getElementById('success-message').innerHTML = successMsg;
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
    
    // Display full webhook URL
    const webhookDisplay = document.getElementById('webhook-url-display');
    if (webhookDisplay) {
        webhookDisplay.textContent = `${window.location.origin}/api/webhook/application`;
    }
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

// ========== CANDIDATE SCORING FUNCTIONALITY ==========

// Candidate Upload Handling
const candidateUploadArea = document.getElementById('candidate-upload-area');
const candidateFileInput = document.getElementById('candidate-file-input');
const candidatesList = document.getElementById('candidates-list');
const candidatesContainer = document.getElementById('candidates-container');
const candidateCount = document.getElementById('candidate-count');

if (candidateUploadArea) {
    candidateUploadArea.addEventListener('click', () => candidateFileInput.click());
    
    candidateUploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        candidateUploadArea.classList.add('dragover');
    });
    
    candidateUploadArea.addEventListener('dragleave', () => {
        candidateUploadArea.classList.remove('dragover');
    });
    
    candidateUploadArea.addEventListener('drop', async (e) => {
        e.preventDefault();
        candidateUploadArea.classList.remove('dragover');
        
        const files = Array.from(e.dataTransfer.files);
        for (const file of files) {
            await uploadCandidateResume(file);
        }
    });
    
    candidateFileInput.addEventListener('change', async (e) => {
        const files = Array.from(e.target.files);
        for (const file of files) {
            await uploadCandidateResume(file);
        }
        e.target.value = ''; // Reset input
    });
}

async function uploadCandidateResume(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        showToast(`Uploading ${file.name}...`, 'info');
        
        const response = await fetch('/api/upload-resume', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.error) {
            throw new Error(data.error);
        }
        
        // Add to uploaded candidates
        uploadedCandidates.push({
            filename: file.name,
            info: data.candidate_info
        });
        
        updateCandidatesList();
        showToast(`${file.name} uploaded successfully!`, 'success');
        
    } catch (error) {
        showToast(`Failed to upload ${file.name}: ${error.message}`, 'error');
    }
}

function updateCandidatesList() {
    if (uploadedCandidates.length === 0) {
        candidatesList.style.display = 'none';
        return;
    }
    
    candidatesList.style.display = 'block';
    candidateCount.textContent = uploadedCandidates.length;
    
    candidatesContainer.innerHTML = uploadedCandidates.map((candidate, index) => `
        <div class="candidate-item">
            <div class="candidate-info">
                <i class="fas fa-file-alt"></i>
                <div>
                    <strong>${candidate.info.name || candidate.filename}</strong>
                    <small>${candidate.info.email || 'Email not found'}</small>
                </div>
            </div>
            <button class="btn-remove" onclick="removeCandidate(${index})">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `).join('');
}

function removeCandidate(index) {
    uploadedCandidates.splice(index, 1);
    updateCandidatesList();
    
    // Hide results if no candidates
    if (uploadedCandidates.length === 0) {
        document.getElementById('candidates-results').style.display = 'none';
    }
}

// Fetch Applications
document.getElementById('fetch-candidates-btn')?.addEventListener('click', async () => {
    const btn = document.getElementById('fetch-candidates-btn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Fetching...';
    
    try {
        const response = await fetch('/api/candidates');
        const data = await response.json();
        
        if (data.candidates && data.candidates.length > 0) {
            // Rank candidates
            const rankResponse = await fetch('/api/rank-candidates', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ candidates: data.candidates })
            });
            
            const rankData = await rankResponse.json();
            
            if (rankData.success) {
                displayRankedCandidates(rankData.ranked_candidates);
                showToast(`Fetched ${data.candidates.length} applications!`, 'success');
            }
        } else {
            showToast('No applications found.', 'info');
        }
    } catch (error) {
        showToast(`Failed to fetch candidates: ${error.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-sync"></i> Fetch Applications from Webhook';
    }
});

// Score All Candidates
document.getElementById('score-all-btn')?.addEventListener('click', async () => {
    if (uploadedCandidates.length === 0) {
        // If no uploads, try fetching only
        document.getElementById('fetch-candidates-btn').click();
        return;
    }
    
    if (!currentJobDescription || !currentJobTitle) {
        showToast('Please generate interview questions first to set job requirements', 'error');
        return;
    }
    
    const btn = document.getElementById('score-all-btn');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Scoring...';
    
    try {
        let allScoredCandidates = [];
        
        // 1. Score uploaded candidates
        for (const candidate of uploadedCandidates) {
            const response = await fetch('/api/score-candidate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    candidate_info: candidate.info,
                    job_description: currentJobDescription,
                    job_title: currentJobTitle
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                allScoredCandidates.push(data.score);
            }
        }
        
        // 2. Fetch stored candidates
        try {
            const storedResponse = await fetch('/api/candidates');
            const storedData = await storedResponse.json();
            if (storedData.candidates) {
                allScoredCandidates = [...allScoredCandidates, ...storedData.candidates];
            }
        } catch (e) {
            console.log("Could not fetch stored candidates", e);
        }
        
        if (allScoredCandidates.length === 0) {
            showToast('No candidates to rank', 'warning');
            return;
        }

        // 3. Rank all
        const rankResponse = await fetch('/api/rank-candidates', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ candidates: allScoredCandidates })
        });
        
        const rankData = await rankResponse.json();
        
        if (rankData.success) {
            displayRankedCandidates(rankData.ranked_candidates);
            showToast('Candidates scored and ranked successfully!', 'success');
        }
        
    } catch (error) {
        showToast(`Failed to score candidates: ${error.message}`, 'error');
    } finally {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-calculator"></i> Score All Candidates';
    }
});

function displayRankedCandidates(rankedCandidates) {
    const resultsContainer = document.getElementById('ranked-candidates-container');
    const resultsSection = document.getElementById('candidates-results');
    
    resultsSection.style.display = 'block';
    
    resultsContainer.innerHTML = rankedCandidates.map(candidate => {
        const gradeClass = candidate.grade === 'A' ? 'grade-a' : 
                          candidate.grade === 'B' ? 'grade-b' :
                          candidate.grade === 'C' ? 'grade-c' : 'grade-d';
        
        // AI Analysis Section
        let aiSection = '';
        if (candidate.ai_analysis) {
            aiSection = `
                <div class="ai-analysis-section">
                    <h5><i class="fas fa-robot"></i> AI Analysis</h5>
                    <div class="ai-summary">
                        <strong>Summary:</strong> ${candidate.ai_analysis.summary}
                    </div>
                    <div class="ai-pros-cons">
                        <div class="ai-pros">
                            <h6><i class="fas fa-check text-success"></i> Pros</h6>
                            <ul>
                                ${candidate.ai_analysis.pros.map(p => `<li>${p}</li>`).join('')}
                            </ul>
                        </div>
                        <div class="ai-cons">
                            <h6><i class="fas fa-times text-danger"></i> Cons</h6>
                            <ul>
                                ${candidate.ai_analysis.cons.map(c => `<li>${c}</li>`).join('')}
                            </ul>
                        </div>
                    </div>
                    ${candidate.ai_analysis.adjustment ? `
                        <div class="ai-adjustment">
                            <small>AI Score Adjustment: <span class="${candidate.ai_analysis.adjustment >= 0 ? 'text-success' : 'text-danger'}">${candidate.ai_analysis.adjustment > 0 ? '+' : ''}${candidate.ai_analysis.adjustment}</span></small>
                        </div>
                    ` : ''}
                </div>
            `;
        }

        return `
            <div class="candidate-score-card">
                <div class="candidate-rank">
                    <div class="rank-badge ${candidate.rank <= 3 ? 'top-rank' : ''}">
                        #${candidate.rank}
                    </div>
                </div>
                <div class="candidate-details">
                    <h4>${candidate.candidate_name}</h4>
                    <p class="candidate-email">${candidate.candidate_email}</p>
                </div>
                <div class="candidate-score">
                    <div class="score-circle ${gradeClass}">
                        <span class="score-value">${candidate.total_score}</span>
                        <span class="score-grade">${candidate.grade}</span>
                    </div>
                </div>
                <div class="score-breakdown">
                    <h5>Score Breakdown:</h5>
                    <div class="breakdown-grid">
                        <div class="breakdown-item">
                            <span class="breakdown-label">Skills Match</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${candidate.breakdown.skills_match}%"></div>
                            </div>
                            <span class="breakdown-value">${candidate.breakdown.skills_match}%</span>
                        </div>
                        <div class="breakdown-item">
                            <span class="breakdown-label">Experience</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${candidate.breakdown.experience}%"></div>
                            </div>
                            <span class="breakdown-value">${candidate.breakdown.experience}%</span>
                        </div>
                        <div class="breakdown-item">
                            <span class="breakdown-label">Education</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${candidate.breakdown.education}%"></div>
                            </div>
                            <span class="breakdown-value">${candidate.breakdown.education}%</span>
                        </div>
                        <div class="breakdown-item">
                            <span class="breakdown-label">Keywords</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${candidate.breakdown.keywords}%"></div>
                            </div>
                            <span class="breakdown-value">${candidate.breakdown.keywords}%</span>
                        </div>
                        <div class="breakdown-item">
                            <span class="breakdown-label">Certifications</span>
                            <div class="progress-bar">
                                <div class="progress-fill" style="width: ${candidate.breakdown.certifications}%"></div>
                            </div>
                            <span class="breakdown-value">${candidate.breakdown.certifications}%</span>
                        </div>
                    </div>
                    
                    ${aiSection}
                    
                    <div class="feedback-section">
                        <h5>Feedback:</h5>
                        <ul class="feedback-list">
                            ${candidate.feedback.map(f => `<li>${f}</li>`).join('')}
                        </ul>
                    </div>
                </div>
            </div>
        `;
    }).join('');
    
    // Scroll to results
    resultsSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
}
