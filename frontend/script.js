/**
 * Cold Email AI - Frontend JavaScript
 * Handles all API calls, UI interactions, and data management
 */

// ============================================
// Configuration
// ============================================

// API URL Configuration - Update this with your Render backend URL after deployment
const API_BASE = (() => {
    // Local development
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return 'http://localhost:8000';
    }
    // Production - Update with your actual Render backend URL
    // Example: 'https://cold-email-api.onrender.com'
    // For now, try same origin (if frontend and backend on same domain)
    return window.API_URL || '';
})();

let currentEmail = null;
let batchResults = [];
let historyData = [];

// ============================================
// Tab Navigation
// ============================================

document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        // Update active tab button
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        
        // Update active tab content
        const tabId = btn.dataset.tab;
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
        });
        document.getElementById(tabId).classList.add('active');
        
        // Load data for specific tabs
        if (tabId === 'history') loadHistory();
        if (tabId === 'analytics') loadAnalytics();
    });
});

// ============================================
// Single Email Generation
// ============================================

document.getElementById('emailForm').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const jobUrl = document.getElementById('jobUrl').value;
    const role = document.getElementById('role').value;
    const industry = document.getElementById('industry').value;
    
    // Validate: need either job_url OR (role + industry)
    if (!jobUrl && (!role || !industry)) {
        showToast('Please provide either a Job URL or both Role and Industry', 'error');
        return;
    }
    
    const formData = {
        job_url: jobUrl || null,
        role: role || null,
        industry: industry || null,
        company_name: document.getElementById('companyName').value || null,
        recipient_name: document.getElementById('recipientName').value || null,
        sender_name: document.getElementById('senderName').value,
        sender_company: document.getElementById('senderCompany').value,
        sender_services: document.getElementById('senderServices').value,
        tone: document.getElementById('tone').value
    };
    
    await generateEmail(formData);
});

async function generateEmail(formData) {
    // Show loading state
    showState('loading');
    const btn = document.getElementById('generateBtn');
    btn.disabled = true;
    
    // Animate loading steps
    animateLoadingSteps();
    
    try {
        const response = await fetch(`${API_BASE}/generate`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Failed to generate email');
        }
        
        const data = await response.json();
        currentEmail = data;
        displayEmailResult(data);
        showToast('Email generated successfully!', 'success');
        
    } catch (error) {
        console.error('Error:', error);
        showToast(error.message || 'Failed to generate email', 'error');
        showState('empty');
    } finally {
        btn.disabled = false;
    }
}

function animateLoadingSteps() {
    const steps = document.querySelectorAll('.loading-steps .step');
    let currentStep = 0;
    
    const interval = setInterval(() => {
        if (currentStep < steps.length) {
            steps[currentStep].classList.remove('active');
            steps[currentStep].classList.add('done');
            currentStep++;
            if (currentStep < steps.length) {
                steps[currentStep].classList.add('active');
            }
        } else {
            clearInterval(interval);
        }
    }, 1500);
    
    // Start first step
    steps[0].classList.add('active');
    
    // Store interval to clear later
    window.loadingInterval = interval;
}

function animateLeadLoadingSteps() {
    const steps = document.querySelectorAll('#leadPreviewLoadingState .loading-steps .step');
    let currentStep = 0;
    
    const interval = setInterval(() => {
        if (currentStep < steps.length) {
            steps[currentStep].classList.remove('active');
            steps[currentStep].classList.add('done');
            currentStep++;
            if (currentStep < steps.length) {
                steps[currentStep].classList.add('active');
            }
        } else {
            clearInterval(interval);
        }
    }, 1500);
    
    // Start first step
    steps[0].classList.add('active');
    
    // Store interval to clear later
    window.leadLoadingInterval = interval;
}

function showState(state) {
    document.getElementById('loadingState').style.display = state === 'loading' ? 'block' : 'none';
    document.getElementById('emptyState').style.display = state === 'empty' ? 'block' : 'none';
    document.getElementById('resultState').style.display = state === 'result' ? 'block' : 'none';
    
    // Reset loading steps
    if (state !== 'loading') {
        clearInterval(window.loadingInterval);
        document.querySelectorAll('.loading-steps .step').forEach(step => {
            step.classList.remove('active', 'done');
        });
    }
}

function displayEmailResult(data) {
    console.log('displayEmailResult called with:', data);
    console.log('Portfolio items received:', data.portfolio_items_used);
    showState('result');
    
    // Display email content
    const email = data.email || {};
    console.log('Email object:', email);
    
    document.getElementById('emailSubject').textContent = email.subject_line || 'No subject';
    document.getElementById('emailBody').textContent = email.body || 'No body content';
    document.getElementById('emailCta').textContent = email.cta || 'No CTA';
    
    // Display score
    const score = data.evaluation?.overall_score || 0;
    document.getElementById('scoreBadge').style.display = 'flex';
    document.getElementById('scoreValue').textContent = score.toFixed(1);
    
    // Display metrics
    const evaluation = data.evaluation || {};
    displayMetric('clarity', evaluation.clarity_score || 0);
    displayMetric('tone', evaluation.tone_alignment_score || 0);
    displayMetric('length', evaluation.length_score || 0);
    displayMetric('personal', evaluation.personalization_score || 0);
    displayMetric('spam', 10 - (evaluation.spam_risk_score || 5)); // Invert for "spam safe"
    
    // Display strengths
    const strengthsList = document.getElementById('strengthsList');
    strengthsList.innerHTML = '';
    const strengths = evaluation.strengths || [];
    if (strengths.length > 0) {
        document.getElementById('strengthsSection').style.display = 'block';
        strengths.forEach(s => {
            const li = document.createElement('li');
            li.textContent = s;
            strengthsList.appendChild(li);
        });
    } else {
        document.getElementById('strengthsSection').style.display = 'none';
    }
    
    // Display issues
    const issuesList = document.getElementById('issuesList');
    issuesList.innerHTML = '';
    const issues = evaluation.issues || [];
    if (issues.length > 0) {
        document.getElementById('issuesSection').style.display = 'block';
        issues.forEach(i => {
            const li = document.createElement('li');
            li.textContent = i;
            issuesList.appendChild(li);
        });
    } else {
        document.getElementById('issuesSection').style.display = 'none';
    }
    
    // Display alternative subjects
    const altSubjectsList = document.getElementById('altSubjectsList');
    altSubjectsList.innerHTML = '';
    const altSubjects = data.alternative_subject_lines || [];
    if (altSubjects.length > 0) {
        document.getElementById('altSubjectsSection').style.display = 'block';
        altSubjects.forEach(subject => {
            const li = document.createElement('li');
            li.textContent = subject;
            li.onclick = () => {
                document.getElementById('emailSubject').textContent = subject;
                currentEmail.email.subject_line = subject;
                showToast('Subject line updated!', 'success');
            };
            altSubjectsList.appendChild(li);
        });
    } else {
        document.getElementById('altSubjectsSection').style.display = 'none';
    }
    
    // Display portfolio items
    const portfolioList = document.getElementById('portfolioList');
    portfolioList.innerHTML = '';
    const portfolioItems = data.portfolio_items_used || [];
    if (portfolioItems.length > 0) {
        document.getElementById('portfolioSection').style.display = 'block';
        portfolioItems.forEach(item => {
            const div = document.createElement('div');
            div.className = 'portfolio-item';
            div.innerHTML = `
                <h5>${item.title || 'Project'}</h5>
                <div class="tech-stack">${item.tech_stack || 'N/A'}</div>
                <a href="${item.link || '#'}" target="_blank"><i class="fas fa-external-link-alt"></i> View Project</a>
            `;
            portfolioList.appendChild(div);
        });
    } else {
        document.getElementById('portfolioSection').style.display = 'none';
    }
}

function displayMetric(name, score) {
    const bar = document.getElementById(`${name}Bar`);
    const scoreEl = document.getElementById(`${name}Score`);
    
    bar.style.width = `${score * 10}%`;
    scoreEl.textContent = score.toFixed(1);
    
    // Color based on score
    if (score >= 8) {
        bar.style.background = 'var(--success)';
    } else if (score >= 6) {
        bar.style.background = 'var(--primary)';
    } else {
        bar.style.background = 'var(--warning)';
    }
}

// ============================================
// Action Buttons
// ============================================

function copyEmail() {
    if (!currentEmail) return;
    
    const email = currentEmail.email;
    const text = `Subject: ${email.subject_line}\n\n${email.body}`;
    
    navigator.clipboard.writeText(text).then(() => {
        showToast('Email copied to clipboard!', 'success');
    }).catch(() => {
        showToast('Failed to copy', 'error');
    });
}

function downloadTxt() {
    if (!currentEmail) return;
    
    const email = currentEmail.email;
    const text = `Subject: ${email.subject_line}\n\n${email.body}\n\n${email.cta || ''}`;
    
    const blob = new Blob([text], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cold-email-${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showToast('Email saved as TXT file!', 'success');
}

function downloadEml() {
    if (!currentEmail) return;
    
    const email = currentEmail.email;
    const recipientName = document.getElementById('recipientName').value || 'Hiring Manager';
    const senderName = document.getElementById('senderName').value;
    const senderEmail = 'sender@example.com'; // Placeholder
    
    const emlContent = `MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
From: ${senderName} <${senderEmail}>
To: ${recipientName}
Subject: ${email.subject_line}
Date: ${new Date().toUTCString()}

${email.body}
`;
    
    const blob = new Blob([emlContent], { type: 'message/rfc822' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cold-email-${Date.now()}.eml`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showToast('Email downloaded as .eml file!', 'success');
}

function exportJson() {
    if (!currentEmail) return;
    
    const blob = new Blob([JSON.stringify(currentEmail, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `cold-email-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showToast('Exported as JSON!', 'success');
}

// ============================================
// Batch Processing
// ============================================

const uploadZone = document.getElementById('uploadZone');
const csvFileInput = document.getElementById('csvFile');
let csvData = [];

// Drag and drop
uploadZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadZone.classList.add('dragover');
});

uploadZone.addEventListener('dragleave', () => {
    uploadZone.classList.remove('dragover');
});

uploadZone.addEventListener('drop', (e) => {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    const file = e.dataTransfer.files[0];
    if (file && file.name.endsWith('.csv')) {
        handleCsvFile(file);
    } else {
        showToast('Please upload a CSV file', 'error');
    }
});

csvFileInput.addEventListener('change', (e) => {
    if (e.target.files[0]) {
        handleCsvFile(e.target.files[0]);
    }
});

function handleCsvFile(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
        const text = e.target.result;
        csvData = parseCSV(text);
        displayCsvPreview();
    };
    reader.readAsText(file);
}

function parseCSV(text) {
    const lines = text.trim().split('\n');
    const headers = lines[0].split(',').map(h => h.trim());
    const data = [];
    
    for (let i = 1; i < lines.length; i++) {
        if (!lines[i].trim()) continue;
        const values = lines[i].split(',').map(v => v.trim());
        const row = {};
        headers.forEach((h, idx) => {
            row[h] = values[idx] || '';
        });
        data.push(row);
    }
    
    return data;
}

function displayCsvPreview() {
    const preview = document.getElementById('csvPreview');
    const table = document.getElementById('previewTable');
    const rowCount = document.getElementById('rowCount');
    
    if (csvData.length === 0) {
        preview.style.display = 'none';
        return;
    }
    
    // Validate required columns
    const headers = Object.keys(csvData[0]);
    const requiredColumns = ['job_url', 'company_name'];
    const missingColumns = requiredColumns.filter(col => !headers.includes(col));
    
    if (missingColumns.length > 0) {
        showToast(`Missing required columns: ${missingColumns.join(', ')}`, 'error');
        csvData = [];
        preview.style.display = 'none';
        return;
    }
    
    // Check for empty required fields
    const invalidRows = csvData.filter((row, idx) => !row.job_url || !row.company_name)
        .map((_, idx) => idx + 2); // +2 because row 1 is headers
    
    if (invalidRows.length > 0) {
        showToast(`Empty required fields in rows: ${invalidRows.slice(0, 5).join(', ')}${invalidRows.length > 5 ? '...' : ''}`, 'error');
    }
    
    // Check row count
    if (csvData.length > 200) {
        showToast('CSV cannot exceed 200 rows. Please split into smaller batches.', 'error');
        csvData = csvData.slice(0, 200);
    }
    
    rowCount.textContent = csvData.length;
    
    // Build table
    let html = '<thead><tr>';
    headers.forEach(h => {
        const isRequired = requiredColumns.includes(h);
        html += `<th>${h}${isRequired ? ' *' : ''}</th>`;
    });
    html += '</tr></thead><tbody>';
    
    // Show first 5 rows
    const previewRows = csvData.slice(0, 5);
    previewRows.forEach(row => {
        html += '<tr>';
        headers.forEach(h => html += `<td>${row[h] || '-'}</td>`);
        html += '</tr>';
    });
    
    if (csvData.length > 5) {
        html += `<tr><td colspan="${headers.length}" style="text-align:center;color:var(--gray-400);">... and ${csvData.length - 5} more rows</td></tr>`;
    }
    
    html += '</tbody>';
    table.innerHTML = html;
    preview.style.display = 'block';
    
    showToast(`✅ Loaded ${csvData.length} rows. Ready to process!`, 'success');
}

function clearCsv() {
    csvData = [];
    csvFileInput.value = '';
    document.getElementById('csvPreview').style.display = 'none';
    document.getElementById('batchProgress').style.display = 'none';
    document.getElementById('batchResults').style.display = 'none';
}

function resetBatch() {
    // Clear all data
    csvData = [];
    batchResults = [];
    csvFileInput.value = '';
    
    // Hide all sections
    document.getElementById('csvPreview').style.display = 'none';
    document.getElementById('batchProgress').style.display = 'none';
    document.getElementById('batchResults').style.display = 'none';
    
    // Clear results table
    document.getElementById('resultsTableBody').innerHTML = '';
    
    // Reset upload zone
    uploadZone.classList.remove('dragover');
    
    showToast('Ready for new batch upload', 'success');
}

document.getElementById('startBatchBtn').addEventListener('click', startBatchProcessing);

async function startBatchProcessing() {
    if (csvData.length === 0) return;
    
    batchResults = [];
    let successCount = 0;
    let failedCount = 0;
    let totalScore = 0;
    const errors = [];

    document.getElementById('csvPreview').style.display = 'none';
    document.getElementById('batchProgress').style.display = 'block';
    document.getElementById('batchResults').style.display = 'none';
    
    const progressBar = document.getElementById('progressBar');
    const progressCount = document.getElementById('progressCount');
    const batchLog = document.getElementById('batchLog');
    batchLog.innerHTML = '';
    
    for (let i = 0; i < csvData.length; i++) {
        const row = csvData[i];
        const progress = ((i + 1) / csvData.length) * 100;
        
        progressBar.style.width = `${progress}%`;
        progressCount.textContent = `${i + 1}/${csvData.length}`;
        
        try {
            const response = await fetch(`${API_BASE}/generate`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    job_url: row.job_url,
                    company_name: row.company_name || null,
                    recipient_name: row.recipient_name || null,
                    sender_name: row.sender_name || 'Alex',
                    sender_company: row.sender_company || 'TechSolutions Inc.',
                    sender_services: row.sender_services || 'software development and consulting'
                })
            });
            
            if (response.ok) {
                const data = await response.json();
                const score = data.evaluation?.overall_score || 0;
                batchResults.push({
                    row_number: i + 1,
                    company_name: row.company_name || 'Unknown',
                    job_url: row.job_url,
                    recipient_name: row.recipient_name || '',
                    status: 'Success',
                    subject_line: data.email?.subject_line || '',
                    body: data.email?.body || '',
                    cta: data.email?.cta || '',
                    score: score,
                    clarity_score: data.evaluation?.clarity_score || 0,
                    tone_score: data.evaluation?.tone_alignment_score || 0,
                    length_score: data.evaluation?.length_score || 0,
                    personalization_score: data.evaluation?.personalization_score || 0,
                    spam_risk_score: data.evaluation?.spam_risk_score || 5,
                    // New fields for modal
                    strengths: data.evaluation?.strengths || [],
                    issues: data.evaluation?.issues || [],
                    portfolio_items: data.portfolio_items_used || [],
                    alt_subjects: data.alternative_subject_lines || []
                });
                successCount++;
                totalScore += score;
                addLogItem(`✓ ${row.company_name || row.job_url}`, 'success');
            } else {
                const errData = await response.json().catch(() => ({}));
                const errorMsg = errData.detail || `HTTP ${response.status}`;
                throw new Error(errorMsg);
            }
        } catch (error) {
            batchResults.push({
                row_number: i + 1,
                company_name: row.company_name || 'Unknown',
                job_url: row.job_url,
                status: 'Failed',
                error: error.message,
                subject_line: '',
                body: '',
                cta: '',
                score: 0
            });
            failedCount++;
            errors.push(`Row ${i + 1} (${row.company_name || row.job_url}): ${error.message}`);
            addLogItem(`✗ ${row.company_name || row.job_url}: ${error.message}`, 'error');
        }
        
        // Small delay to prevent rate limiting
        await new Promise(resolve => setTimeout(resolve, 500));
    }
    
    // Calculate average score
    const avgScore = successCount > 0 ? (totalScore / successCount) : 0;
    
    // Show results
    document.getElementById('batchProgress').style.display = 'none';
    document.getElementById('batchResults').style.display = 'block';
    
    // Update stats
    document.getElementById('totalCount').textContent = csvData.length;
    document.getElementById('successCount').textContent = successCount;
    document.getElementById('failedCount').textContent = failedCount;
    document.getElementById('batchAvgScore').textContent = avgScore.toFixed(1);
    
    // Show errors if any
    if (errors.length > 0) {
        document.getElementById('batchErrors').style.display = 'block';
        document.getElementById('errorCount').textContent = errors.length;
        document.getElementById('errorList').innerHTML = errors.map(e => `<div class="error-item"><i class="fas fa-exclamation-circle"></i> ${e}</div>`).join('');
    } else {
        document.getElementById('batchErrors').style.display = 'none';
    }
    
    // Build results table
    buildResultsTable();
    
    showToast(`Batch complete! ${successCount} success, ${failedCount} failed`, 'success');
}

function toggleBatchErrors() {
    const errorList = document.getElementById('errorList');
    errorList.style.display = errorList.style.display === 'none' ? 'block' : 'none';
}

function buildResultsTable() {
    const tbody = document.getElementById('resultsTableBody');
    tbody.innerHTML = '';
    
    batchResults.forEach((result, idx) => {
        const statusClass = result.status === 'Success' ? 'success' : 'failed';
        const scoreDisplay = result.status === 'Success' ? result.score.toFixed(1) : '-';
        const truncatedSubject = result.subject_line ? 
            (result.subject_line.length > 35 ? result.subject_line.substring(0, 35) + '...' : result.subject_line) 
            : '-';
        
        // Build metrics display
        const metricsHtml = result.status === 'Success' ? `
            <div class="metrics-mini">
                <span title="Clarity">C:${(result.clarity_score || 0).toFixed(1)}</span>
                <span title="Tone">T:${(result.tone_score || 0).toFixed(1)}</span>
                <span title="Personal">P:${(result.personalization_score || 0).toFixed(1)}</span>
                <span title="Length">L:${(result.length_score || 0).toFixed(1)}</span>
                <span title="Spam Safe">S:${(10 - (result.spam_risk_score || 5)).toFixed(1)}</span>
            </div>
        ` : '-';
        
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${result.row_number}</td>
            <td>${result.company_name}</td>
            <td title="${result.subject_line || ''}">${truncatedSubject}</td>
            <td><span class="score-badge ${result.score >= 7 ? 'good' : result.score >= 5 ? 'ok' : 'low'}">${scoreDisplay}</span></td>
            <td>${metricsHtml}</td>
            <td><span class="status-badge ${statusClass}">${result.status}</span></td>
            <td>
                ${result.status === 'Success' ? `
                    <button class="btn-icon" onclick="viewBatchEmail(${idx})" title="View Email">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn-icon" onclick="copyBatchEmail(${idx})" title="Copy Email">
                        <i class="fas fa-copy"></i>
                    </button>
                ` : '-'}
            </td>
        `;
        tbody.appendChild(row);
    });
}

function viewBatchEmail(idx) {
    const result = batchResults[idx];
    if (!result || result.status !== 'Success') return;
    
    // Build strengths HTML
    const strengthsHtml = result.strengths && result.strengths.length > 0 ? `
        <div class="modal-section strengths-section">
            <h4><i class="fas fa-check-circle"></i> Strengths</h4>
            <ul>${result.strengths.map(s => `<li>${s}</li>`).join('')}</ul>
        </div>
    ` : '';
    
    // Build issues HTML
    const issuesHtml = result.issues && result.issues.length > 0 ? `
        <div class="modal-section issues-section">
            <h4><i class="fas fa-exclamation-triangle"></i> Areas to Improve</h4>
            <ul>${result.issues.map(i => `<li>${i}</li>`).join('')}</ul>
        </div>
    ` : '';
    
    // Build portfolio items HTML
    const portfolioHtml = result.portfolio_items && result.portfolio_items.length > 0 ? `
        <div class="modal-section portfolio-section">
            <h4><i class="fas fa-briefcase"></i> Portfolio Items Included</h4>
            <div class="portfolio-list">
                ${result.portfolio_items.map(p => `
                    <div class="portfolio-item-mini">
                        <strong>${p.title || 'Project'}</strong>
                        <span class="tech-stack">${p.tech_stack || ''}</span>
                        ${p.link ? `<a href="${p.link}" target="_blank"><i class="fas fa-external-link-alt"></i></a>` : ''}
                    </div>
                `).join('')}
            </div>
        </div>
    ` : '';
    
    // Build alternative subjects HTML
    const altSubjectsHtml = result.alt_subjects && result.alt_subjects.length > 0 ? `
        <div class="modal-section alt-subjects-section">
            <h4><i class="fas fa-lightbulb"></i> Alternative Subject Lines</h4>
            <ul class="alt-subjects-list">
                ${result.alt_subjects.map(s => `<li>${s}</li>`).join('')}
            </ul>
        </div>
    ` : '';
    
    // Create modal content with all metrics
    const modalHtml = `
        <div class="batch-email-modal" id="batchEmailModal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${result.company_name}</h3>
                    <button onclick="closeBatchEmailModal()" class="close-btn"><i class="fas fa-times"></i></button>
                </div>
                <div class="modal-body">
                    <div class="email-field">
                        <label>Subject:</label>
                        <p>${result.subject_line}</p>
                    </div>
                    <div class="email-field">
                        <label>Body:</label>
                        <p style="white-space: pre-wrap;">${result.body}</p>
                    </div>
                    <div class="email-field">
                        <label>CTA:</label>
                        <p>${result.cta}</p>
                    </div>
                    
                    <!-- Evaluation Metrics -->
                    <div class="modal-metrics">
                        <h4>Evaluation Metrics</h4>
                        <div class="metrics-grid">
                            <div class="metric-item">
                                <span class="metric-label">Overall Score</span>
                                <span class="metric-value score">${result.score.toFixed(1)}/10</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Clarity</span>
                                <span class="metric-value">${(result.clarity_score || 0).toFixed(1)}</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Tone</span>
                                <span class="metric-value">${(result.tone_score || 0).toFixed(1)}</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Length</span>
                                <span class="metric-value">${(result.length_score || 0).toFixed(1)}</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Personalization</span>
                                <span class="metric-value">${(result.personalization_score || 0).toFixed(1)}</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Spam Safe</span>
                                <span class="metric-value">${(10 - (result.spam_risk_score || 5)).toFixed(1)}</span>
                            </div>
                        </div>
                    </div>
                    
                    ${strengthsHtml}
                    ${issuesHtml}
                    ${altSubjectsHtml}
                    ${portfolioHtml}
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="copyBatchEmail(${idx})">
                        <i class="fas fa-copy"></i> Copy
                    </button>
                    <button class="btn btn-primary" onclick="downloadBatchEmailEml(${idx})">
                        <i class="fas fa-envelope"></i> Download .eml
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('batchEmailModal');
    if (existingModal) existingModal.remove();
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
}

function closeBatchEmailModal() {
    const modal = document.getElementById('batchEmailModal');
    if (modal) modal.remove();
}

function copyBatchEmail(idx) {
    const result = batchResults[idx];
    if (!result) return;
    
    const text = `Subject: ${result.subject_line}\n\n${result.body}`;
    navigator.clipboard.writeText(text).then(() => {
        showToast('Email copied!', 'success');
    });
}

function downloadBatchEmailEml(idx) {
    const result = batchResults[idx];
    if (!result) return;
    
    const emlContent = `From: <sender@example.com>
To: <recipient@${result.company_name.toLowerCase().replace(/\s+/g, '')}.com>
Subject: ${result.subject_line}
MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8

${result.body}`;
    
    const blob = new Blob([emlContent], { type: 'message/rfc822' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `email-${result.company_name.replace(/\s+/g, '-')}.eml`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

function addLogItem(text, type) {
    const log = document.getElementById('batchLog');
    const item = document.createElement('div');
    item.className = `log-item ${type}`;
    item.innerHTML = `<i class="fas fa-${type === 'success' ? 'check' : 'times'}"></i> ${text}`;
    log.appendChild(item);
    log.scrollTop = log.scrollHeight;
}

function downloadBatchResults() {
    if (batchResults.length === 0) return;
    
    const headers = ['row_number', 'company_name', 'job_url', 'status', 'subject_line', 'body', 'cta', 'score', 'clarity_score', 'tone_score', 'length_score', 'personalization_score', 'spam_risk_score'];
    let csv = headers.join(',') + '\n';
    
    batchResults.forEach(row => {
        const values = headers.map(h => {
            let val = row[h] !== undefined ? row[h] : '';
            // Convert to string and handle body specially to preserve full content
            val = String(val);
            // Always wrap in quotes and escape internal quotes
            val = '"' + val.replace(/"/g, '""') + '"';
            return val;
        });
        csv += values.join(',') + '\n';
    });
    
    // Add BOM for Excel UTF-8 compatibility
    const BOM = '\uFEFF';
    const blob = new Blob([BOM + csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `batch-results-${new Date().toISOString().slice(0,10)}.csv`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showToast('CSV downloaded!', 'success');
}

function downloadBatchResultsExcel() {
    if (batchResults.length === 0) return;
    
    // Create a simple HTML table and download as .xls (Excel compatible)
    const headers = ['#', 'Company', 'Job URL', 'Status', 'Subject Line', 'Email Body', 'CTA', 'Score', 'Clarity', 'Tone', 'Length', 'Personal', 'Spam Risk'];
    const keys = ['row_number', 'company_name', 'job_url', 'status', 'subject_line', 'body', 'cta', 'score', 'clarity_score', 'tone_score', 'length_score', 'personalization_score', 'spam_risk_score'];
    
    let html = `
        <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel">
        <head><meta charset="UTF-8">
        <style>
            td { vertical-align: top; }
            .body-cell { white-space: pre-wrap; min-width: 400px; }
        </style>
        </head>
        <body>
        <table border="1">
            <thead><tr>${headers.map(h => `<th style="background:#744B93;color:white;font-weight:bold;">${h}</th>`).join('')}</tr></thead>
            <tbody>
    `;
    
    batchResults.forEach(row => {
        html += '<tr>';
        keys.forEach(k => {
            let val = row[k] !== undefined ? row[k] : '';
            // Escape HTML and preserve newlines for body
            val = String(val).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            if (k === 'body') {
                // Preserve line breaks in body
                val = val.replace(/\n/g, '<br>');
                html += `<td class="body-cell">${val}</td>`;
            } else {
                html += `<td>${val}</td>`;
            }
        });
        html += '</tr>';
    });
    
    html += '</tbody></table></body></html>';
    
    const blob = new Blob([html], { type: 'application/vnd.ms-excel' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `batch-results-${new Date().toISOString().slice(0,10)}.xls`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showToast('Excel downloaded!', 'success');
}

function downloadTemplate() {
    const template = `job_url,company_name,recipient_name,sender_name,sender_company,sender_services
https://www.linkedin.com/jobs/view/123456,Acme Corp,Sarah Chen,Alex,TechSolutions Inc.,software development and consulting services
https://careers.google.com/jobs/results/789012,Google,Mike Johnson,Alex,TechSolutions Inc.,AI and machine learning solutions
https://jobs.apple.com/en-us/details/345678,Apple,Lisa Wang,Alex,TechSolutions Inc.,mobile app development and cloud infrastructure`;
    
    const blob = new Blob([template], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'batch_template.csv';
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showToast('Template downloaded!', 'success');
}

// ============================================
// History
// ============================================

async function loadHistory() {
    try {
        const response = await fetch(`${API_BASE}/history`);
        if (response.ok) {
            historyData = await response.json();
            displayHistory();
        }
    } catch (error) {
        console.error('Failed to load history:', error);
    }
}

function displayHistory() {
    const list = document.getElementById('historyList');
    
    if (historyData.length === 0) {
        list.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-inbox"></i>
                <p>No emails generated yet</p>
            </div>
        `;
        return;
    }
    
    list.innerHTML = historyData.map((item, idx) => `
        <div class="history-item" onclick="viewHistoryItem(${idx})">
            <div class="history-item-header">
                <div>
                    <div class="history-item-title">${item.subject_line || 'No subject'}</div>
                    <div class="history-item-meta">
                        ${item.company_name || 'Unknown'} • ${item.role || 'Unknown role'} • ${formatDate(item.timestamp)}
                    </div>
                </div>
                <span class="history-item-score">${(item.final_score || 0).toFixed(1)}</span>
            </div>
            <div class="history-item-preview">${item.body ? item.body.substring(0, 150) + '...' : ''}</div>
        </div>
    `).join('');
}

function viewHistoryItem(idx) {
    const item = historyData[idx];
    if (!item) return;
    
    console.log('History item data:', item);
    console.log('Strengths field:', item.strengths);
    console.log('Issues field:', item.issues);
    console.log('Alt subjects field:', item.alternative_subject_lines);
    
    // Switch to single tab and display
    document.querySelector('[data-tab="single"]').click();
    
    // FIXED: Better portfolio parsing
    const portfolioItems = item.portfolio_items_used ? 
        parsePortfolioItems(item.portfolio_items_used) : [];
    
    // Parse stored JSON strings for strengths, issues, alt subjects
    const parseJsonField = (field) => {
        if (!field) return [];
        // If it's already an array, return it
        if (Array.isArray(field)) return field;
        // If it's a string, try to parse it
        if (typeof field === 'string') {
            try {
                const parsed = JSON.parse(field);
                console.log('Parsed field:', field, '→', parsed);
                return Array.isArray(parsed) ? parsed : [];
            } catch (e) {
                console.error('Error parsing field:', field, e);
                return [];
            }
        }
        return [];
    };
    
    const strengths = parseJsonField(item.strengths);
    const issues = parseJsonField(item.issues);
    const altSubjects = parseJsonField(item.alternative_subject_lines);
    
    console.log('Parsed strengths:', strengths);
    console.log('Parsed issues:', issues);
    console.log('Parsed alt subjects:', altSubjects);
    
    // Format history item to match generate API response structure
    currentEmail = {
        email: {
            subject_line: item.subject_line || '',
            body: item.body || '',
            cta: item.cta || ''
        },
        evaluation: {
            overall_score: item.final_score || 0,
            clarity_score: item.clarity_score || 7,
            tone_alignment_score: item.tone_score || 7,
            length_score: item.length_score || 7,
            personalization_score: item.personalization_score || 7,
            spam_risk_score: item.spam_risk_score || 3,
            strengths: strengths,
            issues: issues
        },
        alternative_subject_lines: altSubjects,
        portfolio_items_used: portfolioItems
    };
    
    console.log('Current email object:', currentEmail);
    
    displayEmailResult(currentEmail);
}

function filterHistory() {
    const search = document.getElementById('historySearch').value.toLowerCase();
    const items = document.querySelectorAll('.history-item');
    
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(search) ? 'block' : 'none';
    });
}

function sortHistory() {
    const sort = document.getElementById('historySort').value;
    
    historyData.sort((a, b) => {
        switch (sort) {
            case 'newest':
                return new Date(b.created_at || b.timestamp) - new Date(a.created_at || a.timestamp);
            case 'oldest':
                return new Date(a.created_at || a.timestamp) - new Date(b.created_at || b.timestamp);
            case 'score-high':
                return (b.final_score || 0) - (a.final_score || 0);
            case 'score-low':
                return (a.final_score || 0) - (b.final_score || 0);
            default:
                return 0;
        }
    });
    
    displayHistory();
}

// ============================================
// HELPER: Parse Portfolio Items Correctly
// ============================================

function parsePortfolioItems(portfolioString) {
    if (!portfolioString || !portfolioString.trim()) return [];
    
    // Check if it contains "Project with" pattern
    if (portfolioString.includes('Project with')) {
        // Split by "Project with" but keep it in the result
        const parts = portfolioString.split(/(?=Project with)/);
        return parts
            .filter(p => p.trim())
            .map(p => {
                const title = p.trim();
                // Extract tech stack (remove "Project with " prefix)
                const techStack = title.replace(/^Project with\s+/i, '').trim();
                return {
                    title: title,
                    tech_stack: techStack,
                    link: '#'
                };
            });
    } else {
        // Single tech stack entry
        return [{
            title: `Project with ${portfolioString}`,
            tech_stack: portfolioString,
            link: '#'
        }];
    }
}

// ============================================
// Analytics
// ============================================

async function loadAnalytics() {
    try {
        const response = await fetch(`${API_BASE}/analytics`);
        if (response.ok) {
            const data = await response.json();
            displayAnalytics(data);
        }
    } catch (error) {
        console.error('Failed to load analytics:', error);
    }
}

function displayAnalytics(data) {
    // Store for export
    analyticsData = data;
    
    // Summary stats
    document.getElementById('totalEmails').textContent = data.total_emails || 0;
    document.getElementById('avgScore').textContent = (data.avg_score || 0).toFixed(1);
    document.getElementById('uniqueCompanies').textContent = data.unique_companies || 0;
    document.getElementById('highScoreCount').textContent = data.high_score_count || 0;
    
    // Role distribution
    const roleBars = document.getElementById('roleBars');
    const roles = data.roles_distribution || [];
    if (roles.length > 0) {
        const maxCount = Math.max(...roles.map(r => r.count));
        roleBars.innerHTML = roles.slice(0, 6).map(role => `
            <div class="role-bar-item">
                <span class="role-bar-label" title="${role.role}">${role.role}</span>
                <div class="role-bar-track">
                    <div class="role-bar-fill" style="width: ${(role.count / maxCount) * 100}%">
                        ${role.count}
                    </div>
                </div>
            </div>
        `).join('');
    } else {
        roleBars.innerHTML = '<p style="color:var(--gray-400);text-align:center;">No data yet</p>';
    }
    
    // Score distribution
    const scoreDistribution = document.getElementById('scoreDistribution');
    const scores = data.score_distribution || [];
    if (scores.length > 0) {
        const maxScoreCount = Math.max(...scores.map(s => s.count));
        scoreDistribution.innerHTML = scores.map(s => `
            <div class="score-bar">
                <div class="score-bar-fill" style="height: ${(s.count / maxScoreCount) * 150}px" title="${s.count} emails in ${s.range} range"></div>
                <span class="score-bar-label">${s.range}</span>
            </div>
        `).join('');
    } else {
        scoreDistribution.innerHTML = '<p style="color:var(--gray-400);text-align:center;">No data yet</p>';
    }
    
    // Recent activity
    const recentActivity = document.getElementById('recentActivity');
    const recent = data.recent_activity || [];
    if (recent.length > 0) {
        recentActivity.innerHTML = recent.map(item => `
            <div class="activity-item">
                <div class="activity-icon"><i class="fas fa-envelope"></i></div>
                <div class="activity-info">
                    <div class="activity-title">${item.company || 'Unknown'}</div>
                    <div class="activity-meta">${item.role || 'Unknown role'} • ${formatDate(item.created_at)}</div>
                </div>
                <span class="activity-score">${(item.score || 0).toFixed(1)}</span>
            </div>
        `).join('');
    } else {
        recentActivity.innerHTML = '<div class="empty-state-inline"><i class="fas fa-inbox"></i><p>No recent activity</p></div>';
    }
    
    // Template performance (call without await since displayAnalytics is not async)
    loadTemplatePerformance();
}

async function loadTemplatePerformance() {
    try {
        const response = await fetch(`${API_BASE}/template-performance`);
        if (response.ok) {
            const data = await response.json();
            displayTemplatePerformance(data);
        }
    } catch (error) {
        console.error('Failed to load template performance:', error);
    }
}

function displayTemplatePerformance(templates) {
    const container = document.getElementById('templatePerformance');
    
    if (!templates || templates.length === 0) {
        container.innerHTML = `
            <div class="empty-state">
                <i class="fas fa-chart-bar"></i>
                <p>No template usage data yet</p>
            </div>
        `;
        return;
    }
    
    container.innerHTML = templates.map((template, index) => {
        const scoreClass = template.avg_score >= 8.0 ? 'high' : template.avg_score >= 7.5 ? 'medium' : 'low';
        const itemClass = template.avg_score >= 8.0 ? 'high-score' : template.avg_score >= 7.5 ? 'medium-score' : 'low-score';
        
        return `
            <div class="template-item ${itemClass}">
                <div class="template-header">
                    <span class="template-title">${template.template_title || 'Unknown Template'}</span>
                    <span class="template-rank">#${index + 1}</span>
                </div>
                <div class="template-stats">
                    <div class="template-stat">
                        <span class="template-stat-label">Avg Score</span>
                        <span class="template-stat-value">${template.avg_score.toFixed(1)}/10</span>
                    </div>
                    <div class="template-stat">
                        <span class="template-stat-label">Used</span>
                        <span class="template-stat-value">${template.usage_count}x</span>
                    </div>
                </div>
                <div class="template-progress">
                    <div class="template-progress-fill ${scoreClass}" style="width: ${template.avg_score * 10}%"></div>
                </div>
            </div>
        `;
    }).join('');
}

// ============================================
// Export Functions
// ============================================

// Helper function to escape XML special characters (used by all export functions)
function escapeXml(str) {
    if (!str) return '';
    return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// Helper function to parse JSON fields for export
function parseJsonField(field) {
    if (!field) return '';
    try {
        const parsed = typeof field === 'string' ? JSON.parse(field.replace(/'/g, '"')) : field;
        return Array.isArray(parsed) ? parsed.join('; ') : parsed;
    } catch {
        return field;
    }
}

function exportHistoryExcel() {
    if (!historyData || historyData.length === 0) {
        showToast('No data to export', 'error');
        return;
    }
    
    let xml = '<?xml version="1.0"?><?mso-application progid="Excel.Sheet"?>';
    xml += '<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">';
    xml += '<Worksheet ss:Name="Email History"><Table>';
    
    // Headers
    xml += '<Row>';
    const headers = [
        'ID', 'Company', 'Role', 'Industry', 'Recipient', 'Subject Line', 'Email Body', 'CTA',
        'Initial Score', 'Final Score', 'Clarity', 'Tone', 'Length', 
        'Personalization', 'Spam Risk', 'Optimization Applied',
        'Strengths', 'Issues', 'Alternative Subject Lines',
        'Sender Name', 'Sender Company', 'Created At'
    ];
    headers.forEach(h => {
        xml += `<Cell><Data ss:Type="String">${h}</Data></Cell>`;
    });
    xml += '</Row>';
    
    // Data rows
    historyData.forEach(item => {
        xml += '<Row>';
        xml += `<Cell><Data ss:Type="Number">${item.id || 0}</Data></Cell>`;
        xml += `<Cell><Data ss:Type="String">${escapeXml(item.company_name)}</Data></Cell>`;
        xml += `<Cell><Data ss:Type="String">${escapeXml(item.role)}</Data></Cell>`;
        xml += `<Cell><Data ss:Type="String">${escapeXml(item.industry)}</Data></Cell>`;
        xml += `<Cell><Data ss:Type="String">${escapeXml(item.recipient_name)}</Data></Cell>`;
        xml += `<Cell><Data ss:Type="String">${escapeXml(item.subject_line)}</Data></Cell>`;
        xml += `<Cell><Data ss:Type="String">${escapeXml(item.body)}</Data></Cell>`;
        xml += `<Cell><Data ss:Type="String">${escapeXml(item.cta)}</Data></Cell>`;
        xml += `<Cell><Data ss:Type="Number">${item.initial_score || 0}</Data></Cell>`;
        xml += `<Cell><Data ss:Type="Number">${item.final_score || 0}</Data></Cell>`;
        xml += `<Cell><Data ss:Type="Number">${item.clarity_score || 0}</Data></Cell>`;
        xml += `<Cell><Data ss:Type="Number">${item.tone_score || 0}</Data></Cell>`;
        xml += `<Cell><Data ss:Type="Number">${item.length_score || 0}</Data></Cell>`;
        xml += `<Cell><Data ss:Type="Number">${item.personalization_score || 0}</Data></Cell>`;
        xml += `<Cell><Data ss:Type="Number">${item.spam_risk_score || 0}</Data></Cell>`;
        xml += `<Cell><Data ss:Type="String">${item.optimization_applied ? 'Yes' : 'No'}</Data></Cell>`;
        xml += `<Cell><Data ss:Type="String">${escapeXml(parseJsonField(item.strengths))}</Data></Cell>`;
        xml += `<Cell><Data ss:Type="String">${escapeXml(parseJsonField(item.issues))}</Data></Cell>`;
        xml += `<Cell><Data ss:Type="String">${escapeXml(parseJsonField(item.alternative_subject_lines))}</Data></Cell>`;
        xml += `<Cell><Data ss:Type="String">${escapeXml(item.sender_name)}</Data></Cell>`;
        xml += `<Cell><Data ss:Type="String">${escapeXml(item.sender_company)}</Data></Cell>`;
        xml += `<Cell><Data ss:Type="String">${escapeXml(item.created_at)}</Data></Cell>`;
        xml += '</Row>';
    });
    
    xml += '</Table></Worksheet></Workbook>';
    
    downloadFile(xml, 'email_history.xls', 'application/vnd.ms-excel');
    showToast('Excel exported successfully!');
}

// Store analytics data for export
let analyticsData = null;

async function exportAnalytics() {
    if (!analyticsData) {
        // Fetch fresh data if not available
        try {
            const response = await fetch(`${API_BASE}/analytics`);
            if (response.ok) {
                analyticsData = await response.json();
            }
        } catch (error) {
            showToast('Failed to fetch analytics', 'error');
            return;
        }
    }
    
    if (!analyticsData) {
        showToast('No analytics data available', 'error');
        return;
    }
    
    // Fetch template performance data
    let templatePerformance = [];
    try {
        const response = await fetch(`${API_BASE}/template-performance`);
        if (response.ok) {
            templatePerformance = await response.json();
        }
    } catch (error) {
        console.error('Failed to fetch template performance:', error);
    }
    
    // Create simplified Excel XML export
    const timestamp = new Date().toISOString().split('T')[0];
    
    let xml = '<?xml version="1.0"?>\n';
    xml += '<?mso-application progid="Excel.Sheet"?>\n';
    xml += '<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">\n';
    
    // Styles
    xml += '<Styles>\n';
    xml += '<Style ss:ID="Header">\n';
    xml += '  <Font ss:Bold="1" ss:Size="12" ss:Color="#FFFFFF"/>\n';
    xml += '  <Interior ss:Color="#4A90A4" ss:Pattern="Solid"/>\n';
    xml += '</Style>\n';
    xml += '<Style ss:ID="Title">\n';
    xml += '  <Font ss:Bold="1" ss:Size="14"/>\n';
    xml += '</Style>\n';
    xml += '</Styles>\n';
    
    // Summary Sheet
    xml += '<Worksheet ss:Name="Summary">\n';
    xml += '<Table>\n';
    xml += '<Column ss:Width="200"/>\n';
    xml += '<Column ss:Width="100"/>\n';
    xml += '<Row><Cell ss:StyleID="Title"><Data ss:Type="String">EmailCraft AI - Analytics Summary</Data></Cell></Row>\n';
    xml += `<Row><Cell><Data ss:Type="String">Exported: ${timestamp}</Data></Cell></Row>\n`;
    xml += '<Row></Row>\n';
    xml += '<Row><Cell ss:StyleID="Header"><Data ss:Type="String">Metric</Data></Cell><Cell ss:StyleID="Header"><Data ss:Type="String">Value</Data></Cell></Row>\n';
    xml += `<Row><Cell><Data ss:Type="String">Total Emails</Data></Cell><Cell><Data ss:Type="Number">${analyticsData.total_emails || 0}</Data></Cell></Row>\n`;
    xml += `<Row><Cell><Data ss:Type="String">Average Score</Data></Cell><Cell><Data ss:Type="Number">${(analyticsData.avg_score || 0).toFixed(1)}</Data></Cell></Row>\n`;
    xml += `<Row><Cell><Data ss:Type="String">Unique Companies</Data></Cell><Cell><Data ss:Type="Number">${analyticsData.unique_companies || 0}</Data></Cell></Row>\n`;
    xml += `<Row><Cell><Data ss:Type="String">High Score Count (8+)</Data></Cell><Cell><Data ss:Type="Number">${analyticsData.high_score_count || 0}</Data></Cell></Row>\n`;
    xml += '</Table>\n';
    xml += '</Worksheet>\n';
    
    // Emails by Role Sheet
    xml += '<Worksheet ss:Name="Emails by Role">\n';
    xml += '<Table>\n';
    xml += '<Column ss:Width="250"/>\n';
    xml += '<Column ss:Width="80"/>\n';
    xml += '<Row><Cell ss:StyleID="Header"><Data ss:Type="String">Role</Data></Cell><Cell ss:StyleID="Header"><Data ss:Type="String">Count</Data></Cell></Row>\n';
    (analyticsData.roles_distribution || []).forEach(r => {
        xml += `<Row><Cell><Data ss:Type="String">${escapeXml(r.role)}</Data></Cell><Cell><Data ss:Type="Number">${r.count}</Data></Cell></Row>\n`;
    });
    xml += '</Table>\n';
    xml += '</Worksheet>\n';
    
    // Score Distribution Sheet
    xml += '<Worksheet ss:Name="Score Distribution">\n';
    xml += '<Table>\n';
    xml += '<Column ss:Width="120"/>\n';
    xml += '<Column ss:Width="80"/>\n';
    xml += '<Row><Cell ss:StyleID="Header"><Data ss:Type="String">Score Range</Data></Cell><Cell ss:StyleID="Header"><Data ss:Type="String">Count</Data></Cell></Row>\n';
    (analyticsData.score_distribution || []).forEach(s => {
        xml += `<Row><Cell><Data ss:Type="String">${s.range}</Data></Cell><Cell><Data ss:Type="Number">${s.count}</Data></Cell></Row>\n`;
    });
    xml += '</Table>\n';
    xml += '</Worksheet>\n';
    
    // Template Performance Sheet
    xml += '<Worksheet ss:Name="Template Performance">\n';
    xml += '<Table>\n';
    xml += '<Column ss:Width="250"/>\n';
    xml += '<Column ss:Width="100"/>\n';
    xml += '<Column ss:Width="80"/>\n';
    xml += '<Row><Cell ss:StyleID="Header"><Data ss:Type="String">Template</Data></Cell><Cell ss:StyleID="Header"><Data ss:Type="String">Average Score</Data></Cell><Cell ss:StyleID="Header"><Data ss:Type="String">Usage Count</Data></Cell></Row>\n';
    (templatePerformance || []).forEach(t => {
        xml += `<Row><Cell><Data ss:Type="String">${escapeXml(t.template_title || 'Unknown')}</Data></Cell><Cell><Data ss:Type="Number">${(t.avg_score || 0).toFixed(1)}</Data></Cell><Cell><Data ss:Type="Number">${t.usage_count || 0}</Data></Cell></Row>\n`;
    });
    xml += '</Table>\n';
    xml += '</Worksheet>\n';
    
    xml += '</Workbook>';
    
    downloadFile(xml, `analytics_${timestamp}.xls`, 'application/vnd.ms-excel');
    showToast('Analytics exported to Excel successfully!');
}

function downloadFile(content, filename, type) {
    const blob = new Blob([content], { type });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
}

// ============================================
// Toast Notifications
// ============================================

function showToast(message, type = 'success') {
    const toast = document.getElementById('toast');
    const toastMessage = document.getElementById('toastMessage');
    
    toastMessage.textContent = message;
    toast.className = `toast ${type}`;
    
    // Update icon
    const icon = toast.querySelector('i');
    icon.className = type === 'success' ? 'fas fa-check-circle' : 'fas fa-exclamation-circle';
    
    toast.classList.add('show');
    
    setTimeout(() => {
        toast.classList.remove('show');
    }, 3000);
}

// ============================================
// Utility Functions
// ============================================

function formatDate(dateStr) {
    if (!dateStr) return '';
    const date = new Date(dateStr);
    const now = new Date();
    const diff = now - date;
    
    // Less than 1 hour
    if (diff < 3600000) {
        const mins = Math.floor(diff / 60000);
        return `${mins}m ago`;
    }
    // Less than 24 hours
    if (diff < 86400000) {
        const hours = Math.floor(diff / 3600000);
        return `${hours}h ago`;
    }
    // Less than 7 days
    if (diff < 604800000) {
        const days = Math.floor(diff / 86400000);
        return `${days}d ago`;
    }
    // Otherwise show date
    return date.toLocaleDateString();
}

// ============================================
// Initialize
// ============================================

document.addEventListener('DOMContentLoaded', () => {
    // Theme is already initialized by theme.js
    // Just ensure toggle buttons are set up
    if (window.themeManager) {
        window.themeManager.updateToggleButton();
    }
    
    // Check API health
    fetch(`${API_BASE}/health`)
        .then(res => res.json())
        .then(data => {
            console.log('API Status:', data.status);
        })
        .catch(err => {
            console.warn('API not available:', err);
            showToast('Backend not connected. Start the API server.', 'error');
        });
});


// ============================================
// Lead Generation
// ============================================

let leadGenerationResults = [];

document.getElementById('leadForm')?.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const businessType = document.getElementById('businessType').value;
    const location = document.getElementById('location').value;
    const maxLeads = parseInt(document.getElementById('maxLeads').value) || 20;
    const senderName = document.getElementById('leadSenderName').value;
    const senderCompany = document.getElementById('leadSenderCompany').value;
    const senderServices = document.getElementById('leadSenderServices').value;
    
    // Show loading state in preview card
    document.getElementById('leadPreviewEmptyState').style.display = 'none';
    document.getElementById('leadPreviewResultState').style.display = 'none';
    document.getElementById('leadPreviewLoadingState').style.display = 'block';
    document.getElementById('leadScoreBadge').style.display = 'none';
    
    // Animate loading steps
    animateLeadLoadingSteps();
    
    document.getElementById('leadResults').style.display = 'none';
    document.getElementById('generateLeadsBtn').disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/generate-from-leads`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                business_type: businessType,
                location: location,
                max_results: maxLeads,
                sender_name: senderName,
                sender_company: senderCompany,
                sender_services: senderServices,
                tone: 'professional'
            })
        });
        
        if (!response.ok) {
            const error = await response.json();
            throw new Error(error.detail || 'Lead generation failed');
        }
        
        const data = await response.json();
        leadGenerationResults = data.results;
        
        // Display results
        displayLeadResults(data);
        
        showToast('Lead generation complete!', 'success');
        
    } catch (error) {
        console.error('Lead generation error:', error);
        showToast(error.message || 'Lead generation failed', 'error');
        // Clear loading animation
        clearInterval(window.leadLoadingInterval);
        document.querySelectorAll('#leadPreviewLoadingState .loading-steps .step').forEach(step => {
            step.classList.remove('active', 'done');
        });
        // Reset preview card to empty state on error
        document.getElementById('leadPreviewLoadingState').style.display = 'none';
        document.getElementById('leadPreviewEmptyState').style.display = 'block';
    } finally {
        document.getElementById('generateLeadsBtn').disabled = false;
    }
});

function displayLeadResults(data) {
    // Clear loading animation
    clearInterval(window.leadLoadingInterval);
    document.querySelectorAll('#leadPreviewLoadingState .loading-steps .step').forEach(step => {
        step.classList.remove('active', 'done');
    });
    
    // Update stats
    document.getElementById('leadTotalCount').textContent = data.total_leads;
    document.getElementById('leadSuccessCount').textContent = data.successful_emails;
    document.getElementById('leadFailedCount').textContent = data.failed_emails;
    document.getElementById('leadAvgScore').textContent = data.average_score.toFixed(1);
    
    // Store results globally for modal access
    leadGenerationResults = data.results;
    
    // Show preview card with first successful email
    showLeadPreview(0);
    
    // Populate table
    const tbody = document.getElementById('leadResultsTableBody');
    tbody.innerHTML = '';
    
    data.results.forEach((result, index) => {
        const row = document.createElement('tr');
        const lead = result.lead;
        const email = result.email;
        const status = result.status;
        
        // Status check (match batch email exactly)
        const statusClass = status === 'success' ? 'success' : 'failed';
        const scoreDisplay = status === 'success' ? result.quality_score.toFixed(1) : '-';
        
        // Truncate subject line (same as batch email)
        const truncatedSubject = email && email.subject_line ? 
            (email.subject_line.length > 35 ? email.subject_line.substring(0, 35) + '...' : email.subject_line) 
            : '-';
        
        // Build metrics display (same as batch email)
        const metricsHtml = status === 'success' ? `
            <div class="metrics-mini">
                <span title="Clarity">C:${(result.clarity_score || 0).toFixed(1)}</span>
                <span title="Tone">T:${(result.tone_score || 0).toFixed(1)}</span>
                <span title="Personal">P:${(result.personalization_score || 0).toFixed(1)}</span>
                <span title="Length">L:${(result.length_score || 0).toFixed(1)}</span>
                <span title="Spam Safe">S:${(10 - (result.spam_risk_score || 5)).toFixed(1)}</span>
            </div>
        ` : '-';
        
        // Remove click handler since we don't show individual previews anymore
        row.style.cursor = 'default';
        
        row.innerHTML = `
            <td>${index + 1}</td>
            <td>
                <strong>${lead.company_name}</strong>
                ${lead.website ? `<br><small><a href="${lead.website}" target="_blank">${lead.website}</a></small>` : ''}
                ${lead.email ? `<br><small><a href="mailto:${lead.email}">${lead.email}</a></small>` : ''}
                ${lead.decision_maker_name ? `<br><small>${lead.decision_maker_name}</small>` : ''}
            </td>
            <td title="${email ? email.subject_line : ''}">${truncatedSubject}</td>
            <td><span class="score-badge ${result.quality_score >= 7 ? 'good' : result.quality_score >= 5 ? 'ok' : 'low'}">${scoreDisplay}</span></td>
            <td>${metricsHtml}</td>
            <td><span class="status-badge ${statusClass}">${status}</span></td>
            <td>
                ${status === 'success' ? `
                    <button class="btn-icon" onclick="event.stopPropagation(); viewLeadEmail(${index})" title="View Email">
                        <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn-icon" onclick="event.stopPropagation(); copyLeadEmail(${index})" title="Copy">
                        <i class="fas fa-copy"></i>
                    </button>
                ` : '-'}
            </td>
        `;
        
        tbody.appendChild(row);
    });
    
    // Show results
    document.getElementById('leadResults').style.display = 'block';
}

function showLeadPreview(index) {
    // Hide empty/loading states, show result
    document.getElementById('leadPreviewEmptyState').style.display = 'none';
    document.getElementById('leadPreviewLoadingState').style.display = 'none';
    document.getElementById('leadPreviewResultState').style.display = 'block';
    
    // Hide score badge (not needed for success message)
    document.getElementById('leadScoreBadge').style.display = 'none';
    
    // Calculate stats
    const totalLeads = leadGenerationResults.length;
    const successfulLeads = leadGenerationResults.filter(r => r.status === 'success').length;
    
    // Update stats in success message
    document.getElementById('leadPreviewTotal').textContent = totalLeads;
    document.getElementById('leadPreviewSuccess').textContent = successfulLeads;
}

function viewLeadEmail(index) {
    const result = leadGenerationResults[index];
    if (!result || !result.email) return;
    
    const email = result.email;
    const lead = result.lead;
    
    // Build strengths HTML (same as batch email)
    const strengthsHtml = result.strengths && result.strengths.length > 0 ? `
        <div class="modal-section strengths-section">
            <h4><i class="fas fa-check-circle"></i> Strengths</h4>
            <ul>${result.strengths.map(s => `<li>${s}</li>`).join('')}</ul>
        </div>
    ` : '';
    
    // Build issues HTML (same as batch email)
    const issuesHtml = result.issues && result.issues.length > 0 ? `
        <div class="modal-section issues-section">
            <h4><i class="fas fa-exclamation-triangle"></i> Areas to Improve</h4>
            <ul>${result.issues.map(i => `<li>${i}</li>`).join('')}</ul>
        </div>
    ` : '';
    
    // Build portfolio items HTML (same as batch email)
    const portfolioHtml = result.portfolio_items && result.portfolio_items.length > 0 ? `
        <div class="modal-section portfolio-section">
            <h4><i class="fas fa-briefcase"></i> Portfolio Items Included</h4>
            <div class="portfolio-list">
                ${result.portfolio_items.map(p => `
                    <div class="portfolio-item-mini">
                        <strong>${p.title || 'Project'}</strong>
                        <span class="tech-stack">${p.tech_stack || ''}</span>
                        ${p.link ? `<a href="${p.link}" target="_blank"><i class="fas fa-external-link-alt"></i></a>` : ''}
                    </div>
                `).join('')}
            </div>
        </div>
    ` : '';
    
    // Build alternative subjects HTML (same as batch email)
    const altSubjectsHtml = result.alt_subjects && result.alt_subjects.length > 0 ? `
        <div class="modal-section alt-subjects-section">
            <h4><i class="fas fa-lightbulb"></i> Alternative Subject Lines</h4>
            <ul class="alt-subjects-list">
                ${result.alt_subjects.map(s => `<li>${s}</li>`).join('')}
            </ul>
        </div>
    ` : '';
    
    // Create modal content with all metrics (same as batch email)
    const modalHtml = `
        <div class="batch-email-modal" id="leadEmailModal">
            <div class="modal-content">
                <div class="modal-header">
                    <h3>${lead.company_name}</h3>
                    <button onclick="closeLeadEmailModal()" class="close-btn"><i class="fas fa-times"></i></button>
                </div>
                <div class="modal-body">
                    <!-- Lead Info -->
                    <div class="email-field" style="background: var(--card-bg); padding: 15px; border-radius: 8px; margin-bottom: 20px;">
                        <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 10px;">
                            ${lead.website ? `<div><strong>Website:</strong> <a href="${lead.website}" target="_blank">${lead.website}</a></div>` : ''}
                            ${lead.email ? `<div><strong>Email:</strong> <a href="mailto:${lead.email}">${lead.email}</a></div>` : ''}
                            ${lead.decision_maker_name ? `<div><strong>Contact:</strong> ${lead.decision_maker_name}</div>` : ''}
                            ${lead.decision_maker_title ? `<div><strong>Title:</strong> ${lead.decision_maker_title}</div>` : ''}
                            ${lead.phone ? `<div><strong>Phone:</strong> ${lead.phone}</div>` : ''}
                            ${lead.address ? `<div><strong>Address:</strong> ${lead.address}</div>` : ''}
                        </div>
                    </div>
                    
                    <!-- Email Content -->
                    <div class="email-field">
                        <label>Subject:</label>
                        <p>${email.subject_line}</p>
                    </div>
                    <div class="email-field">
                        <label>Body:</label>
                        <p style="white-space: pre-wrap;">${email.body}</p>
                    </div>
                    <div class="email-field">
                        <label>CTA:</label>
                        <p>${email.cta}</p>
                    </div>
                    
                    <!-- Evaluation Metrics -->
                    <div class="modal-metrics">
                        <h4>Evaluation Metrics</h4>
                        <div class="metrics-grid">
                            <div class="metric-item">
                                <span class="metric-label">Overall Score</span>
                                <span class="metric-value score">${result.quality_score.toFixed(1)}/10</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Clarity</span>
                                <span class="metric-value">${(result.clarity_score || 0).toFixed(1)}</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Tone</span>
                                <span class="metric-value">${(result.tone_score || 0).toFixed(1)}</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Length</span>
                                <span class="metric-value">${(result.length_score || 0).toFixed(1)}</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Personalization</span>
                                <span class="metric-value">${(result.personalization_score || 0).toFixed(1)}</span>
                            </div>
                            <div class="metric-item">
                                <span class="metric-label">Spam Safe</span>
                                <span class="metric-value">${(10 - (result.spam_risk_score || 5)).toFixed(1)}</span>
                            </div>
                        </div>
                    </div>
                    
                    ${strengthsHtml}
                    ${issuesHtml}
                    ${altSubjectsHtml}
                    ${portfolioHtml}
                </div>
                <div class="modal-footer">
                    <button class="btn btn-secondary" onclick="copyLeadEmail(${index})">
                        <i class="fas fa-copy"></i> Copy
                    </button>
                    <button class="btn btn-primary" onclick="downloadLeadEmailEml(${index})">
                        <i class="fas fa-envelope"></i> Download .eml
                    </button>
                </div>
            </div>
        </div>
    `;
    
    // Remove existing modal if any
    const existingModal = document.getElementById('leadEmailModal');
    if (existingModal) existingModal.remove();
    
    document.body.insertAdjacentHTML('beforeend', modalHtml);
}

function closeLeadEmailModal() {
    const modal = document.getElementById('leadEmailModal');
    if (modal) modal.remove();
}

function copyLeadEmail(index) {
    const result = leadGenerationResults[index];
    if (!result || !result.email) return;
    
    const email = result.email;
    const emailText = `Subject: ${email.subject_line}\n\n${email.body}\n\n${email.cta}`;
    
    navigator.clipboard.writeText(emailText);
    showToast('Email copied to clipboard!', 'success');
}

function downloadLeadEmailEml(index) {
    const result = leadGenerationResults[index];
    if (!result || !result.email) return;
    
    const email = result.email;
    const lead = result.lead;
    const senderName = document.getElementById('leadSenderName').value || 'Alex';
    const senderEmail = 'sender@example.com'; // Placeholder
    
    const emlContent = `MIME-Version: 1.0
Content-Type: text/plain; charset=UTF-8
From: ${senderName} <${senderEmail}>
To: ${lead.decision_maker_name || 'Contact'} <${lead.email || 'contact@' + lead.company_name.toLowerCase().replace(/\s+/g, '') + '.com'}>
Subject: ${email.subject_line}
Date: ${new Date().toUTCString()}

${email.body}

${email.cta}
`;
    
    const blob = new Blob([emlContent], { type: 'message/rfc822' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `lead-email-${lead.company_name.replace(/\s+/g, '-')}.eml`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    showToast('Email downloaded as .eml file!', 'success');
}

function resetLeadGeneration() {
    document.getElementById('leadResults').style.display = 'none';
    document.getElementById('leadForm').reset();
    leadGenerationResults = [];
    
    // Clear loading animation
    clearInterval(window.leadLoadingInterval);
    document.querySelectorAll('#leadPreviewLoadingState .loading-steps .step').forEach(step => {
        step.classList.remove('active', 'done');
    });
    
    // Reset preview card to empty state
    document.getElementById('leadPreviewResultState').style.display = 'none';
    document.getElementById('leadPreviewLoadingState').style.display = 'none';
    document.getElementById('leadPreviewEmptyState').style.display = 'block';
    document.getElementById('leadScoreBadge').style.display = 'none';
}

function downloadLeadResultsExcel() {
    if (leadGenerationResults.length === 0) {
        showToast('No results to download', 'error');
        return;
    }
    
    console.log('Downloading results:', leadGenerationResults.length, 'items');
    console.log('Sample result:', leadGenerationResults[0]);
    
    // Comprehensive headers including all lead and email data
    const headers = [
        '#', 'Status', 'Company Name', 'Website', 'Phone', 'Address', 
        'Category', 'Rating', 'Reviews', 'Email', 'Contact Name', 'Contact Title',
        'Subject Line', 'Email Body', 'CTA', 
        'Quality Score', 'Clarity', 'Tone', 'Length', 'Personalization', 'Spam Risk',
        'Strengths', 'Issues', 'Alternative Subjects', 'Portfolio Items'
    ];
    
    const rows = leadGenerationResults.map((result, index) => {
        const lead = result.lead || {};
        const email = result.email || {};
        
        // Format arrays as readable text
        const strengths = (result.strengths || []).join('; ');
        const issues = (result.issues || []).join('; ');
        const altSubjects = (result.alt_subjects || []).join('; ');
        const portfolioItems = (result.portfolio_items || [])
            .map(p => `${p.title || 'Untitled'} (${p.tech_stack || 'N/A'})`)
            .join('; ');
        
        // Clean email body - replace newlines with spaces to prevent CSV row breaks
        const cleanBody = (email.body || '').replace(/\r?\n/g, ' ').replace(/\s+/g, ' ').trim();
        
        return [
            index + 1,
            result.status || 'unknown',
            lead.company_name || '',
            lead.website || '',
            lead.phone || '',
            lead.address || '',
            lead.category || '',
            lead.rating || '',
            lead.reviews_count || '',
            lead.email || '',
            lead.decision_maker_name || '',
            lead.decision_maker_title || '',
            email.subject_line || '',
            cleanBody,
            email.cta || '',
            result.status === 'success' ? (result.quality_score || 0).toFixed(1) : '0',
            result.status === 'success' ? (result.clarity_score || 0).toFixed(1) : '0',
            result.status === 'success' ? (result.tone_score || 0).toFixed(1) : '0',
            result.status === 'success' ? (result.length_score || 0).toFixed(1) : '0',
            result.status === 'success' ? (result.personalization_score || 0).toFixed(1) : '0',
            result.status === 'success' ? (result.spam_risk_score || 0).toFixed(1) : '0',
            strengths,
            issues,
            altSubjects,
            portfolioItems
        ];
    });
    
    console.log('Total rows to export:', rows.length);
    console.log('Sample row:', rows[0]);
    
    // Create CSV content with proper escaping
    const csvContent = [
        headers.join(','),
        ...rows.map(row => row.map(cell => {
            // Convert to string and escape quotes
            const str = String(cell).replace(/"/g, '""');
            // Wrap in quotes if contains comma, newline, or quote
            return /[",\n\r]/.test(str) ? `"${str}"` : str;
        }).join(','))
    ].join('\n');
    
    console.log('CSV size:', csvContent.length, 'characters');
    
    // Add BOM for Excel UTF-8 compatibility
    const BOM = '\uFEFF';
    const blob = new Blob([BOM + csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `lead-generation-results-${new Date().toISOString().split('T')[0]}.csv`;
    a.click();
    URL.revokeObjectURL(url);
    
    showToast('Results downloaded with all data!', 'success');
}
