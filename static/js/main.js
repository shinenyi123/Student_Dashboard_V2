import { uploadBugCheckFile } from './api.js';
import { renderFormatError } from './bug-check-ui.js';
import { exportStudents, loadStudents, renderFilterOptions } from './filters.js';
import { renderSummary, renderTable, renderTableError } from './table.js';

async function refreshStudents(form) {
    const data = await loadStudents(form);
    renderFilterOptions(data.options, form);
    renderTable(data);
    renderSummary(data.summary);
}

document.addEventListener('DOMContentLoaded', () => {
    const filterForm = document.querySelector('#filter-form');
    const uploadForm = document.querySelector('#upload-form');

    filterForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        try {
            await refreshStudents(filterForm);
        } catch (error) {
            renderTableError(error.message);
        }
    });

    document.querySelector('#download-button').addEventListener('click', async () => {
        try {
            await exportStudents(filterForm);
        } catch (error) {
            renderTableError(error.message);
        }
    });

    uploadForm.addEventListener('submit', async (event) => {
        event.preventDefault();
        try {
            const file = uploadForm.elements.myfile.files[0];
            if (!file) {
                throw new Error('Please choose an Excel file.');
            }

            const checkFormData = new FormData();
            checkFormData.append('myfile', file);
            const checkResult = await uploadBugCheckFile(checkFormData);
            if (!checkResult.format_valid) {
                renderFormatError(document.querySelector('#table-container'), checkResult);
                return;
            }

            if (checkResult.imported) {
                await refreshStudents(filterForm);
                return;
            }

            window.location.href = '/bug-check';
        } catch (error) {
            renderTableError(error.message);
        }
    });

    refreshStudents(filterForm).catch((error) => renderTableError(error.message));
});

document.addEventListener('DOMContentLoaded', () => {
    const themeToggleBtn = document.getElementById('theme-toggle');
    const htmlElement = document.documentElement;

    // Browser local storage မှ Theme အခြေအနေကို ရယူခြင်း
    const savedTheme = localStorage.getItem('theme') || 'light';
    htmlElement.setAttribute('data-theme', savedTheme);
    updateToggleBtn(savedTheme);

    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const currentTheme = htmlElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'light' ? 'dark' : 'light';

            htmlElement.setAttribute('data-theme', newTheme);
            localStorage.getItem('theme');
            localStorage.setItem('theme', newTheme);
            updateToggleBtn(newTheme);
        });
    }

    function updateToggleBtn(theme) {
        if (!themeToggleBtn) return;
        if (theme === 'dark') {
            themeToggleBtn.innerHTML = '<span class="theme-icon">☀️</span> Light Mode';
        } else {
            themeToggleBtn.innerHTML = '<span class="theme-icon">🌙</span> Dark Mode';
        }
    }
});