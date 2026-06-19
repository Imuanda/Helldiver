// ── Star field ─────────────────────────────────────────────────────────────

const canvas = document.getElementById('star-canvas');
const ctx    = canvas.getContext('2d');

// Resize the canvas to always match the browser window
function resizeCanvas() {
    canvas.width  = window.innerWidth;
    canvas.height = window.innerHeight;
}
resizeCanvas();
window.addEventListener('resize', () => { resizeCanvas(); buildStars(); });

// Each star has a position, size, base opacity, and a twinkle speed
function randomStar() {
    return {
        x:       Math.random() * canvas.width,
        y:       Math.random() * canvas.height,
        radius:  Math.random() * 1.4 + 0.2,          // 0.2 – 1.6 px
        opacity: Math.random() * 0.6 + 0.2,           // 0.2 – 0.8
        speed:   Math.random() * 0.012 + 0.003,       // twinkle speed
        phase:   Math.random() * Math.PI * 2,         // random start in sine wave
    };
}

let stars = [];

function buildStars() {
    // Density: one star per 900 pixels of screen area, max 350
    const count = Math.min(Math.floor((canvas.width * canvas.height) / 900), 350);
    stars = Array.from({ length: count }, randomStar);
}
buildStars();

// Animation loop — redraws every frame
let frame = 0;
function drawStars() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    frame++;

    for (const s of stars) {
        // Sine wave makes each star's brightness pulse at its own rate
        const twinkle = Math.sin(frame * s.speed + s.phase);
        const alpha   = s.opacity + twinkle * 0.25;

        ctx.beginPath();
        ctx.arc(s.x, s.y, s.radius, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(255, 255, 255, ${Math.max(0, Math.min(1, alpha))})`;
        ctx.fill();
    }

    // Stop drawing once the zoom starts (no point wasting CPU)
    if (!document.body.classList.contains('zooming')) {
        requestAnimationFrame(drawStars);
    }
}
drawStars();


// ── Mars click — zoom-into-Mars transition ─────────────────────────────────

const mars        = document.getElementById('mars');
const zoomOverlay = document.getElementById('zoom-overlay');

mars.addEventListener('click', () => {
    // Add 'zooming' to body — CSS transitions pick this up automatically
    document.body.classList.add('zooming');

    // After the red overlay has fully faded in (1.3 s total), go to /home
    setTimeout(() => {
        window.location.href = '/home';
    }, 1350);
});

// Subtle cursor trail on Mars to make hover feel more alive
mars.addEventListener('mousemove', (e) => {
    const rect   = mars.getBoundingClientRect();
    const cx     = rect.left + rect.width  / 2;
    const cy     = rect.top  + rect.height / 2;
    const dx     = (e.clientX - cx) / (rect.width  / 2);
    const dy     = (e.clientY - cy) / (rect.height / 2);
    // Shifts the highlight slightly toward the cursor for a 3D feel
    mars.style.backgroundImage = `
        radial-gradient(circle at ${38 + dx * 10}% ${32 + dy * 10}%,
            #e05a20 0%, #c1440e 40%, #7a1f0a 75%, #3d0d04 100%)
    `;
});

mars.addEventListener('mouseleave', () => {
    mars.style.backgroundImage = '';
});
