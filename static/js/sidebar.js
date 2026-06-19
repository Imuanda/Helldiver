// ── Sidebar toggle ──────────────────────────────────────────────────────────

const sidebar        = document.getElementById('sidebar');
const toggleBtn      = document.getElementById('toggle-btn');
const sidebarOverlay = document.getElementById('sidebar-overlay');

// Opens the sidebar and dims the page behind it
function openSidebar() {
    sidebar.classList.add('open');
    sidebarOverlay.classList.add('visible');
}

// Closes the sidebar and removes the dim overlay
function closeSidebar() {
    sidebar.classList.remove('open');
    sidebarOverlay.classList.remove('visible');
}

// Toggle: if open → close, if closed → open
toggleBtn.addEventListener('click', () => {
    sidebar.classList.contains('open') ? closeSidebar() : openSidebar();
});

// Clicking the dim overlay also closes the sidebar
sidebarOverlay.addEventListener('click', closeSidebar);

// Close on Escape key — good accessibility practice
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeSidebar();
});


// ── Colors dropdown ─────────────────────────────────────────────────────────

const colorsToggle  = document.getElementById('colors-toggle');
const colorsSubmenu = document.getElementById('colors-submenu');
const colorsChevron = document.getElementById('colors-chevron');

colorsToggle.addEventListener('click', () => {
    const isOpen = colorsSubmenu.classList.toggle('open');
    // Rotate the chevron arrow when the submenu is open
    colorsChevron.classList.toggle('rotated', isOpen);
});


// ── Auth notice ─────────────────────────────────────────────────────────────

// authNotice only exists on pages that have reaction/comment buttons (home page)
const authNotice = document.getElementById('auth-notice');
let authNoticeTimer = null;

// Called by reaction buttons and comment box when user is not logged in
function showAuthNotice() {
    if (!authNotice) return; // safely do nothing on pages without this element
    authNotice.classList.add('visible');

    // Auto-hide after 4 seconds so it doesn't clutter the screen
    clearTimeout(authNoticeTimer);
    authNoticeTimer = setTimeout(() => {
        authNotice.classList.remove('visible');
    }, 4000);
}
