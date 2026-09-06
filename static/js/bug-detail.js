import { getBugDetail } from './api.js';
import { renderEditableGrid } from './editable-grid.js';

const titles = {
    duplicate_roll: 'ထပ်နေသောကျောင်းဝင်နံပတ်များ',
    incomplete_row: 'နေရာလွတ်ရှိနေသောအတန်းများ',
    invalid_date: 'မွေးနေ့ရက်စွဲပုံစံမမှန်သောအတန်းများ',
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

document.addEventListener('DOMContentLoaded', async () => {
    setupThemeToggle();
    const bugType = window.BUG_TYPE;
    document.querySelector('#detail-title').textContent = titles[bugType] || 'Bug Details';
    const container = document.querySelector('#bug-detail-results');
    try {
        const result = await getBugDetail(bugType);
        renderEditableGrid(container, result.rows, bugType);
    } catch (error) {
        container.textContent = error.message;
    }
});
