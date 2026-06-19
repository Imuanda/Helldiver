// forms.js — Idempotency for all HTML form submissions.
// Disables the submit button the moment the form is submitted so
// a slow server or impatient double-tap never sends the request twice.

document.querySelectorAll('form').forEach(form => {
    form.addEventListener('submit', () => {
        const btn = form.querySelector('button[type="submit"]');
        if (!btn || btn.disabled) return;

        // Lock immediately — the browser hasn't sent the request yet
        btn.disabled = true;

        // Store original text and swap to a waiting indicator
        btn.dataset.originalText = btn.textContent;
        btn.textContent = 'Please wait…';

        // Safety valve: re-enable after 8 seconds in case the server is slow
        // and the form never redirects (prevents permanent lock-out)
        setTimeout(() => {
            btn.disabled = false;
            btn.textContent = btn.dataset.originalText || btn.textContent;
        }, 8000);
    });
});
