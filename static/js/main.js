const TOAST_DURATION = 4000;

const TOAST_ICONS = {
    success: '✓',
    error: '✕',
    warning: '⚠',
    info: 'ℹ',
};

function showToast(message, category = 'info') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${category}`;
    toast.setAttribute('role', 'alert');
    toast.innerHTML = `
        <span class="toast-icon" aria-hidden="true">${TOAST_ICONS[category] || TOAST_ICONS.info}</span>
        <span class="toast-message"></span>
        <button class="toast-close" aria-label="Dismiss">&times;</button>
    `;
    toast.querySelector('.toast-message').textContent = message;

    container.appendChild(toast);

    requestAnimationFrame(() => {
        requestAnimationFrame(() => toast.classList.add('toast-in'));
    });

    const dismiss = () => {
        toast.classList.remove('toast-in');
        toast.classList.add('toast-out');
        toast.addEventListener('transitionend', () => toast.remove(), { once: true });
    };

    toast.querySelector('.toast-close').addEventListener('click', dismiss);
    setTimeout(dismiss, TOAST_DURATION);
}

document.addEventListener('DOMContentLoaded', function () {
    const flashData = document.getElementById('flash-data');
    if (flashData) {
        flashData.querySelectorAll('[data-category]').forEach(el => {
            showToast(el.dataset.message, el.dataset.category);
        });
    }

    const avatarBtn = document.getElementById('nav-avatar-btn');
    const profilePanel = document.getElementById('nav-profile-panel');

    if (avatarBtn && profilePanel) {
        avatarBtn.addEventListener('click', function (e) {
            e.stopPropagation();
            const isOpen = !profilePanel.hidden;
            profilePanel.hidden = isOpen;
            avatarBtn.setAttribute('aria-expanded', String(!isOpen));
        });

        document.addEventListener('click', function (e) {
            if (!profilePanel.hidden && !profilePanel.contains(e.target)) {
                profilePanel.hidden = true;
                avatarBtn.setAttribute('aria-expanded', 'false');
            }
        });

        document.addEventListener('keydown', function (e) {
            if (e.key === 'Escape' && !profilePanel.hidden) {
                profilePanel.hidden = true;
                avatarBtn.setAttribute('aria-expanded', 'false');
                avatarBtn.focus();
            }
        });
    }
});
