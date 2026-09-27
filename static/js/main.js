/**
 * SecureNote — Vanilla JavaScript Main Module
 * 
 * Features:
 * 1. Dark/Light theme toggle with localStorage persistence.
 * 2. Toast auto-initialization.
 * 3. Delete modal confirmation with dynamic form URL.
 * 4. Clipboard copy for decrypted content.
 * 5. Real Fetch API asynchronous call: GET /api/notes/ live refresh on Dashboard.
 */

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initToasts();
    initDeleteModal();
    initCopyButton();
    initFetchApiRefresh();
});

/**
 * 1. Theme Management (Dark / Light Mode)
 * Controls Bootstrap 5.3 data-bs-theme attribute.
 */
function initTheme() {
    const themeToggleBtn = document.getElementById('themeToggleBtn');
    const themeIcon = document.getElementById('themeIcon');
    const themeLabel = document.getElementById('themeLabel');
    const htmlElement = document.documentElement;

    // Check stored preference or default to 'dark'
    const savedTheme = localStorage.getItem('securenote-theme') || 'dark';
    applyTheme(savedTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = htmlElement.getAttribute('data-bs-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            applyTheme(newTheme);
            localStorage.setItem('securenote-theme', newTheme);
        });
    }

    function applyTheme(theme) {
        htmlElement.setAttribute('data-bs-theme', theme);
        if (themeIcon && themeLabel) {
            if (theme === 'dark') {
                themeIcon.className = 'bi bi-moon-stars';
                themeLabel.textContent = 'Dark';
            } else {
                themeIcon.className = 'bi bi-sun';
                themeLabel.textContent = 'Light';
            }
        }
    }
}

/**
 * 2. Bootstrap Toast Notifications
 */
function initToasts() {
    const toastElList = document.querySelectorAll('.toast');
    toastElList.forEach(toastEl => {
        const toast = new bootstrap.Toast(toastEl, { delay: 5000 });
        toast.show();
    });
}

/**
 * 3. Delete Confirmation Modal
 * Sets the form action URL and note title dynamically.
 */
function initDeleteModal() {
    const deleteModalEl = document.getElementById('deleteConfirmModal');
    if (!deleteModalEl) return;

    const modal = new bootstrap.Modal(deleteModalEl);
    const deleteForm = document.getElementById('deleteNoteForm');
    const deleteTitleSpan = document.getElementById('deleteNoteTitle');

    document.addEventListener('click', (event) => {
        const targetBtn = event.target.closest('.delete-note-btn');
        if (targetBtn) {
            const noteTitle = targetBtn.getAttribute('data-note-title');
            const deleteUrl = targetBtn.getAttribute('data-delete-url');

            deleteForm.setAttribute('action', deleteUrl);
            deleteTitleSpan.textContent = `"${noteTitle}"`;
            modal.show();
        }
    });
}

/**
 * 4. Copy Decrypted Content to Clipboard
 */
function initCopyButton() {
    const copyBtn = document.getElementById('copyContentBtn');
    const contentBox = document.getElementById('decryptedContentBox');
    const copyIcon = document.getElementById('copyIcon');
    const copyBtnText = document.getElementById('copyBtnText');

    if (!copyBtn || !contentBox) return;

    copyBtn.addEventListener('click', async () => {
        try {
            await navigator.clipboard.writeText(contentBox.textContent);
            copyIcon.className = 'bi bi-check2 text-success me-1';
            copyBtnText.textContent = 'Copied!';
            setTimeout(() => {
                copyIcon.className = 'bi bi-clipboard me-1';
                copyBtnText.textContent = 'Copy';
            }, 2000);
        } catch (err) {
            console.error('Failed to copy text: ', err);
        }
    });
}

/**
 * 5. Real Fetch API Demonstration: Asynchronous Live Refresh of Notes
 * Hits GET /api/notes/ and updates the dashboard without full page reload.
 */
function initFetchApiRefresh() {
    const refreshBtn = document.getElementById('refreshNotesBtn');
    const refreshIcon = document.getElementById('refreshIcon');
    const refreshBtnText = document.getElementById('refreshBtnText');
    const notesContainer = document.getElementById('recentNotesContainer');
    const apiBadge = document.getElementById('apiStatusBadge');

    if (!refreshBtn || !notesContainer) return;

    refreshBtn.addEventListener('click', async () => {
        // Show loading state
        refreshIcon.classList.add('spinning');
        refreshBtn.disabled = true;
        refreshBtnText.textContent = 'Fetching...';

        try {
            // Asynchronous Fetch API call to Django REST Framework endpoint
            const response = await fetch('/api/notes/', {
                method: 'GET',
                headers: {
                    'Accept': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest',
                }
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            const notes = await response.json();

            // Render updated notes list dynamically
            renderRecentNotes(notes);

            // Display transient success badge
            if (apiBadge) {
                apiBadge.classList.remove('d-none');
                setTimeout(() => {
                    apiBadge.classList.add('d-none');
                }, 3500);
            }
        } catch (error) {
            console.error('Fetch error:', error);
            alert('Failed to refresh notes from API: ' + error.message);
        } finally {
            // Restore button state
            refreshIcon.classList.remove('spinning');
            refreshBtn.disabled = false;
            refreshBtnText.textContent = 'Refresh (Fetch API)';
        }
    });

    function renderRecentNotes(notes) {
        if (!notes || notes.length === 0) {
            notesContainer.innerHTML = `
                <div class="text-center py-5 text-muted">
                    <i class="bi bi-journal-plus fs-1 text-primary mb-2 d-block"></i>
                    <p class="mb-2 fs-5">No notes found yet.</p>
                    <p class="small mb-3">Create your first encrypted note to see it here on your dashboard.</p>
                    <a href="/notes/create/" class="btn btn-primary rounded-pill px-4">
                        <i class="bi bi-plus-lg me-1"></i>Create First Note
                    </a>
                </div>
            `;
            return;
        }

        // Show top 5 recent notes
        const topNotes = notes.slice(0, 5);

        let cardsHtml = '<div class="row g-3" id="notesListRow">';
        topNotes.forEach(note => {
            const catClass = (note.category || 'personal').toLowerCase();
            cardsHtml += `
                <div class="col-md-6 col-lg-4 note-card-item">
                    <div class="card h-100 border rounded-3 p-3 bg-body shadow-sm hover-card">
                        <div class="d-flex justify-content-between align-items-start mb-2">
                            <span class="badge category-badge category-${escapeHtml(catClass)}">${escapeHtml(note.category)}</span>
                            <small class="text-muted font-monospace"><i class="bi bi-clock me-1"></i>${escapeHtml(formatDate(note.updated_at))}</small>
                        </div>
                        <h6 class="fw-bold text-truncate mb-2" title="${escapeHtml(note.title)}">${escapeHtml(note.title)}</h6>
                        <p class="text-muted small mb-3">
                            <i class="bi bi-shield-lock-fill text-primary me-1"></i>Content encrypted with Fernet
                        </p>
                        <div class="mt-auto d-flex justify-content-between align-items-center pt-2 border-top">
                            <a href="/notes/${note.id}/" class="btn btn-sm btn-outline-primary rounded-pill px-3">
                                <i class="bi bi-eye me-1"></i>Open
                            </a>
                            <div class="d-flex gap-1">
                                <a href="/notes/${note.id}/edit/" class="btn btn-sm btn-outline-secondary rounded-circle" title="Edit Note">
                                    <i class="bi bi-pencil"></i>
                                </a>
                                <button type="button" class="btn btn-sm btn-outline-danger rounded-circle delete-note-btn" 
                                        data-note-id="${note.id}" 
                                        data-note-title="${escapeHtml(note.title)}" 
                                        data-delete-url="/notes/${note.id}/delete/"
                                        title="Delete Note">
                                    <i class="bi bi-trash"></i>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            `;
        });
        cardsHtml += '</div>';

        notesContainer.innerHTML = cardsHtml;
    }

    function formatDate(dateStr) {
        if (!dateStr) return '';
        try {
            const d = new Date(dateStr);
            return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
        } catch {
            return dateStr;
        }
    }

    function escapeHtml(str) {
        if (!str) return '';
        return String(str)
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
    }
}
