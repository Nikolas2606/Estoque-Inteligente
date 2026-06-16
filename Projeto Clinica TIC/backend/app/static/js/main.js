/**
 * Sistema de Estoque Inteligente
 * JavaScript Client-Side: Validações, UX e Interações
 */

document.addEventListener('DOMContentLoaded', () => {
    // ============================================
    // Toast Auto-dismiss
    // ============================================
    document.querySelectorAll('.toast').forEach(toastEl => {
        const toast = new bootstrap.Toast(toastEl, { delay: 5000 });
        toast.show();
    });

    // ============================================
    // Prevent Double Submit
    // ============================================
    document.querySelectorAll('form').forEach(form => {
        form.addEventListener('submit', function () {
            const btn = this.querySelector('[type="submit"]');
            if (btn && !btn.dataset.allowMultiple) {
                setTimeout(() => {
                    btn.disabled = true;
                    btn.innerHTML = '<span class="spinner-border spinner-border-sm me-1"></span> Processando...';
                }, 10);
            }
        });
    });

    // ============================================
    // Search Validation (min 2 chars)
    // ============================================
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('searchInput');

    if (searchForm && searchInput) {
        searchForm.addEventListener('submit', (e) => {
            const val = searchInput.value.trim();
            if (val.length > 0 && val.length < 2) {
                e.preventDefault();
                searchInput.classList.add('is-invalid');
                showToast('Digite pelo menos 2 caracteres para buscar.', 'warning');
            } else {
                searchInput.classList.remove('is-invalid');
            }
        });

        // Remove invalid state on input
        searchInput.addEventListener('input', () => {
            searchInput.classList.remove('is-invalid');
        });
    }

    // ============================================
    // Login Form Validation
    // ============================================
    const loginForm = document.getElementById('loginForm');
    if (loginForm) {
        loginForm.addEventListener('submit', (e) => {
            const username = document.getElementById('username');
            const password = document.getElementById('password');
            let valid = true;

            if (username && username.value.trim().length < 3) {
                e.preventDefault();
                username.classList.add('is-invalid');
                valid = false;
            } else if (username) {
                username.classList.remove('is-invalid');
            }

            if (password && password.value.length < 4) {
                e.preventDefault();
                password.classList.add('is-invalid');
                valid = false;
            } else if (password) {
                password.classList.remove('is-invalid');
            }
        });
    }

    // ============================================
    // Historico Date Validation
    // ============================================
    const filtroForm = document.getElementById('filtroForm');
    if (filtroForm) {
        filtroForm.addEventListener('submit', (e) => {
            const inicio = document.getElementById('filtroDataInicio')?.value;
            const fim = document.getElementById('filtroDataFim')?.value;
            if (inicio && fim && inicio > fim) {
                e.preventDefault();
                showToast('Data inicial deve ser anterior ou igual à data final.', 'warning');
            }
        });
    }
});

/**
 * Show a dynamic Bootstrap toast notification.
 * @param {string} message - Message to display
 * @param {string} type - Bootstrap color: success, danger, warning, info
 */
function showToast(message, type = 'info') {
    const container = document.querySelector('.toast-container') ||
        (() => {
            const div = document.createElement('div');
            div.className = 'toast-container position-fixed top-0 end-0 p-3';
            div.style.zIndex = '9999';
            document.body.appendChild(div);
            return div;
        })();

    const iconMap = {
        success: 'bi-check-circle-fill',
        danger: 'bi-exclamation-triangle-fill',
        warning: 'bi-exclamation-circle-fill',
        info: 'bi-info-circle-fill'
    };

    const toastHTML = `
        <div class="toast align-items-center text-bg-${type} border-0" role="alert"
             aria-live="assertive" aria-atomic="true">
            <div class="d-flex">
                <div class="toast-body">
                    <i class="bi ${iconMap[type] || iconMap.info} me-2"></i>${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto"
                        data-bs-dismiss="toast" aria-label="Fechar"></button>
            </div>
        </div>
    `;

    container.insertAdjacentHTML('beforeend', toastHTML);
    const toastEl = container.lastElementChild;
    const toast = new bootstrap.Toast(toastEl, { delay: 5000 });
    toast.show();

    toastEl.addEventListener('hidden.bs.toast', () => toastEl.remove());
}
