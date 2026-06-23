// interactions.js — AJAX reactions and comments (no page reload needed)

// ── Reactions ─────────────────────────────────────────────────────────────────

document.querySelectorAll('.reaction-btn').forEach(btn => {
    btn.addEventListener('click', async () => {
        const type    = btn.dataset.type;
        const quoteId = btn.dataset.quoteId;

        try {
            const res  = await fetch(`/quote/${quoteId}/react`, {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ type }),
            });
            const data = await res.json();

            if (data.error) {
                console.warn('Reaction error:', data.error);
                return;
            }

            // Update the count on the clicked button
            btn.querySelector('.reaction-count').textContent = data.count;
            btn.classList.toggle('reacted', data.reacted);

            // If the user swapped from a different reaction, deactivate the old button
            if (data.old_type) {
                const card    = btn.closest('[data-quote-id]');
                const oldBtn  = card && card.querySelector(`.reaction-btn[data-type="${data.old_type}"]`);
                if (oldBtn) {
                    // Decrement the old button's count and remove its active state
                    const oldCountEl = oldBtn.querySelector('.reaction-count');
                    oldCountEl.textContent = Math.max(0, parseInt(oldCountEl.textContent, 10) - 1);
                    oldBtn.classList.remove('reacted');
                }
            }

            // Recalculate the total likes counter
            const card  = btn.closest('[data-quote-id]');
            const total = card && card.querySelector('.total-likes');
            if (total) {
                const counts = [...card.querySelectorAll('.reaction-count')]
                    .map(el => parseInt(el.textContent, 10) || 0);
                total.textContent = counts.reduce((a, b) => a + b, 0);
            }

        } catch (err) {
            console.error('Reaction failed:', err);
        }
    });
});


// ── Comments ──────────────────────────────────────────────────────────────────

// Load existing comments when the page opens (home page only)
const commentList = document.getElementById('comment-list');
const commentForm = document.getElementById('comment-form');

if (commentList && commentForm) {
    const quoteId = commentForm.dataset.quoteId;

    // Fetch and render existing comments on load
    loadComments(quoteId);

    // Live character counter for the textarea
    const textarea  = document.getElementById('comment-text');
    const charCount = commentForm.querySelector('.comment-char-count');

    if (textarea && charCount) {
        textarea.addEventListener('input', () => {
            charCount.textContent = `${textarea.value.length} / 500`;
        });
    }

    // Submit handler — posts via AJAX, adds comment to list without reloading
    let commentSubmitting = false; // idempotency flag — prevents double-submit

    commentForm.addEventListener('submit', async (e) => {
        e.preventDefault();

        // If already submitting, ignore the second tap entirely
        if (commentSubmitting) return;

        const text     = textarea.value.trim();
        const errorDiv = document.getElementById('comment-error');
        const submitBtn = commentForm.querySelector('.comment-submit');

        if (!text) return;

        // Lock the button visually and functionally
        commentSubmitting = true;
        submitBtn.disabled    = true;
        submitBtn.textContent = '…';

        try {
            const res  = await fetch(`/quote/${quoteId}/comment`, {
                method:  'POST',
                headers: { 'Content-Type': 'application/json' },
                body:    JSON.stringify({ text }),
            });
            const data = await res.json();

            if (data.error) {
                errorDiv.textContent = data.error;
                errorDiv.style.display = 'block';
                return;
            }

            errorDiv.style.display = 'none';
            textarea.value = '';
            if (charCount) charCount.textContent = '0 / 500';
            appendComment(data);

        } catch (err) {
            console.error('Comment submit failed:', err);
            errorDiv.textContent = 'Something went wrong. Please try again.';
            errorDiv.style.display = 'block';
        } finally {
            // Always unlock — even if there was an error
            commentSubmitting        = false;
            submitBtn.disabled       = false;
            submitBtn.textContent    = 'Post';
        }
    });
}


async function loadComments(quoteId) {
    try {
        const res  = await fetch(`/quote/${quoteId}/comments`);
        const data = await res.json();

        commentList.innerHTML = ''; // clear "Loading…" placeholder

        if (!data.length) {
            commentList.innerHTML = '<p class="no-comments">No comments yet. Be the first.</p>';
            return;
        }

        data.forEach(appendComment);

    } catch (err) {
        commentList.innerHTML = '<p class="no-comments">Could not load comments.</p>';
    }
}


function appendComment(comment) {
    // Remove "no comments" placeholder if it's there
    const placeholder = commentList.querySelector('.no-comments, .comments-loading');
    if (placeholder) placeholder.remove();

    const el = document.createElement('div');
    el.className = 'comment-item';
    el.innerHTML = `
        <div class="comment-header">
            <span class="comment-author">${escapeHtml(comment.author)}</span>
            <span class="comment-time">${comment.time}</span>
        </div>
        <p class="comment-body">${escapeHtml(comment.text)}</p>
    `;
    commentList.appendChild(el);
}


// Escape HTML on the client side — defence-in-depth (server also escapes)
function escapeHtml(str) {
    return String(str)
        .replace(/&/g,  '&amp;')
        .replace(/</g,  '&lt;')
        .replace(/>/g,  '&gt;')
        .replace(/"/g,  '&quot;')
        .replace(/'/g,  '&#39;');
}
