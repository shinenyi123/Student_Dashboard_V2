import { downloadBugTemplate } from './api.js';

export function renderFormatError(container, result) {
    container.replaceChildren();
    const message = document.createElement('p');
    message.className = 'format-error';
    message.textContent = 'The Excel file format is wrong.';
    const expected = document.createElement('p');
    expected.textContent = `Expected columns: ${result.expected_columns.join(' | ')}`;
    const downloadButton = document.createElement('button');
    downloadButton.className = 'template-download-button';
    downloadButton.textContent = 'Download Template';
    downloadButton.addEventListener('click', () => {
        downloadBugTemplate().catch((error) => window.alert(error.message));
    });
    container.append(message, expected, downloadButton);
}
