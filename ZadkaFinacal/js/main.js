document.addEventListener('DOMContentLoaded', () => {
    // Initialize tooltips
    initTooltips();
    // Initialize modals
    initModals();
    // Initialize dropdown toggles
    initDropdowns();
    // Add form validation
    initFormValidation();
});

function initTooltips() {
    const tooltips = document.querySelectorAll('[data-tooltip]');
    tooltips.forEach(element => {
        tippy(element, {
            content: element.getAttribute('data-tooltip'),
            placement: 'top'
        });
    });
}

function initModals() {
    const modalTriggers = document.querySelectorAll('[data-modal-target]');
    modalTriggers.forEach(trigger => {
        trigger.addEventListener('click', () => {
            const modal = document.querySelector(trigger.dataset.modalTarget);
            if (modal) {
                modal.classList.remove('hidden');
            }
        });
    });

    const modalCloseButtons = document.querySelectorAll('[data-modal-close]');
    modalCloseButtons.forEach(button => {
        button.addEventListener('click', () => {
            const modal = button.closest('.modal');
            if (modal) {
                modal.classList.add('hidden');
            }
        });
    });
}

function initDropdowns() {
    const dropdowns = document.querySelectorAll('.dropdown');
    dropdowns.forEach(dropdown => {
        const trigger = dropdown.querySelector('.dropdown-trigger');
        const content = dropdown.querySelector('.dropdown-content');

        trigger.addEventListener('click', (e) => {
            e.stopPropagation();
            content.classList.toggle('hidden');
        });

        document.addEventListener('click', () => {
            content.classList.add('hidden');
        });
    });
}

function initFormValidation() {
    const forms = document.querySelectorAll('form[data-validate]');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            if (!validateForm(form)) {
                e.preventDefault();
            }
        });
    });
}

function validateForm(form) {
    let isValid = true;
    const inputs = form.querySelectorAll('input[required], select[required], textarea[required]');
    
    inputs.forEach(input => {
        if (!input.value.trim()) {
            isValid = false;
            showError(input, 'กรุณากรอกข้อมูลในช่องนี้');
        } else {
            clearError(input);
        }
    });

    return isValid;
}

function showError(input, message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'text-red-500 text-sm mt-1';
    errorDiv.textContent = message;
    
    clearError(input);
    input.classList.add('border-red-500');
    input.parentNode.appendChild(errorDiv);
}

function clearError(input) {
    const existingError = input.parentNode.querySelector('.text-red-500');
    if (existingError) {
        existingError.remove();
    }
    input.classList.remove('border-red-500');
}