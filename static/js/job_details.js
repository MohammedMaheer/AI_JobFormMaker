
// Global variables
let currentCandidates = [];
let isKanbanView = false;
let currentJobTitle = null; // Store job title for emails

// Helper function to ensure LinkedIn URL has proper protocol
function formatLinkedInUrl(url) {
    if (!url) return '';
    url = url.trim();
    if (url.startsWith('http://') || url.startsWith('https://')) {
        return url;
    }
    return 'https://' + url;
}

// DOM Elements
const candidatesList = document.getElementById('candidates-list');
const resultsSection = document.getElementById('results-section');
const kanbanSection = document.getElementById('kanban-section');
const refreshBtn = document.getElementById('refresh-btn');
const viewToggleBtn = document.getElementById('view-toggle-btn');
const jobTitleElement = document.getElementById('job-title');
const jobMetaElement = document.getElementById('job-meta');

// Modal Elements
const candidateModal = document.getElementById('candidate-modal');
const modalCandidateName = document.getElementById('modal-candidate-name');
const modalCandidateBody = document.getElementById('modal-candidate-body');
const closeCandidateModal = document.getElementById('close-candidate-modal');

// Schedule Modal Elements
const scheduleModal = document.getElementById('scheduleModal');
const closeScheduleBtn = scheduleModal.querySelector('.close');
const generateGCalBtn = document.getElementById('generateGCal');
const copyLinkBtn = document.getElementById('copyLink');
const rejectCandidateBtn = document.getElementById('rejectCandidateBtn');
let currentScheduleCandidateId = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    loadJobDetails();
    loadCandidates();
    
    // Event Listeners
    if (refreshBtn) refreshBtn.addEventListener('click', loadCandidates);
    
    if (viewToggleBtn) {
        viewToggleBtn.addEventListener('click', toggleView);
    }
    
    if (closeCandidateModal) {
        closeCandidateModal.addEventListener('click', () => {
            candidateModal.classList.remove('active');
        });
    }

    window.addEventListener('click', (e) => {
        if (e.target === candidateModal) {
            candidateModal.classList.remove('active');
        }
        if (e.target === scheduleModal) {
            scheduleModal.style.display = "none";
        }
    });
    
    if (closeScheduleBtn) {
        closeScheduleBtn.onclick = function() {
            scheduleModal.style.display = "none";
        }
    }
    
    // Search & Filter Event Listeners
    initializeFilters();
});

// Filter state
let filterState = {
    search: '',
    scoreMin: null,
    scoreMax: null,
    status: '',
    tag: ''
};

function initializeFilters() {
    const searchInput = document.getElementById('search-input');
    const scoreMin = document.getElementById('score-min');
    const scoreMax = document.getElementById('score-max');
    const statusFilter = document.getElementById('status-filter');
    const tagFilter = document.getElementById('tag-filter');
    const clearBtn = document.getElementById('clear-filters-btn');
    
    if (searchInput) {
        searchInput.addEventListener('input', debounce((e) => {
            filterState.search = e.target.value.toLowerCase();
            applyFilters();
        }, 300));
    }
    
    if (scoreMin) {
        scoreMin.addEventListener('input', () => {
            filterState.scoreMin = scoreMin.value ? parseInt(scoreMin.value) : null;
            applyFilters();
        });
    }
    
    if (scoreMax) {
        scoreMax.addEventListener('input', () => {
            filterState.scoreMax = scoreMax.value ? parseInt(scoreMax.value) : null;
            applyFilters();
        });
    }
    
    if (statusFilter) {
        statusFilter.addEventListener('change', () => {
            filterState.status = statusFilter.value;
            applyFilters();
        });
    }
    
    if (tagFilter) {
        tagFilter.addEventListener('change', () => {
            filterState.tag = tagFilter.value;
            applyFilters();
        });
    }
    
    if (clearBtn) {
        clearBtn.addEventListener('click', clearFilters);
    }
}

function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}

function clearFilters() {
    filterState = { search: '', scoreMin: null, scoreMax: null, status: '', tag: '' };
    
    const searchInput = document.getElementById('search-input');
    const scoreMin = document.getElementById('score-min');
    const scoreMax = document.getElementById('score-max');
    const statusFilter = document.getElementById('status-filter');
    const tagFilter = document.getElementById('tag-filter');
    
    if (searchInput) searchInput.value = '';
    if (scoreMin) scoreMin.value = '';
    if (scoreMax) scoreMax.value = '';
    if (statusFilter) statusFilter.value = '';
    if (tagFilter) tagFilter.value = '';
    
    applyFilters();
}

function applyFilters() {
    let filtered = [...currentCandidates];
    
    // Search filter (name, email, skills)
    if (filterState.search) {
        filtered = filtered.filter(c => {
            const name = (c.candidate_name || c.name || '').toLowerCase();
            const email = (c.candidate_email || c.email || '').toLowerCase();
            const skills = (c.ai_analysis?.summary || c.feedback || '').toLowerCase();
            const tags = (c.tags || []).join(' ').toLowerCase();
            return name.includes(filterState.search) || 
                   email.includes(filterState.search) || 
                   skills.includes(filterState.search) ||
                   tags.includes(filterState.search);
        });
    }
    
    // Score range filter
    if (filterState.scoreMin !== null) {
        filtered = filtered.filter(c => (c.total_score || 0) >= filterState.scoreMin);
    }
    if (filterState.scoreMax !== null) {
        filtered = filtered.filter(c => (c.total_score || 0) <= filterState.scoreMax);
    }
    
    // Status filter
    if (filterState.status) {
        filtered = filtered.filter(c => {
            let status = c.status || 'applied';
            if (status === 'processed' || status === 'pending') status = 'applied';
            return status === filterState.status;
        });
    }
    
    // Tag filter
    if (filterState.tag) {
        filtered = filtered.filter(c => (c.tags || []).includes(filterState.tag));
    }
    
    // Update display
    if (isKanbanView) {
        renderKanbanBoard(filtered);
    } else {
        displayResults(filtered);
    }
    
    // Show filter results count
    updateFilterResultsCount(filtered.length, currentCandidates.length);
}

function updateFilterResultsCount(shown, total) {
    const existingBadge = document.getElementById('filter-results-badge');
    if (existingBadge) existingBadge.remove();
    
    if (shown !== total) {
        const badge = document.createElement('span');
        badge.id = 'filter-results-badge';
        badge.style.cssText = 'background: var(--primary-color); color: white; padding: 4px 10px; border-radius: 20px; font-size: 0.85rem; margin-left: 10px;';
        badge.textContent = `Showing ${shown} of ${total}`;
        
        const header = document.querySelector('.card-header h2');
        if (header) header.appendChild(badge);
    }
}

function updateTagFilter() {
    const tagFilter = document.getElementById('tag-filter');
    if (!tagFilter) return;
    
    // Collect all unique tags
    const allTags = new Set();
    currentCandidates.forEach(c => {
        (c.tags || []).forEach(tag => allTags.add(tag));
    });
    
    // Keep current selection
    const currentValue = tagFilter.value;
    
    // Rebuild options
    tagFilter.innerHTML = '<option value="">All Tags</option>';
    Array.from(allTags).sort().forEach(tag => {
        const option = document.createElement('option');
        option.value = tag;
        option.textContent = tag;
        if (tag === currentValue) option.selected = true;
        tagFilter.appendChild(option);
    });
}

async function loadJobDetails() {
    try {
        const response = await fetch(`/api/jobs/${JOB_ID}`);
        const data = await response.json();
        
        if (data.job) {
            currentJobTitle = data.job.title; // Store for email use
            jobTitleElement.textContent = data.job.title;
            jobMetaElement.innerHTML = `
                <i class="far fa-calendar-alt"></i> Created: ${new Date(data.job.created_at).toLocaleDateString()} 
                <span class="status-badge status-${data.job.status}" style="margin-left: 10px;">${data.job.status}</span>
            `;
            
            const descElement = document.getElementById('job-description');
            if (descElement) {
                descElement.innerHTML = data.job.description || 'No description provided.';
            }
            
            // Handle Form Link
            const formLink = document.getElementById('form-link');
            if (formLink && data.job.form_url) {
                formLink.href = data.job.form_url;
                formLink.style.display = 'inline-flex';
            }

            // Handle Edit Link
            const editLink = document.getElementById('edit-form-link');
            if (editLink && data.job.edit_url) {
                editLink.href = data.job.edit_url;
                editLink.style.display = 'inline-flex';
            }

            // Handle Close Job Button
            const closeBtn = document.getElementById('close-job-btn');
            if (closeBtn && data.job.status === 'active') {
                closeBtn.style.display = 'inline-flex';
                closeBtn.onclick = () => closeJob(data.job.id);
            }

            // Handle Delete Job Button
            const deleteBtn = document.getElementById('delete-job-btn');
            if (deleteBtn) {
                deleteBtn.style.display = 'inline-flex';
                deleteBtn.onclick = () => deleteJob(data.job.id);
            }
        }
    } catch (error) {
        console.error('Error loading job details:', error);
    }
}

async function closeJob(jobId) {
    if (!confirm('Are you sure you want to close this job? New applications will no longer be processed.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/jobs/${jobId}/close`, { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            alert('Job closed successfully.');
            window.location.reload();
        } else {
            alert('Error closing job: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to close job.');
    }
}

async function deleteJob(jobId) {
    if (!confirm('Are you sure you want to DELETE this job? This will also delete all candidate data associated with it. This action cannot be undone.')) {
        return;
    }
    
    try {
        const response = await fetch(`/api/jobs/${jobId}`, { method: 'DELETE' });
        const data = await response.json();
        
        if (data.success) {
            alert('Job deleted successfully.');
            window.location.href = '/'; // Redirect to dashboard
        } else {
            alert('Error deleting job: ' + data.error);
        }
    } catch (error) {
        console.error('Error:', error);
        alert('Failed to delete job.');
    }
}

// Toggle description expand/collapse
const toggleDescBtn = document.getElementById('toggle-desc-btn');
const jobDescElement = document.getElementById('job-description');

if (toggleDescBtn && jobDescElement) {
    toggleDescBtn.addEventListener('click', () => {
        const isCollapsed = jobDescElement.classList.contains('collapsed');
        if (isCollapsed) {
            jobDescElement.classList.remove('collapsed');
            jobDescElement.classList.add('expanded');
            toggleDescBtn.innerHTML = '<i class="fas fa-chevron-up"></i> Hide Description';
        } else {
            jobDescElement.classList.add('collapsed');
            jobDescElement.classList.remove('expanded');
            toggleDescBtn.innerHTML = '<i class="fas fa-chevron-down"></i> View Full Description';
        }
    });
}

async function loadCandidates() {
    if (refreshBtn) {
        refreshBtn.disabled = true;
        refreshBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Loading...';
    }
    
    try {
        const response = await fetch(`/api/jobs/${JOB_ID}/candidates`);
        const data = await response.json();
        
        if (data.candidates) {
            // Sort by score descending
            const sorted = data.candidates.sort((a, b) => (b.total_score || 0) - (a.total_score || 0));
            currentCandidates = sorted;
            
            // Update tag filter dropdown with available tags
            updateTagFilter();
            
            // Apply any active filters
            applyFilters();
        } else {
            currentCandidates = [];
            displayResults([]);
        }
    } catch (error) {
        console.error('Error loading candidates:', error);
        alert('Failed to load candidates.');
    } finally {
        if (refreshBtn) {
            refreshBtn.disabled = false;
            refreshBtn.innerHTML = '<i class="fas fa-sync-alt"></i> Refresh Candidates';
        }
    }
}

function toggleView() {
    isKanbanView = !isKanbanView;
    if (isKanbanView) {
        resultsSection.style.display = 'none';
        kanbanSection.style.display = 'block';
        viewToggleBtn.innerHTML = '<i class="fas fa-list"></i> List View';
        renderKanbanBoard(currentCandidates);
    } else {
        resultsSection.style.display = 'block';
        kanbanSection.style.display = 'none';
        viewToggleBtn.innerHTML = '<i class="fas fa-columns"></i> Kanban View';
        displayResults(currentCandidates);
    }
}

function displayResults(candidates) {
    resultsSection.style.display = 'block';
    candidatesList.innerHTML = '';
    
    if (candidates.length === 0) {
        candidatesList.innerHTML = '<div class="empty-state"><i class="fas fa-users" style="font-size: 3rem; color: var(--text-secondary); margin-bottom: 1rem;"></i><p>No candidates found yet.</p></div>';
        return;
    }
    
    const pendingIds = [];

    candidates.forEach((candidate, index) => {
        let scoreClass = candidate.total_score >= 80 ? 'score-high' : 
                         candidate.total_score >= 60 ? 'score-medium' : 'score-low';
        
        let scoreDisplay = `${candidate.total_score || 0}% Match`;
        let actionButton = `<button class="btn btn-sm btn-outline-primary schedule-btn" 
                            onclick="event.stopPropagation(); openScheduleModal('${(candidate.candidate_name || candidate.name || '').replace(/'/g, "\\'")}', '${(candidate.candidate_email || candidate.email || '').replace(/'/g, "\\'")}', '${candidate.id}')"
                            style="font-size: 0.8rem; padding: 0.25rem 0.5rem; background: transparent; border: 1px solid var(--primary-color); color: var(--primary-color); border-radius: 4px; cursor: pointer;">
                        <i class="far fa-calendar-alt"></i> Schedule
                    </button>`;

        // Handle Pending/Processing State
        const isPending = candidate.status === 'pending' || (candidate.total_score === 0 && (!candidate.ai_analysis || (candidate.ai_analysis.summary && candidate.ai_analysis.summary.includes('Pending'))));

        if (isPending) {
            scoreClass = 'score-medium';
            scoreDisplay = '<i class="fas fa-clock"></i> Pending';
            actionButton = `<button class="btn btn-sm btn-warning" 
                            onclick="event.stopPropagation(); processCandidate('${candidate.id}')"
                            style="font-size: 0.8rem; padding: 0.25rem 0.5rem; border-radius: 4px; cursor: pointer;">
                        <i class="fas fa-cog fa-spin"></i> Processing...
                    </button>`;
            pendingIds.push(candidate.id);
        } else if (candidate.parsing_failed) {
            scoreClass = 'score-medium';
            scoreDisplay = '<i class="fas fa-exclamation-triangle"></i> Manual Review';
        }
        
        const card = document.createElement('div');
        card.className = 'candidate-card';
        card.style.cursor = 'pointer';
        
        card.addEventListener('click', (e) => {
            if (e.target.closest('a') || e.target.closest('button')) return;
            openCandidateModal(candidate);
        });
        
        card.innerHTML = `
            <div class="candidate-header">
                <div>
                    <h4>#${index + 1} ${candidate.candidate_name || candidate.name || 'Unknown Candidate'}</h4>
                    <div style="font-size: 0.9rem; color: var(--text-secondary); margin-top: 5px;">
                        <i class="fas fa-envelope"></i> ${candidate.candidate_email || candidate.email || 'N/A'}
                    </div>
                    <div style="font-size: 0.9rem; color: var(--text-secondary); margin-top: 2px;">
                        <i class="fas fa-phone"></i> ${candidate.candidate_phone || candidate.phone || 'N/A'}
                    </div>
                </div>
                <div style="display: flex; flex-direction: column; align-items: flex-end; gap: 10px;">
                    <span class="score-badge ${scoreClass}">${scoreDisplay}</span>
                    ${actionButton}
                </div>
            </div>
            <div class="candidate-details">
                <div class="detail-item">
                    <label>Skills</label>
                    <span>${candidate.breakdown?.skills_match || 0}%</span>
                </div>
                <div class="detail-item">
                    <label>Experience</label>
                    <span>${candidate.breakdown?.experience || 0}%</span>
                </div>
                <div class="detail-item">
                    <label>Education</label>
                    <span>${candidate.breakdown?.education || 0}%</span>
                </div>
            </div>
            <div class="ai-feedback" style="max-height: 80px; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;">
                <strong>Summary:</strong> ${candidate.ai_analysis?.summary || candidate.feedback || 'No feedback available.'}
            </div>
            <div style="margin-top: 10px; text-align: center; color: var(--primary-color); font-size: 0.9rem; font-weight: 500;">
                Click to view full details
            </div>
        `;
        candidatesList.appendChild(card);
    });

    // Auto-process pending candidates (with delay to let backend finish first)
    if (pendingIds.length > 0) {
        console.log('Found pending candidates, will check status in 5 seconds:', pendingIds);
        // Delay auto-processing to give webhook background thread time to finish
        setTimeout(() => {
            console.log('Checking pending candidates for processing...');
            processPendingQueue(pendingIds);
        }, 5000);
    }
}

function renderKanbanBoard(candidates) {
    const cols = {
        'applied': document.getElementById('list-applied'),
        'interview_scheduled': document.getElementById('list-interview'),
        'rejected': document.getElementById('list-rejected')
    };
    
    // Clear columns
    Object.values(cols).forEach(col => {
        if(col) col.innerHTML = '';
    });
    
    // Reset counts
    const counts = { 'applied': 0, 'interview_scheduled': 0, 'rejected': 0 };

    candidates.forEach(candidate => {
        // Map 'processed' and 'pending' to 'applied' for Kanban display
        let status = candidate.status || 'applied';
        if (status === 'processed' || status === 'pending') {
            status = 'applied';
        }
        
        if (cols[status]) {
            const card = createKanbanCard(candidate);
            cols[status].appendChild(card);
            counts[status]++;
        }
    });

    // Update badges
    const countApplied = document.getElementById('count-applied');
    const countInterview = document.getElementById('count-interview');
    const countRejected = document.getElementById('count-rejected');
    
    if(countApplied) countApplied.textContent = counts['applied'];
    if(countInterview) countInterview.textContent = counts['interview_scheduled'];
    if(countRejected) countRejected.textContent = counts['rejected'];
}

function createKanbanCard(candidate) {
    const div = document.createElement('div');
    div.className = 'kanban-card';
    div.draggable = true;
    div.id = `card-${candidate.id}`;
    div.ondragstart = (e) => drag(e, candidate);
    
    // Click to open details
    div.onclick = (e) => {
        if (!e.target.closest('button')) openCandidateModal(candidate);
    };

    let scoreClass = candidate.total_score >= 80 ? 'score-high' : 
                     candidate.total_score >= 60 ? 'score-medium' : 'score-low';
    
    div.innerHTML = `
        <div class="kanban-card-header">
            <div class="kanban-card-title">${candidate.candidate_name || candidate.name}</div>
            <div class="kanban-card-score ${scoreClass}">${candidate.total_score || 0}%</div>
        </div>
        <div class="kanban-card-details">
            <div><i class="fas fa-envelope"></i> ${candidate.candidate_email || candidate.email || 'N/A'}</div>
            <div><i class="fas fa-briefcase"></i> Exp: ${candidate.breakdown?.experience || 0}%</div>
        </div>
        <div class="kanban-card-footer">
            <div class="kanban-card-date">${new Date(candidate.timestamp).toLocaleDateString()}</div>
        </div>
    `;
    return div;
}

// Drag and Drop Functions
let draggedCandidate = null;

function drag(ev, candidate) {
    draggedCandidate = candidate;
    ev.dataTransfer.setData("text", ev.target.id);
    ev.target.classList.add('dragging');
}

function allowDrop(ev) {
    ev.preventDefault();
    const col = ev.target.closest('.kanban-column');
    if (col) {
        col.classList.add('drag-over');
    }
}

// Remove drag-over style when leaving
document.addEventListener('dragleave', (e) => {
    if (e.target.classList.contains('kanban-column')) {
        e.target.classList.remove('drag-over');
    }
});

async function drop(ev, newStatus) {
    ev.preventDefault();
    const col = ev.target.closest('.kanban-column');
    if (col) col.classList.remove('drag-over');
    
    if (!draggedCandidate) return;
    
    const oldStatus = draggedCandidate.status || 'applied';
    if (oldStatus === newStatus) return;

    // Logic for specific columns
    if (newStatus === 'rejected') {
        if (confirm(`Are you sure you want to reject ${draggedCandidate.candidate_name || draggedCandidate.name}? This will send a rejection email.`)) {
            await rejectCandidateKanban(draggedCandidate);
        } else {
            return; // Cancel drop
        }
    } else if (newStatus === 'interview_scheduled') {
        // Open modal for scheduling
        openScheduleModal(draggedCandidate.candidate_name || draggedCandidate.name, draggedCandidate.candidate_email || draggedCandidate.email, draggedCandidate.id);
        await updateStatus(draggedCandidate.id, newStatus);
    } else {
        // Just moving back to Applied
        await updateStatus(draggedCandidate.id, newStatus);
    }
    
    // Refresh UI
    loadCandidates();
}

async function updateStatus(id, status) {
    try {
        const response = await fetch(`/api/candidates/${id}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        });
        const data = await response.json();
        if (!data.success) alert('Failed to update status');
    } catch (e) {
        console.error(e);
    }
}

async function rejectCandidateKanban(candidate) {
    try {
        const response = await fetch('/api/reject', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ 
                name: candidate.candidate_name || candidate.name, 
                email: candidate.candidate_email || candidate.email,
                id: candidate.id,
                job_title: currentJobTitle
            })
        });
        const data = await response.json();
        if (data.success) {
            alert('Rejection email sent.');
        } else {
            alert('Error sending rejection: ' + data.error);
        }
    } catch (e) {
        console.error(e);
    }
    loadCandidates();
}

function openCandidateModal(candidate) {
    currentModalCandidateId = candidate.id; // Store for tag operations
    modalCandidateName.textContent = candidate.candidate_name || candidate.name || 'Candidate Details';
    
    let scoreClass = candidate.total_score >= 80 ? 'score-high' : 
                     candidate.total_score >= 60 ? 'score-medium' : 'score-low';
    
    let scoreDisplay = `${candidate.total_score || 0}% Match`;
    
    if (candidate.parsing_failed) {
        scoreClass = 'score-medium'; // Neutral color
        scoreDisplay = 'Manual Review';
    }

    let prosHtml = '';
    let consHtml = '';
    
    if (candidate.ai_analysis) {
        if (candidate.ai_analysis.pros && candidate.ai_analysis.pros.length > 0) {
            prosHtml = `
                <div style="flex: 1; min-width: 300px; background: rgba(16, 185, 129, 0.05); padding: 20px; border-radius: 16px; border: 1px solid rgba(16, 185, 129, 0.2);">
                    <strong style="color: var(--success-color); display: flex; align-items: center; gap: 10px; margin-bottom: 15px; font-size: 1.1rem;">
                        <i class="fas fa-check-circle"></i> Strengths
                    </strong>
                    <ul style="margin: 0 0 0 20px; color: #d0d0d5; line-height: 1.6;">
                        ${candidate.ai_analysis.pros.map(pro => `<li style="margin-bottom: 8px;">${pro}</li>`).join('')}
                    </ul>
                </div>`;
        }
        
        if (candidate.ai_analysis.cons && candidate.ai_analysis.cons.length > 0) {
            consHtml = `
                <div style="flex: 1; min-width: 300px; background: rgba(239, 68, 68, 0.05); padding: 20px; border-radius: 16px; border: 1px solid rgba(239, 68, 68, 0.2);">
                    <strong style="color: var(--danger-color); display: flex; align-items: center; gap: 10px; margin-bottom: 15px; font-size: 1.1rem;">
                        <i class="fas fa-exclamation-circle"></i> Areas for Improvement
                    </strong>
                    <ul style="margin: 0 0 0 20px; color: #d0d0d5; line-height: 1.6;">
                        ${candidate.ai_analysis.cons.map(con => `<li style="margin-bottom: 8px;">${con}</li>`).join('')}
                    </ul>
                </div>`;
        }
    }

    const viewResumeBtn = candidate.file_url ? 
        `<a href="${candidate.file_url}" target="_blank" class="btn btn-primary" style="display: inline-flex; align-items: center; gap: 8px; text-decoration: none; margin-top: 10px;">
            <i class="fas fa-file-alt"></i> View Full Resume
         </a>` : '';

    // Construct Gmail Compose URL
    const emailSubject = encodeURIComponent(`Interview Invitation: ${candidate.candidate_name || 'Candidate'}`);
    const emailBody = encodeURIComponent(`Hi ${candidate.candidate_name || 'Candidate'},\n\nWe have reviewed your application and would like to invite you for an interview.\n\nPlease let us know your availability.\n\nBest regards,\nRecruiting Team`);
    const gmailUrl = `https://mail.google.com/mail/?view=cm&fs=1&to=${candidate.candidate_email}&su=${emailSubject}&body=${emailBody}`;

    modalCandidateBody.innerHTML = `
        <div style="display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 30px; border-bottom: 1px solid var(--border-color); padding-bottom: 20px;">
            <div>
                <div style="font-size: 1.2rem; font-weight: 500; color: var(--text-primary); margin-bottom: 8px; display: flex; align-items: center; gap: 10px;">
                    <i class="fas fa-envelope" style="color: var(--primary-color);"></i> 
                    ${candidate.candidate_email ? 
                        `<a href="${gmailUrl}" target="_blank" style="color: var(--text-primary); text-decoration: none; border-bottom: 1px dashed var(--text-secondary); transition: all 0.2s;" onmouseover="this.style.color='var(--primary-color)'" onmouseout="this.style.color='var(--text-primary)'" title="Compose Interview Email in Gmail">
                            ${candidate.candidate_email} <i class="fas fa-external-link-alt" style="font-size: 0.7em; margin-left: 5px; opacity: 0.7;"></i>
                         </a>` : 'N/A'}
                </div>
                <div style="font-size: 1.2rem; font-weight: 500; color: var(--text-primary); display: flex; align-items: center; gap: 10px;">
                    <i class="fas fa-phone" style="color: var(--primary-color);"></i> 
                    ${candidate.candidate_phone || 'N/A'}
                </div>
            </div>
            <div class="score-badge ${scoreClass}" style="font-size: 1.4rem; padding: 0.75rem 1.5rem; box-shadow: 0 4px 12px rgba(0,0,0,0.2);">
                ${scoreDisplay}
            </div>
        </div>

        ${candidate.parsing_failed ? `
        <div style="background-color: rgba(245, 158, 11, 0.1); color: #f59e0b; padding: 1.5rem; border-radius: 12px; margin-bottom: 2rem; border: 1px solid rgba(245, 158, 11, 0.3);">
            <i class="fas fa-exclamation-triangle"></i> <strong>Resume Parsing Failed</strong><br>
            The system could not automatically read the resume file. Please view the resume manually to evaluate this candidate.
        </div>
        ` : ''}

        <div style="display: grid; grid-template-columns: repeat(3, 1fr); gap: 20px; margin-bottom: 30px;">
            <div style="background: rgba(255, 255, 255, 0.03); padding: 20px; border-radius: 16px; text-align: center; border: 1px solid var(--border-color);">
                <div style="font-size: 1rem; color: #c0c0c5; margin-bottom: 8px;">Skills Match</div>
                <div style="font-size: 2rem; font-weight: 700; color: var(--primary-color);">${candidate.breakdown?.skills_match || 0}%</div>
            </div>
            <div style="background: rgba(255, 255, 255, 0.03); padding: 20px; border-radius: 16px; text-align: center; border: 1px solid var(--border-color);">
                <div style="font-size: 1rem; color: #c0c0c5; margin-bottom: 8px;">Experience</div>
                <div style="font-size: 2rem; font-weight: 700; color: var(--primary-color);">${candidate.breakdown?.experience || 0}%</div>
            </div>
            <div style="background: rgba(255, 255, 255, 0.03); padding: 20px; border-radius: 16px; text-align: center; border: 1px solid var(--border-color);">
                <div style="font-size: 1rem; color: #c0c0c5; margin-bottom: 8px;">Education</div>
                <div style="font-size: 2rem; font-weight: 700; color: var(--primary-color);">${candidate.breakdown?.education || 0}%</div>
            </div>
        </div>

        <div style="margin-bottom: 30px; background: rgba(255, 255, 255, 0.02); padding: 25px; border-radius: 16px; border: 1px solid var(--border-color);">
            <h4 style="color: var(--text-primary); margin-bottom: 15px; font-size: 1.2rem; border-bottom: 1px solid var(--border-color); padding-bottom: 10px;">
                <i class="fas fa-robot" style="margin-right: 10px; color: var(--info-color);"></i> AI Executive Summary
            </h4>
            <p style="line-height: 1.8; color: #d0d0d5; font-size: 1.05rem;">
                ${candidate.ai_analysis?.summary || candidate.feedback || 'No summary available.'}
            </p>
        </div>

        <div style="display: flex; gap: 25px; margin-bottom: 30px; flex-wrap: wrap; align-items: stretch;">
            ${prosHtml}
            ${consHtml}
        </div>

        <!-- Tags Section -->
        <div style="margin-bottom: 25px; background: rgba(255, 255, 255, 0.02); padding: 20px; border-radius: 16px; border: 1px solid var(--border-color);">
            <h4 style="color: var(--text-primary); margin-bottom: 15px; font-size: 1.1rem;">
                <i class="fas fa-tags" style="margin-right: 10px; color: var(--warning-color);"></i> Tags
            </h4>
            <div id="modal-tags-container" style="display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 15px;">
                ${renderTags(candidate.tags || [])}
            </div>
            <div style="display: flex; gap: 10px;">
                <input type="text" id="modal-new-tag" class="form-control" placeholder="Add new tag..." 
                    style="flex: 1; padding: 8px 12px; border: 1px solid var(--border-color); border-radius: 6px; background: var(--bg-color); color: var(--text-primary);"
                    onkeypress="if(event.key==='Enter'){event.preventDefault(); addTagFromModal('${candidate.id}');}">
                <button class="btn btn-sm btn-primary" onclick="addTagFromModal('${candidate.id}')" style="padding: 8px 16px;">
                    <i class="fas fa-plus"></i> Add
                </button>
            </div>
            <div style="margin-top: 10px; display: flex; flex-wrap: wrap; gap: 5px;">
                <small style="color: var(--text-secondary); margin-right: 5px;">Quick add:</small>
                <button class="quick-tag-btn" onclick="quickAddTag('${candidate.id}', 'Senior')">Senior</button>
                <button class="quick-tag-btn" onclick="quickAddTag('${candidate.id}', 'Junior')">Junior</button>
                <button class="quick-tag-btn" onclick="quickAddTag('${candidate.id}', 'Remote OK')">Remote OK</button>
                <button class="quick-tag-btn" onclick="quickAddTag('${candidate.id}', 'Top Pick')">⭐ Top Pick</button>
                <button class="quick-tag-btn" onclick="quickAddTag('${candidate.id}', 'Needs Follow-up')">Needs Follow-up</button>
            </div>
        </div>

        <!-- Notes Section -->
        <div style="margin-bottom: 25px; background: rgba(255, 255, 255, 0.02); padding: 20px; border-radius: 16px; border: 1px solid var(--border-color);">
            <h4 style="color: var(--text-primary); margin-bottom: 15px; font-size: 1.1rem;">
                <i class="fas fa-sticky-note" style="margin-right: 10px; color: var(--info-color);"></i> Internal Notes
            </h4>
            <textarea id="modal-notes" class="form-control" rows="4" placeholder="Add internal notes about this candidate..."
                style="width: 100%; padding: 12px; border: 1px solid var(--border-color); border-radius: 8px; background: var(--bg-color); color: var(--text-primary); resize: vertical;">${candidate.notes || ''}</textarea>
            <div style="display: flex; justify-content: flex-end; margin-top: 10px;">
                <button class="btn btn-sm btn-primary" onclick="saveNotes('${candidate.id}')" id="save-notes-btn">
                    <i class="fas fa-save"></i> Save Notes
                </button>
            </div>
        </div>

        <div style="margin-top: 20px; text-align: right; border-top: 1px solid var(--border-color); padding-top: 20px;">
            ${viewResumeBtn}
        </div>
    `;

    candidateModal.classList.add('active');
}

// Helper function to render tags
function renderTags(tags) {
    if (!tags || tags.length === 0) {
        return '<span style="color: var(--text-secondary); font-style: italic;">No tags yet</span>';
    }
    return tags.map(tag => `
        <span class="candidate-tag" style="background: linear-gradient(135deg, var(--primary-color), var(--info-color)); color: white; padding: 4px 12px; border-radius: 20px; font-size: 0.85rem; display: inline-flex; align-items: center; gap: 6px;">
            ${tag}
            <button onclick="removeTag('${currentModalCandidateId}', '${tag}')" style="background: none; border: none; color: white; cursor: pointer; padding: 0; line-height: 1; opacity: 0.8;" title="Remove tag">
                <i class="fas fa-times" style="font-size: 0.7rem;"></i>
            </button>
        </span>
    `).join('');
}

// Store current modal candidate ID
let currentModalCandidateId = null;

// Tags Functions
async function addTagFromModal(candidateId) {
    const input = document.getElementById('modal-new-tag');
    const tag = input.value.trim();
    if (!tag) return;
    
    await addTag(candidateId, tag);
    input.value = '';
}

async function quickAddTag(candidateId, tag) {
    await addTag(candidateId, tag);
}

async function addTag(candidateId, tag) {
    const candidate = currentCandidates.find(c => c.id === candidateId);
    if (!candidate) return;
    
    const currentTags = candidate.tags || [];
    if (currentTags.includes(tag)) {
        alert('Tag already exists!');
        return;
    }
    
    const newTags = [...currentTags, tag];
    
    try {
        const response = await fetch(`/api/candidates/${candidateId}/tags`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tags: newTags })
        });
        const data = await response.json();
        if (data.success) {
            candidate.tags = newTags;
            document.getElementById('modal-tags-container').innerHTML = renderTags(newTags);
            updateTagFilter(); // Update the filter dropdown
        } else {
            alert('Failed to add tag: ' + data.error);
        }
    } catch (e) {
        console.error('Error adding tag:', e);
        alert('Failed to add tag');
    }
}

async function removeTag(candidateId, tagToRemove) {
    const candidate = currentCandidates.find(c => c.id === candidateId);
    if (!candidate) return;
    
    const newTags = (candidate.tags || []).filter(t => t !== tagToRemove);
    
    try {
        const response = await fetch(`/api/candidates/${candidateId}/tags`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ tags: newTags })
        });
        const data = await response.json();
        if (data.success) {
            candidate.tags = newTags;
            document.getElementById('modal-tags-container').innerHTML = renderTags(newTags);
            updateTagFilter();
        }
    } catch (e) {
        console.error('Error removing tag:', e);
    }
}

// Notes Functions
async function saveNotes(candidateId) {
    const notesArea = document.getElementById('modal-notes');
    const saveBtn = document.getElementById('save-notes-btn');
    const notes = notesArea.value;
    
    saveBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Saving...';
    saveBtn.disabled = true;
    
    try {
        const response = await fetch(`/api/candidates/${candidateId}/notes`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ notes })
        });
        const data = await response.json();
        if (data.success) {
            const candidate = currentCandidates.find(c => c.id === candidateId);
            if (candidate) candidate.notes = notes;
            saveBtn.innerHTML = '<i class="fas fa-check"></i> Saved!';
            setTimeout(() => {
                saveBtn.innerHTML = '<i class="fas fa-save"></i> Save Notes';
                saveBtn.disabled = false;
            }, 2000);
        } else {
            throw new Error(data.error);
        }
    } catch (e) {
        console.error('Error saving notes:', e);
        saveBtn.innerHTML = '<i class="fas fa-exclamation-triangle"></i> Error';
        setTimeout(() => {
            saveBtn.innerHTML = '<i class="fas fa-save"></i> Save Notes';
            saveBtn.disabled = false;
        }, 2000);
    }
}

// Schedule Modal Logic
window.openScheduleModal = function(name, email, id) {
    document.getElementById('candidateName').value = name;
    document.getElementById('candidateEmail').value = email;
    currentScheduleCandidateId = id;
    document.getElementById('interviewTitle').value = `Interview with ${name}${currentJobTitle ? ' - ' + currentJobTitle : ''}`;
    
    const savedLink = localStorage.getItem('defaultMeetingLink');
    if (savedLink) {
        document.getElementById('meetingLink').value = savedLink;
    }
    
    const tomorrow = new Date();
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(10, 0, 0, 0);
    const offset = tomorrow.getTimezoneOffset() * 60000;
    const localISOTime = (new Date(tomorrow - offset)).toISOString().slice(0, 16);
    document.getElementById('interviewDate').value = localISOTime;
    
    scheduleModal.style.display = "block";
}

function getCalendarUrl() {
    const title = encodeURIComponent(document.getElementById('interviewTitle').value);
    const dateInput = document.getElementById('interviewDate').value;
    const duration = parseInt(document.getElementById('interviewDuration').value);
    const type = encodeURIComponent(document.getElementById('interviewType').value);
    const meetingLink = document.getElementById('meetingLink').value;
    const email = encodeURIComponent(document.getElementById('candidateEmail').value);
    const name = document.getElementById('candidateName').value;
    
    const startDate = new Date(dateInput);
    const endDate = new Date(startDate.getTime() + duration * 60000);
    
    const formatTime = (date) => date.toISOString().replace(/-|:|\.\d\d\d/g, "");
    
    let detailsText = `Interview with ${name}\nType: ${decodeURIComponent(type)}`;
    if (meetingLink) {
        detailsText += `\nMeeting Link: ${meetingLink}`;
    }
    detailsText += `\n\nPlease confirm your availability.`;
    
    const details = encodeURIComponent(detailsText);
    let location = "";
    if (meetingLink) {
        location = `&location=${encodeURIComponent(meetingLink)}`;
    }
    
    return `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${title}&dates=${formatTime(startDate)}/${formatTime(endDate)}&details=${details}${location}&add=${email}`;
}

if (generateGCalBtn) {
    generateGCalBtn.onclick = async function() {
        const name = document.getElementById('candidateName').value;
        const email = document.getElementById('candidateEmail').value;
        const title = document.getElementById('interviewTitle').value;
        const dateInput = document.getElementById('interviewDate').value;
        const duration = document.getElementById('interviewDuration').value;
        const type = document.getElementById('interviewType').value;
        const meetingLink = document.getElementById('meetingLink').value;
        
        const gcalUrl = getCalendarUrl();
        
        if (meetingLink) {
            localStorage.setItem('defaultMeetingLink', meetingLink);
        }
        
        const dateObj = new Date(dateInput);
        const dateDisplay = dateObj.toLocaleString();

        const originalText = this.innerHTML;
        this.disabled = true;
        this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';

        try {
            const response = await fetch('/api/schedule', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    id: currentScheduleCandidateId,
                    name: name,
                    email: email,
                    details: {
                        title: title,
                        start_time: dateInput,
                        duration: duration,
                        type: type,
                        meeting_link: meetingLink,
                        gcal_link: gcalUrl,
                        date_display: dateDisplay,
                        job_title: currentJobTitle
                    }
                })
            });

            const data = await response.json();

            if (data.success) {
                alert(`Interview invitation sent to ${name}.`);
                scheduleModal.style.display = "none";
                loadCandidates();
            } else {
                alert('Error sending invitation: ' + (data.error || 'Unknown error'));
            }
        } catch (e) {
            console.error(e);
            alert('Failed to send invitation.');
        } finally {
            this.disabled = false;
            this.innerHTML = originalText;
        }
    }
}

if (copyLinkBtn) {
    copyLinkBtn.onclick = function() {
        const url = getCalendarUrl();
        navigator.clipboard.writeText(url).then(() => {
            const originalText = this.innerHTML;
            this.innerHTML = '<i class="fas fa-check"></i> Copied!';
            setTimeout(() => {
                this.innerHTML = originalText;
            }, 2000);
        });
    }
}

if (rejectCandidateBtn) {
    rejectCandidateBtn.onclick = async function() {
        const name = document.getElementById('candidateName').value;
        const email = document.getElementById('candidateEmail').value;

        if (!confirm(`Are you sure you want to send a rejection email to ${name}?`)) {
            return;
        }

        const originalText = this.innerHTML;
        this.disabled = true;
        this.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Sending...';

        try {
            const response = await fetch('/api/reject', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ 
                    name, 
                    email, 
                    id: currentScheduleCandidateId,
                    job_title: currentJobTitle
                })
            });

            const data = await response.json();

            if (data.success) {
                alert(`Rejection email sent to ${name}.`);
                scheduleModal.style.display = "none";
                loadCandidates();
            } else {
                alert('Error sending email: ' + (data.error || 'Unknown error'));
            }
        } catch (error) {
            console.error('Error:', error);
            alert('An error occurred while sending the rejection email.');
        } finally {
            this.disabled = false;
            this.innerHTML = originalText;
        }
    }
}

async function processPendingQueue(ids) {
    console.log(`Starting batch processing check for ${ids.length} candidates...`);
    
    let processed = 0;
    let skipped = 0;
    
    for (let i = 0; i < ids.length; i++) {
        const id = ids[i];
        const btn = document.querySelector(`button[onclick*="${id}"]`);
        
        if (btn) {
            btn.innerHTML = `<i class="fas fa-spinner fa-spin"></i> Checking (${i+1}/${ids.length})...`;
            btn.disabled = true;
        }

        try {
            const response = await fetch(`/api/process/${id}`, { method: 'POST' });
            const data = await response.json();
            
            if (data.skipped) {
                console.log(`Candidate ${id} already processed, skipping.`);
                skipped++;
            } else {
                console.log(`Candidate ${id} processed successfully.`);
                processed++;
            }
            
            await new Promise(r => setTimeout(r, 500)); // Shorter delay since we're just checking
        } catch (e) {
            console.error(`Failed to process ${id}:`, e);
        }
    }
    
    console.log(`Batch complete: ${processed} processed, ${skipped} skipped.`);
    loadCandidates();
}

async function processCandidate(id) {
    try {
        const btn = event.target.closest('button');
        const originalText = btn.innerHTML;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
        btn.disabled = true;

        const response = await fetch(`/api/process/${id}`, { method: 'POST' });
        const data = await response.json();

        if (data.success) {
            loadCandidates(); 
        } else {
            alert('Error: ' + data.error);
            btn.innerHTML = originalText;
            btn.disabled = false;
        }
    } catch (e) {
        console.error(e);
        alert('Failed to process candidate.');
    }
}
