/* ==================================================================
   VALIDATE.JS
   Aakha project na forms mate client-side JS validation.
   Server-side validation (Python) j final source of truth che,
   pan aa JS thi user ne submit karta pehla j error khabar pade.
   ================================================================== */

const NAME_RE = /^[A-Za-z ]{2,40}$/;
const EMAIL_RE = /^[^@\s]+@[^@\s]+\.[^@\s]+$/;
const PASSWORD_RE = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[!@#$%^&*()_\-+=[\]{}|;:,.<>?]).{8,}$/;

function setError(inputId, message) {
    const input = document.getElementById(inputId);
    const errorSpan = document.getElementById('err_' + inputId);
    if (input) input.classList.toggle('invalid', !!message);
    if (errorSpan) errorSpan.textContent = message || '';
    return !message;
}

function attachSignupValidation(formId) {
    const form = document.getElementById(formId);
    if (!form) return;

    function validate() {
        let ok = true;

        const firstName = document.getElementById('first_name').value.trim();
        const lastName = document.getElementById('last_name').value.trim();
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;
        const confirmPassword = document.getElementById('confirm_password').value;

        ok = setError('first_name', NAME_RE.test(firstName) ? '' : 'First name only letters, 2-40 characters.') && ok;
        ok = setError('last_name', NAME_RE.test(lastName) ? '' : 'Last name only letters, 2-40 characters.') && ok;
        ok = setError('email', EMAIL_RE.test(email) ? '' : 'Please enter a valid email address.') && ok;
        ok = setError('password', PASSWORD_RE.test(password) ? '' : 'Min 8 chars incl. uppercase, lowercase, number, special char.') && ok;
        ok = setError('confirm_password', password === confirmPassword ? '' : 'Passwords do not match.') && ok;

        return ok;
    }

    ['first_name', 'last_name', 'email', 'password', 'confirm_password'].forEach(id => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('input', validate);
    });

    form.addEventListener('submit', function (e) {
        if (!validate()) {
            e.preventDefault();
        }
    });
}

function attachLoginValidation(formId) {
    const form = document.getElementById(formId);
    if (!form) return;

    function validate() {
        let ok = true;
        const email = document.getElementById('email').value.trim();
        const password = document.getElementById('password').value;

        ok = setError('email', EMAIL_RE.test(email) ? '' : 'Please enter a valid email address.') && ok;
        ok = setError('password', password.length > 0 ? '' : 'Password is required.') && ok;
        return ok;
    }

    form.addEventListener('submit', function (e) {
        if (!validate()) e.preventDefault();
    });
}

function attachEmailOnlyValidation(formId) {
    const form = document.getElementById(formId);
    if (!form) return;

    form.addEventListener('submit', function (e) {
        const email = document.getElementById('email').value.trim();
        if (!setError('email', EMAIL_RE.test(email) ? '' : 'Please enter a valid email address.')) {
            e.preventDefault();
        }
    });
}

function attachResetPasswordValidation(formId, newPassId, confirmPassId) {
    const form = document.getElementById(formId);
    if (!form) return;

    form.addEventListener('submit', function (e) {
        let ok = true;
        const newPass = document.getElementById(newPassId).value;
        const confirmPass = document.getElementById(confirmPassId).value;

        const newSpan = document.getElementById('err_' + newPassId);
        const confirmSpan = document.getElementById('err_' + confirmPassId);

        if (!PASSWORD_RE.test(newPass)) {
            ok = false;
            if (newSpan) newSpan.textContent = 'Min 8 chars incl. uppercase, lowercase, number, special char.';
            document.getElementById(newPassId).classList.add('invalid');
        } else {
            if (newSpan) newSpan.textContent = '';
            document.getElementById(newPassId).classList.remove('invalid');
        }

        if (newPass !== confirmPass) {
            ok = false;
            if (confirmSpan) confirmSpan.textContent = 'Passwords do not match.';
            document.getElementById(confirmPassId).classList.add('invalid');
        } else {
            if (confirmSpan) confirmSpan.textContent = '';
            document.getElementById(confirmPassId).classList.remove('invalid');
        }

        if (!ok) e.preventDefault();
    });
}
