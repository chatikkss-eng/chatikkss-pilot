// Support Modal Logic
function openSupportModal() {
    document.getElementById('supportModal').classList.add('active');
}

function closeSupportModal() {
    document.getElementById('supportModal').classList.remove('active');
}

// Close modal when clicking outside
window.onclick = function (event) {
    const modal = document.getElementById('supportModal');
    if (event.target == modal) {
        closeSupportModal();
    }
}

async function copyWallet() {
    const wallet = "UQAjcKkV4mIbCwFhEmN-0uJH70m9Ig5ZTKG1Qn0MCv7N7fBy";
    const textSpan = document.getElementById('copyText');
    const btn = document.getElementById('copyBtn');

    try {
        await navigator.clipboard.writeText(wallet);
        const originalText = textSpan.innerText;
        textSpan.innerText = "Адрес скопирован! ✨";
        btn.style.borderColor = "#4ade80"; // green

        setTimeout(() => {
            textSpan.innerText = originalText;
            btn.style.borderColor = "";
        }, 2000);
    } catch (err) {
        console.error('Failed to copy: ', err);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const cursorGlow = document.getElementById('cursorGlow');
    const glassCard = document.querySelector('.glass-card');

    // Smooth Mouse Glow
    document.addEventListener('mousemove', (e) => {
        cursorGlow.style.left = e.clientX + 'px';
        cursorGlow.style.top = e.clientY + 'px';

        // Tilt animation for image - More subtle
        if (glassCard) {
            const rect = glassCard.getBoundingClientRect();
            const x = e.clientX - rect.left - rect.width / 2;
            const y = e.clientY - rect.top - rect.height / 2;

            const rotateX = -y / 80;
            const rotateY = x / 80;

            glassCard.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-5px)`;
        }
    });

    // Download button feedback
    const downloadBtn = document.querySelector('.btn-primary');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', function () {
            const originalHTML = this.innerHTML;

            // Change style
            this.style.background = '#4ade80'; // Emerald Green
            this.style.color = '#000';
            this.innerHTML = 'Загрузка началась! ✨ <span class="btn-sub">Проверьте папку загрузок</span>';

            // Show toast or notification logic could go here

            setTimeout(() => {
                this.style.background = '';
                this.style.color = '';
                this.innerHTML = originalHTML;
            }, 4000);
        });
    }

    // Reveal animations on scroll
    const cards = document.querySelectorAll('.detail-card');

    const observerOptions = {
        threshold: 0.1
    };

    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);

    cards.forEach(card => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';
        card.style.transition = 'all 0.6s ease-out';
        observer.observe(card);
    });

    // Smooth scroll for nav links (if any)
});
