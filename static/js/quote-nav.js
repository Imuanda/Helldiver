// quote-nav.js — Navigate between quotes with arrows or swipe gestures

const dataEl   = document.getElementById('quote-data');
if (!dataEl) throw new Error('No quote data');  // exits silently if no quotes

// ── State ─────────────────────────────────────────────────────────────────────
const allIds   = dataEl.dataset.ids.split(',').map(Number).filter(Boolean);
let   currentIdx = allIds.indexOf(Number(dataEl.dataset.current));

// ── DOM refs ──────────────────────────────────────────────────────────────────
const card        = document.getElementById('quote-card');
const prevBtn     = document.getElementById('nav-prev');
const nextBtn     = document.getElementById('nav-next');
const counter     = document.getElementById('quote-counter');

// ── Counter display ────────────────────────────────────────────────────────────
function updateCounter() {
    if (allIds.length <= 1) { counter.style.display = 'none'; return; }
    counter.textContent = `${currentIdx + 1} / ${allIds.length}`;
}

// ── Arrow visibility ───────────────────────────────────────────────────────────
function updateArrows() {
    prevBtn.style.opacity = currentIdx === 0                  ? '0.2' : '1';
    nextBtn.style.opacity = currentIdx === allIds.length - 1  ? '0.2' : '1';
    prevBtn.disabled      = currentIdx === 0;
    nextBtn.disabled      = currentIdx === allIds.length - 1;
}

// ── Load a quote by index ─────────────────────────────────────────────────────
async function goTo(idx) {
    if (idx < 0 || idx >= allIds.length) return;

    const quoteId = allIds[idx];

    // Fade the card out
    card.style.opacity    = '0';
    card.style.transform  = 'translateY(8px)';
    card.style.transition = 'opacity 0.2s ease, transform 0.2s ease';

    try {
        const res  = await fetch(`/api/quote/${quoteId}`);
        if (!res.ok) return;
        const q    = await res.json();

        // Swap content
        document.getElementById('q-text').textContent    = q.text;
        document.getElementById('q-speaker').innerHTML   = `&#8212;&nbsp;${escapeHtml(q.speaker)}`;
        document.getElementById('q-source').innerHTML    = buildSource(q);

        // Perspective — show only when it exists
        const perspEl   = document.getElementById('q-perspective');
        const perspText = document.getElementById('q-perspective-text');
        if (q.perspective) {
            perspText.textContent  = q.perspective;
            perspEl.style.display  = '';
        } else {
            perspEl.style.display  = 'none';
        }

        // Update reaction counts and data-quote-id attributes
        card.dataset.quoteId = q.id;
        document.querySelectorAll('.reaction-btn').forEach(btn => {
            btn.dataset.quoteId = q.id;
            const type  = btn.dataset.type;
            btn.querySelector('.reaction-count').textContent = q[`${type}_count`];
            btn.classList.remove('reacted');
        });
        document.querySelector('.total-likes').textContent = q.likes;

        // Update comment form
        const commentForm = document.getElementById('comment-form');
        commentForm.dataset.quoteId = q.id;

        // Reload comments for the new quote
        const commentList = document.getElementById('comment-list');
        commentList.innerHTML = '<div class="comments-loading">Loading comments…</div>';
        loadComments(q.id);

        currentIdx = idx;
        updateCounter();
        updateArrows();

        // Fade the card back in
        card.style.opacity   = '1';
        card.style.transform = 'translateY(0)';

    } catch (err) {
        console.error('Failed to load quote:', err);
        card.style.opacity   = '1';
        card.style.transform = 'translateY(0)';
    }
}

function buildSource(q) {
    let src = escapeHtml(q.book);
    if (q.chapter) src += ` &middot; Chapter ${q.chapter}`;
    if (q.page)    src += ` &middot; Page ${q.page}`;
    return src;
}

function escapeHtml(str) {
    return String(str || '')
        .replace(/&/g, '&amp;').replace(/</g, '&lt;')
        .replace(/>/g, '&gt;').replace(/"/g, '&quot;');
}

// ── Arrow buttons ─────────────────────────────────────────────────────────────
prevBtn.addEventListener('click', () => goTo(currentIdx - 1));
nextBtn.addEventListener('click', () => goTo(currentIdx + 1));

// ── Keyboard navigation (left / right arrow keys) ──────────────────────────────
document.addEventListener('keydown', e => {
    if (e.key === 'ArrowLeft')  goTo(currentIdx - 1);
    if (e.key === 'ArrowRight') goTo(currentIdx + 1);
});

// ── Touch swipe support (mobile) ─────────────────────────────────────────────
let touchStartX = 0;
let touchStartY = 0;

card.addEventListener('touchstart', e => {
    touchStartX = e.touches[0].clientX;
    touchStartY = e.touches[0].clientY;
}, { passive: true });

card.addEventListener('touchend', e => {
    const dx = e.changedTouches[0].clientX - touchStartX;
    const dy = e.changedTouches[0].clientY - touchStartY;

    // Only trigger if mostly horizontal swipe (not a scroll)
    if (Math.abs(dx) < 50 || Math.abs(dy) > Math.abs(dx)) return;

    if (dx < 0) goTo(currentIdx + 1);  // swipe left = next
    if (dx > 0) goTo(currentIdx - 1);  // swipe right = previous
}, { passive: true });

// ── Init ───────────────────────────────────────────────────────────────────────
updateCounter();
updateArrows();
