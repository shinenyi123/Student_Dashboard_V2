import { getBugCheckSummary } from './api.js';

const bugLabels = {
    duplicate_roll: 'ကျောင်းဝင်အမှတ် ထပ်နေခြင်း',
    incomplete_row: 'နေရာလွတ်ရှိနေခြင်း',
    invalid_date: 'date format မမှန်ခြင်း',
};

function setupThemeToggle() {
    const button = document.querySelector('#theme-toggle');
    const html = document.documentElement;
    const update = (theme) => {
        html.setAttribute('data-theme', theme);
        button.querySelector('.theme-icon').textContent = theme === 'dark' ? '☀️' : '🌙';
        button.lastChild.textContent = theme === 'dark' ? ' Light Mode' : ' Dark Mode';
    };
    update(localStorage.getItem('theme') || 'light');
    button.addEventListener('click', () => {
        const theme = html.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
        localStorage.setItem('theme', theme);
        update(theme);
    });
}

function renderResults(result) {
    const container = document.querySelector('#bug-check-results');
    container.replaceChildren();
    Object.entries(bugLabels).forEach(([bugType, label]) => {
        const line = document.createElement('div');
        line.className = 'bug-summary-line';
        const text = document.createElement('span');
        text.textContent = `${label} — ${result.bugs[bugType].count} bug`;
        const link = document.createElement('a');
        link.href = `/bug-check/detail/${bugType}`;
        link.textContent = 'See more';
        line.append(text, link);
        container.appendChild(line);
    });

}

document.addEventListener('DOMContentLoaded', () => {
    setupThemeToggle();
    const results = document.querySelector('#bug-check-results');
    getBugCheckSummary()
        .then((result) => {
            if (!result.active) {
                const message = document.createElement('p');
                message.className = 'empty-state';
                message.append('Please return to the Dashboard to upload a file first. ');
                const link = document.createElement('a');
                link.href = '/';
                link.textContent = 'Go to Dashboard';
                message.appendChild(link);
                results.appendChild(message);
                return;
            }
            renderResults(result);
        })
        .catch((error) => {
            results.textContent = error.message;
        });
});
