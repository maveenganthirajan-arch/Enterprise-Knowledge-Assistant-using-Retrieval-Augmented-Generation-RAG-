let currentTab = 'chat';
let isQuerying = false;

document.addEventListener('DOMContentLoaded', () => {
    fetchDocuments();
    fetchLatestEvaluation();
    setupDragAndDrop();
});

function switchTab(tab) {
    currentTab = tab;
    ['chat', 'documents', 'evaluation'].forEach(t => {
        const view = document.getElementById(`view-${t}`);
        const tabBtn = document.getElementById(`tab-${t}`);
        if (t === tab) {
            view.classList.remove('hidden');
            tabBtn.className = "px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center space-x-2 bg-blue-600 text-white shadow";
        } else {
            view.classList.add('hidden');
            tabBtn.className = "px-3.5 py-1.5 text-xs font-semibold rounded-lg transition-all flex items-center space-x-2 text-slate-400 hover:text-slate-200";
        }
    });

    if (tab === 'documents') {
        fetchDocuments();
    } else if (tab === 'evaluation') {
        fetchLatestEvaluation();
    }
}

function usePrompt(text) {
    const input = document.getElementById('query-input');
    input.value = text;
    input.focus();
}

async function handleChatSubmit(e) {
    e.preventDefault();
    const input = document.getElementById('query-input');
    const question = input.value.trim();
    if (!question || isQuerying) return;

    // Remove welcome screen if present
    const welcome = document.getElementById('chat-welcome');
    if (welcome) welcome.style.display = 'none';

    // Append User Message
    appendUserMessage(question);
    input.value = '';
    isQuerying = true;
    document.getElementById('send-button').disabled = true;

    // Append Loading Bubble
    const loadingId = appendLoadingMessage();

    try {
        const resp = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
        });

        if (!resp.ok) {
            throw new Error(`Server returned error: ${resp.status}`);
        }

        const data = await resp.json();
        removeMessage(loadingId);
        appendAssistantMessage(data);
    } catch (err) {
        removeMessage(loadingId);
        appendErrorMessage(err.message || 'Failed to generate answer. Check server logs.');
    } finally {
        isQuerying = false;
        document.getElementById('send-button').disabled = false;
    }
}

function appendUserMessage(text) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'flex justify-end max-w-4xl mx-auto';
    div.innerHTML = `
        <div class="max-w-2xl bg-blue-600 text-white px-5 py-3 rounded-2xl rounded-tr-sm shadow-md text-sm leading-relaxed">
            <p>${escapeHtml(text)}</p>
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function appendLoadingMessage() {
    const container = document.getElementById('chat-messages');
    const id = 'loading-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'flex justify-start max-w-4xl mx-auto items-start space-x-3';
    div.innerHTML = `
        <div class="w-8 h-8 rounded-xl bg-slate-800 border border-slate-700 flex items-center justify-center text-blue-400 flex-shrink-0">
            <i class="fa-solid fa-robot text-sm"></i>
        </div>
        <div class="bg-slate-800/90 border border-slate-700/80 px-5 py-3.5 rounded-2xl rounded-tl-sm text-xs text-slate-400 flex items-center space-x-2.5">
            <span class="w-2 h-2 rounded-full bg-blue-400 animate-ping"></span>
            <span>Retrieving company documents & verifying facts...</span>
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return id;
}

function removeMessage(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

function appendAssistantMessage(data) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'flex justify-start max-w-4xl mx-auto items-start space-x-3';

    const isInsufficient = data.status === 'insufficient_evidence';
    
    // Status pill
    let statusPill = isInsufficient
        ? `<span class="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/30 flex items-center space-x-1">
             <i class="fa-solid fa-triangle-exclamation"></i>
             <span>Insufficient Evidence</span>
           </span>`
        : `<span class="px-2 py-0.5 rounded-md text-[10px] font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 flex items-center space-x-1">
             <i class="fa-solid fa-check"></i>
             <span>Context Grounded</span>
           </span>`;

    // Citations HTML
    let citationsHtml = '';
    if (data.sources && data.sources.length > 0) {
        citationsHtml = `
            <div class="mt-4 pt-3 border-t border-slate-700/60">
                <span class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider block mb-2">Verified Sources (${data.sources.length})</span>
                <div class="grid grid-cols-1 md:grid-cols-2 gap-2">
                    ${data.sources.map((s, idx) => `
                        <div class="p-2.5 rounded-xl bg-slate-900/60 border border-slate-700/50 hover:border-blue-500/50 transition text-xs">
                            <div class="flex items-center justify-between text-[11px] font-semibold text-blue-300 mb-1">
                                <span class="truncate max-w-[180px]"><i class="fa-regular fa-file-lines mr-1"></i>${escapeHtml(s.document_name)}</span>
                                <span class="px-1.5 py-0.5 rounded bg-slate-800 text-slate-300">Page ${s.page || 1}</span>
                            </div>
                            <p class="text-[11px] text-slate-400 italic line-clamp-2">"${escapeHtml(s.snippet)}"</p>
                            <div class="mt-1 flex items-center justify-between text-[10px] text-slate-500">
                                <span>Relevance: ${(s.similarity_score * 100).toFixed(1)}%</span>
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;
    }

    div.innerHTML = `
        <div class="w-8 h-8 rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 flex items-center justify-center text-white flex-shrink-0 shadow-md">
            <i class="fa-solid fa-robot text-xs"></i>
        </div>
        <div class="flex-1 bg-slate-800/90 border border-slate-700/80 p-5 rounded-2xl rounded-tl-sm shadow-xl space-y-3">
            <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2">
                    ${statusPill}
                    <span class="text-[10px] text-slate-400"><i class="fa-solid fa-bolt mr-1"></i>${data.response_time_ms} ms</span>
                </div>
                <!-- Feedback buttons -->
                <div class="flex items-center space-x-1" id="feedback-ctrls-${data.query_id}">
                    <button onclick="openFeedbackModal('${data.query_id}', 1)" class="w-7 h-7 rounded-lg hover:bg-slate-700 text-slate-400 hover:text-emerald-400 transition flex items-center justify-center text-xs" title="Helpful answer">
                        <i class="fa-regular fa-thumbs-up"></i>
                    </button>
                    <button onclick="openFeedbackModal('${data.query_id}', -1)" class="w-7 h-7 rounded-lg hover:bg-slate-700 text-slate-400 hover:text-rose-400 transition flex items-center justify-center text-xs" title="Not helpful or inaccurate">
                        <i class="fa-regular fa-thumbs-down"></i>
                    </button>
                </div>
            </div>

            <div class="text-xs text-slate-200 leading-relaxed space-y-2">
                ${formatAnswerContent(data.answer)}
            </div>

            ${citationsHtml}
        </div>
    `;

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function formatAnswerContent(text) {
    // Highlight [Source: ...] brackets with subtle styling
    let formatted = escapeHtml(text);
    formatted = formatted.replace(/\[Source: ([^\]]+)\]/g, '<span class="inline-block px-1.5 py-0.5 rounded text-[10px] font-mono bg-blue-500/20 text-blue-300 border border-blue-500/30">[Source: $1]</span>');
    return `<p>${formatted.replace(/\n\n/g, '</p><p>').replace(/\n/g, '<br>')}</p>`;
}

function appendErrorMessage(msg) {
    const container = document.getElementById('chat-messages');
    const div = document.createElement('div');
    div.className = 'flex justify-start max-w-4xl mx-auto items-start space-x-3';
    div.innerHTML = `
        <div class="w-8 h-8 rounded-xl bg-rose-500/20 border border-rose-500/40 flex items-center justify-center text-rose-400 flex-shrink-0">
            <i class="fa-solid fa-triangle-exclamation text-xs"></i>
        </div>
        <div class="bg-rose-950/40 border border-rose-800/60 p-4 rounded-2xl rounded-tl-sm text-xs text-rose-200">
            <p class="font-semibold">Query Processing Failed</p>
            <p class="mt-1">${escapeHtml(msg)}</p>
        </div>
    `;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

// ------------------- DOCUMENT MANAGEMENT -------------------

async function fetchDocuments() {
    try {
        const resp = await fetch('/api/documents');
        const docs = await resp.json();
        
        // Update badges
        document.getElementById('nav-doc-badge').innerText = docs.length;
        document.getElementById('doc-summary-badge').innerText = `${docs.length} documents indexed`;
        document.getElementById('active-doc-count').innerText = `${docs.length} indexed documents active`;

        const container = document.getElementById('document-table-body');
        if (docs.length === 0) {
            container.innerHTML = `
                <div class="p-6 text-center text-slate-500 bg-slate-800/20 rounded-xl border border-slate-800 text-xs">
                    No documents uploaded yet. Upload a PDF or TXT document above to start.
                </div>
            `;
            return;
        }

        container.innerHTML = docs.map(d => `
            <div class="p-3.5 rounded-xl bg-slate-800/60 border border-slate-700/60 flex items-center justify-between hover:border-slate-600 transition">
                <div class="flex items-center space-x-3">
                    <div class="w-9 h-9 rounded-lg bg-blue-500/10 text-blue-400 border border-blue-500/20 flex items-center justify-center text-sm">
                        <i class="fa-solid ${d.file_type === 'pdf' ? 'fa-file-pdf text-rose-400' : 'fa-file-lines text-blue-400'}"></i>
                    </div>
                    <div>
                        <div class="flex items-center space-x-2">
                            <span class="text-xs font-semibold text-white">${escapeHtml(d.filename)}</span>
                            <span class="px-1.5 py-0.2 rounded text-[10px] bg-slate-700 text-slate-300 uppercase">${d.file_type}</span>
                        </div>
                        <div class="flex items-center space-x-3 text-[11px] text-slate-400 mt-0.5">
                            <span><i class="fa-solid fa-cubes text-[10px] mr-1"></i>${d.chunk_count} chunks</span>
                            <span>•</span>
                            <span>${(d.file_size / 1024).toFixed(1)} KB</span>
                            <span>•</span>
                            <span>${new Date(d.created_at).toLocaleDateString()}</span>
                        </div>
                    </div>
                </div>
                <button onclick="deleteDocument('${d.id}')" class="px-3 py-1.5 text-xs text-rose-400 hover:bg-rose-500/10 rounded-lg transition" title="Delete document">
                    <i class="fa-solid fa-trash-can mr-1"></i> Delete
                </button>
            </div>
        `).join('');
    } catch (e) {
        console.error('Failed to fetch documents:', e);
    }
}

async function handleFileSelect(e) {
    const files = e.target.files;
    if (!files || files.length === 0) return;
    await uploadFileList(files);
}

function setupDragAndDrop() {
    const dropZone = document.getElementById('drop-zone');
    ['dragenter', 'dragover'].forEach(name => {
        dropZone.addEventListener(name, (e) => {
            e.preventDefault();
            dropZone.classList.add('border-blue-500');
        }, false);
    });
    ['dragleave', 'drop'].forEach(name => {
        dropZone.addEventListener(name, (e) => {
            e.preventDefault();
            dropZone.classList.remove('border-blue-500');
        }, false);
    });
    dropZone.addEventListener('drop', (e) => {
        const files = e.dataTransfer.files;
        if (files && files.length > 0) {
            uploadFileList(files);
        }
    });
}

async function uploadFileList(files) {
    const formData = new FormData();
    for (let f of files) {
        formData.append('files', f);
    }

    const dropZone = document.getElementById('drop-zone');
    const originalHtml = dropZone.innerHTML;
    dropZone.innerHTML = `
        <div class="flex flex-col items-center justify-center p-4">
            <span class="w-8 h-8 rounded-full border-2 border-blue-500 border-t-transparent animate-spin mb-2"></span>
            <span class="text-xs text-blue-400 font-semibold">Chunking, embedding and indexing into FAISS...</span>
        </div>
    `;

    try {
        const resp = await fetch('/api/documents/upload', {
            method: 'POST',
            body: formData
        });

        if (!resp.ok) {
            const err = await resp.json();
            throw new Error(err.detail || 'Upload failed');
        }

        await fetchDocuments();
    } catch (err) {
        alert('Upload Error: ' + err.message);
    } finally {
        dropZone.innerHTML = originalHtml;
    }
}

async function deleteDocument(docId) {
    if (!confirm('Are you sure you want to remove this document and delete its vector embeddings?')) return;
    try {
        const resp = await fetch(`/api/documents/${docId}`, { method: 'DELETE' });
        if (resp.ok) {
            await fetchDocuments();
        } else {
            alert('Failed to delete document');
        }
    } catch (e) {
        alert('Error: ' + e.message);
    }
}

async function loadSampleDocuments() {
    const btn = event.currentTarget;
    const oldText = btn.innerHTML;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-1"></i> Ingesting...`;
    btn.disabled = true;

    try {
        const resp = await fetch('/api/documents/load-samples', { method: 'POST' });
        if (resp.ok) {
            await fetchDocuments();
            alert('Sample enterprise documents (PDF & TXT) successfully ingested and indexed into FAISS!');
        } else {
            alert('Failed to load sample documents.');
        }
    } catch (e) {
        console.error(e);
        alert('Error: ' + e.message);
    } finally {
        btn.innerHTML = oldText;
        btn.disabled = false;
        fetchDocuments();
    }
}

// ------------------- EVALUATION & BENCHMARKS -------------------

async function runBenchmarkEvaluation() {
    const btn = document.getElementById('run-eval-btn');
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin mr-1"></i> Running Benchmark...`;

    try {
        const resp = await fetch('/api/evaluate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ benchmark_type: 'full' })
        });
        if (!resp.ok) throw new Error('Benchmark execution failed');
        const data = await resp.json();
        renderEvaluationResults(data);
    } catch (err) {
        alert('Evaluation Error: ' + err.message);
    } finally {
        btn.disabled = false;
        btn.innerHTML = `<i class="fa-solid fa-play text-xs"></i> <span>Run Evaluation Benchmark</span>`;
    }
}

async function fetchLatestEvaluation() {
    try {
        const resp = await fetch('/api/evaluate/latest');
        if (resp.ok) {
            const data = await resp.json();
            renderEvaluationResults(data);
        }
    } catch (e) {
        // No evaluations yet
    }
}

function renderEvaluationResults(data) {
    document.getElementById('metric-correctness').innerText = `${(data.correctness_score * 100).toFixed(1)}%`;
    document.getElementById('metric-precision').innerText = `${(data.retrieval_precision * 100).toFixed(1)}%`;
    document.getElementById('metric-hallucination').innerText = `${(data.hallucination_prevention_rate * 100).toFixed(1)}%`;
    document.getElementById('metric-latency').innerText = `${data.average_response_time_ms} ms`;
    document.getElementById('benchmark-timestamp').innerText = `Completed: ${new Date(data.created_at).toLocaleTimeString()}`;

    const tbody = document.getElementById('eval-table-body');
    if (!data.details || data.details.length === 0) return;

    tbody.innerHTML = data.details.map(t => `
        <tr class="hover:bg-slate-700/30">
            <td class="py-3 px-4 font-medium text-white max-w-xs truncate">${escapeHtml(t.question)}</td>
            <td class="py-3 px-4">
                <span class="px-2 py-0.5 rounded text-[10px] ${t.category === 'hallucination_test' ? 'bg-amber-500/20 text-amber-300' : 'bg-blue-500/20 text-blue-300'}">
                    ${t.category}
                </span>
            </td>
            <td class="py-3 px-4 text-slate-400">${t.should_answer ? 'Answer Grounded' : 'Declare Refusal'}</td>
            <td class="py-3 px-4 font-mono text-[11px]">${t.actual_status}</td>
            <td class="py-3 px-4">
                <span class="inline-flex items-center space-x-1 px-2 py-0.5 rounded text-[10px] font-semibold ${t.is_correct ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'}">
                    <i class="fa-solid ${t.is_correct ? 'fa-check' : 'fa-xmark'}"></i>
                    <span>${t.is_correct ? 'PASSED' : 'FAILED'}</span>
                </span>
            </td>
            <td class="py-3 px-4 font-mono text-slate-400">${t.latency_ms} ms</td>
        </tr>
    `).join('');
}

// ------------------- FEEDBACK MODAL -------------------

function openFeedbackModal(queryId, rating) {
    document.getElementById('modal-query-id').value = queryId;
    document.getElementById('modal-rating').value = rating;
    document.getElementById('modal-feedback-type').innerText = rating > 0
        ? 'Thank you! What made this response helpful?'
        : 'Help us improve: What was missing or inaccurate?';
    document.getElementById('modal-comment').value = '';
    document.getElementById('feedback-modal').classList.remove('hidden');
}

function closeFeedbackModal() {
    document.getElementById('feedback-modal').classList.add('hidden');
}

async function submitFeedbackModal() {
    const query_id = document.getElementById('modal-query-id').value;
    const rating = parseInt(document.getElementById('modal-rating').value);
    const comment = document.getElementById('modal-comment').value.trim();

    try {
        const resp = await fetch('/api/feedback', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query_id, rating, comment })
        });
        if (resp.ok) {
            closeFeedbackModal();
            const ctrls = document.getElementById(`feedback-ctrls-${query_id}`);
            if (ctrls) {
                ctrls.innerHTML = `<span class="text-[10px] text-emerald-400 font-semibold"><i class="fa-solid fa-check mr-1"></i>Feedback logged</span>`;
            }
        }
    } catch (e) {
        alert('Failed to submit feedback');
    }
}

function escapeHtml(str) {
    if (!str) return '';
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}
