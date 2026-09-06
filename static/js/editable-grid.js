import { saveBugCheckProgress } from './api.js';

const columns = [
    ['စဉ်', 'စဉ်'],
    ['ကျောင်းဝင်အမှတ်', 'ကျောင်းဝင်အမှတ်'],
    ['နာမည်', 'နာမည်'],
    ['အဖေနာမည်', 'အဖေနာမည်'],
    ['ကျားမ', 'ကျား/မ'],
    ['မွေးနေ့', 'မွေးနေ့'],
    ['class', 'class'],
    ['Grade', 'Grade'],
];

function isFilled(value) {
    return String(value ?? '').trim() !== '';
}

function isValidDate(value) {
    const text = String(value ?? '').trim();
    if (!/^\d{2}-\d{2}-\d{4}$/.test(text)) return false;
    const [day, month, year] = text.split('-').map(Number);
    const parsed = new Date(year, month - 1, day);
    return parsed.getFullYear() === year
        && parsed.getMonth() === month - 1
        && parsed.getDate() === day;
}

function getOffendingColumns(row, allRows, bugType) {
    if (bugType === 'duplicate_roll') {
        const roll = String(row['ကျောင်းဝင်အမှတ်'] ?? '').trim();
        const duplicate = roll && allRows.filter((candidate) => (
            String(candidate['ကျောင်းဝင်အမှတ်'] ?? '').trim() === roll
        )).length > 1;
        return duplicate ? ['ကျောင်းဝင်အမှတ်'] : [];
    }

    if (bugType === 'invalid_date') {
        const date = String(row['မွေးနေ့'] ?? '').trim();
        return date && !isValidDate(date) ? ['မွေးနေ့'] : [];
    }

    if (bugType === 'incomplete_row') {
        const values = columns.map(([key]) => row[key] ?? '');
        const filledCount = values.filter(isFilled).length;
        return filledCount > 0 && filledCount < columns.length
            ? columns.filter(([key]) => !isFilled(row[key])).map(([key]) => key)
            : [];
    }

    return Array.isArray(row.offending_columns) ? row.offending_columns : [];
}

function applyCellError(cell, row, allRows, bugType, key) {
    const offendingColumns = getOffendingColumns(row, allRows, bugType);
    cell.classList.toggle('cell-error', offendingColumns.includes(key));
}

export function renderEditableGrid(container, rows, bugType) {
    const state = {
        rows: rows.map((row) => ({ ...row })),
        deleted: new Set(),
        history: [],
        future: [],
    };

    function record(action) {
        state.history.push(action);
        state.future = [];
    }

    function restore(action, reverse) {
        if (action.type === 'edit') {
            action.row[action.column] = reverse ? action.before : action.after;
        } else if (action.type === 'delete') {
            if (reverse) state.deleted.delete(action.rowNumber);
            else state.deleted.add(action.rowNumber);
        }
    }

    function render() {
        container.replaceChildren();
        const toolbar = document.createElement('div');
        toolbar.className = 'grid-toolbar';
        const undoButton = document.createElement('button');
        undoButton.textContent = 'Undo';
        undoButton.disabled = state.history.length === 0;
        undoButton.addEventListener('click', () => {
            const action = state.history.pop();
            restore(action, true);
            state.future.push(action);
            render();
        });
        const redoButton = document.createElement('button');
        redoButton.textContent = 'Redo';
        redoButton.disabled = state.future.length === 0;
        redoButton.addEventListener('click', () => {
            const action = state.future.pop();
            restore(action, false);
            state.history.push(action);
            render();
        });
        const saveButton = document.createElement('button');
        saveButton.className = 'save-excel-button';
        saveButton.textContent = 'Save Progress';
        saveButton.addEventListener('click', async () => {
            saveButton.disabled = true;
            try {
                const result = await saveBugCheckProgress({
                    edits: state.rows.filter((row) => !state.deleted.has(row.original_row_number)).map((row) => ({
                        original_row_number: row.original_row_number,
                        values: Object.fromEntries(columns.map(([key]) => [key, row[key] ?? ''])),
                    })),
                    deleted_rows: [...state.deleted],
                });
                window.location.href = result.redirect || '/bug-check';
            } catch (error) {
                window.alert(error.message);
            } finally {
                saveButton.disabled = false;
            }
        });
        toolbar.append(undoButton, redoButton, saveButton);
        container.appendChild(toolbar);

        const visibleRows = state.rows.filter((row) => !state.deleted.has(row.original_row_number));
        if (visibleRows.length === 0) {
            const empty = document.createElement('p');
            empty.className = 'empty-state';
            empty.textContent = 'No rows in this bug category.';
            container.appendChild(empty);
            return;
        }

        const table = document.createElement('table');
        const headerRow = document.createElement('tr');
        ['Original row #', ...columns.map(([, label]) => label), ''].forEach((label) => {
            const header = document.createElement('th');
            header.textContent = label;
            headerRow.appendChild(header);
        });
        const thead = document.createElement('thead');
        thead.appendChild(headerRow);
        const tbody = document.createElement('tbody');

        visibleRows.forEach((row) => {
            const tableRow = document.createElement('tr');
            const numberCell = document.createElement('td');
            numberCell.textContent = row.original_row_number;
            tableRow.appendChild(numberCell);
            columns.forEach(([key]) => {
                const cell = document.createElement('td');
                cell.contentEditable = 'true';
                cell.textContent = row[key] ?? '';
                applyCellError(cell, row, state.rows, bugType, key);
                cell.addEventListener('input', () => {
                    const draftRow = { ...row, [key]: cell.textContent };
                    const allRows = state.rows.map((candidate) => (
                        candidate === row ? draftRow : candidate
                    ));
                    applyCellError(cell, draftRow, allRows, bugType, key);
                });
                cell.addEventListener('blur', () => {
                    const after = cell.textContent;
                    if (after === row[key]) return;
                    const action = { type: 'edit', row, column: key, before: row[key] ?? '', after };
                    row[key] = after;
                    record(action);
                    render();
                });
                tableRow.appendChild(cell);
            });
            const actionCell = document.createElement('td');
            const deleteButton = document.createElement('button');
            deleteButton.className = 'delete-row-button';
            deleteButton.setAttribute('aria-label', 'Delete row');
            deleteButton.textContent = '×';
            deleteButton.addEventListener('click', () => {
                state.deleted.add(row.original_row_number);
                record({ type: 'delete', rowNumber: row.original_row_number });
                render();
            });
            actionCell.appendChild(deleteButton);
            tableRow.appendChild(actionCell);
            tbody.appendChild(tableRow);
        });

        table.append(thead, tbody);
        const tableContainer = document.createElement('div');
        tableContainer.className = 'bug-detail-table-container';
        tableContainer.appendChild(table);
        container.appendChild(tableContainer);
    }

    render();
}
