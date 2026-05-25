const btnBurger = document.getElementById('btn-burger');
const mobileMenu = document.getElementById('mobile-menu');

if (btnBurger && mobileMenu) {
    btnBurger.addEventListener('click', () => {
        mobileMenu.classList.toggle('hidden');
    });
}

document.querySelectorAll('.dropdown-container').forEach(container => {
    const btn = container.querySelector('button');
    const body = container.querySelector('.dropdown-body');
    if (!btn || !body) return;

    btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = !body.classList.contains('hidden');
        document.querySelectorAll('.dropdown-body').forEach(d => {
            d.classList.add('hidden', 'opacity-0', 'scale-95');
            d.classList.remove('opacity-100', 'scale-100');
        });
        if (!isOpen) {
            body.classList.remove('hidden', 'opacity-0', 'scale-95');
            body.classList.add('opacity-100', 'scale-100');
        }
    });
});

document.addEventListener('click', () => {
    document.querySelectorAll('.dropdown-body').forEach(d => {
        d.classList.add('hidden', 'opacity-0', 'scale-95');
        d.classList.remove('opacity-100', 'scale-100');
    });
});

document.querySelectorAll('form[method="POST"], form[method="post"]').forEach(form => {
    if (form.id === 'chat-form') return;
    form.addEventListener('submit', function() {
        const btn = form.querySelector('button[type="submit"], input[type="submit"]');
        if (btn && !btn.disabled) {
            btn.disabled = true;
            btn.dataset.originalText = btn.textContent;
            btn.textContent = 'Processing...';
            setTimeout(() => {
                btn.disabled = false;
                btn.textContent = btn.dataset.originalText;
            }, 5000);
        }
    });
});
