import { exportSummary, getSummary } from './api.js';
import { readFilterValues, renderFilterOptions } from './filters.js';

const columns = [
    ['grade', 'Grade'],
    ['class', 'Class'],
    ['male', 'Male'],
    ['female', 'Female'],
    ['total', 'Total'],
];

function renderSummaryTable(summary) {
    const container = document.querySelector('#summary-table-container');
    const rows = Array.isArray(summary?.rows) ? summary.rows : [];
    const grandTotal = summary?.grand_total || { male: 0, female: 0, total: 0 };
    container.replaceChildren();

    const table = document.createElement('table');
    table.className = 'summary-table';
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');

    columns.forEach(([, label]) => {
        const header = document.createElement('th');
        header.textContent = label;
        headerRow.appendChild(header);
    });
    thead.appendChild(headerRow);

    const tbody = document.createElement('tbody');
    rows.forEach((summaryRow) => {
        const row = document.createElement('tr');
        columns.forEach(([key]) => {
            const cell = document.createElement('td');
            cell.textContent = summaryRow[key] ?? '';
            row.appendChild(cell);
        });
        tbody.appendChild(row);
    });

    const totalRow = document.createElement('tr');
    totalRow.className = 'grand-total';
    const totalLabel = document.createElement('td');
    totalLabel.colSpan = 2;
    totalLabel.textContent = 'Grand Total';
    totalRow.appendChild(totalLabel);
    ['male', 'female', 'total'].forEach((key) => {
        const cell = document.createElement('td');
        cell.textContent = grandTotal[key];
        totalRow.appendChild(cell);
    });
    tbody.appendChild(totalRow);

    table.append(thead, tbody);
    container.appendChild(table);
}

function renderError(message) {
    const container = document.querySelector('#summary-table-container');
    container.replaceChildren();
    const errorState = document.createElement('div');
    errorState.className = 'empty-state error-message';
    errorState.textContent = message;
    container.appendChild(errorState);
}

function setupThemeToggle() {
    const themeToggleButton = document.querySelector('#theme-toggle');
    const htmlElement = document.documentElement;
    const savedTheme = localStorage.getItem('theme') || 'light';
    htmlElement.setAttribute('data-theme', savedTheme);

    const updateToggleButton = (theme) => {
        if (!themeToggleButton) return;
        themeToggleButton.replaceChildren();
        const icon = document.createElement('span');
        icon.className = 'theme-icon';
        icon.textContent = theme === 'dark' ? '☀️' : '🌙';
        themeToggleButton.append(icon, document.createTextNode(theme === 'dark' ? ' Light Mode' : ' Dark Mode'));
    };

    updateToggleButton(savedTheme);
    themeToggleButton?.addEventListener('click', () => {
        const newTheme = htmlElement.getAttribute('data-theme') === 'light' ? 'dark' : 'light';
        htmlElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateToggleButton(newTheme);
    });
}

async function refreshSummary(form) {
    const summary = await getSummary(readFilterValues(form));
    renderFilterOptions(summary.options, form);
    renderSummaryTable(summary);
}

document.addEventListener('DOMContentLoaded', () => {
    setupThemeToggle();
    const filterForm = document.querySelector('#summary-filter-form');
    const dateInput = filterForm.elements.date;
    dateInput.value = new Date().toISOString().slice(0, 10);

    filterForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        try {
            await refreshSummary(filterForm);
        } catch (error) {
            renderError(error.message);
        }
    });

    document.querySelector('#summary-download-button').addEventListener('click', async () => {
        const fileName = document.querySelector('#summary-file-name').value;
        try {
            await exportSummary({ ...readFilterValues(filterForm), file_name: fileName });
        } catch (error) {
            renderError(error.message);
        }
    });

    refreshSummary(filterForm).catch((error) => renderError(error.message));
});
