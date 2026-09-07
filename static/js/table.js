const columns = [
    ['စဉ်', 'စဉ်'],
    ['ကျောင်းဝင်အမှတ်', 'ကျောင်းဝင်အမှတ်'],
    ['နာမည်', 'နာမည်'],
    ['အဖေနာမည်', 'အဖေနာမည်'],
    ['ကျားမ', 'ကျား/မ'],
    ['မွေးနေ့', 'မွေးနေ့'],
    ['Grade', 'Grade'],
    ['အသက်', 'အသက်'],
];

export function renderTable(jsonData) {
    const container = document.querySelector('#table-container');
    const students = Array.isArray(jsonData?.students) ? jsonData.students : [];
    container.replaceChildren();

    if (students.length === 0) {
        const emptyState = document.createElement('div');
        emptyState.className = 'empty-state error-message';
        const noData = document.createElement('p');
        noData.textContent = 'ကျောင်းသားဒေတာ မတွေ့ရှိပါ။';
        const uploadPrompt = document.createElement('p');
        uploadPrompt.textContent = 'Excel ဖိုင် Upload လုပ်ပေးပါ။';
        emptyState.append(noData, uploadPrompt);
        container.appendChild(emptyState);
        return;
    }

    const table = document.createElement('table');
    const thead = document.createElement('thead');
    const headerRow = document.createElement('tr');
    columns.forEach(([, label]) => {
        const header = document.createElement('th');
        header.textContent = label;
        headerRow.appendChild(header);
    });
    thead.appendChild(headerRow);

    const tbody = document.createElement('tbody');
    students.forEach((student) => {
        const row = document.createElement('tr');
        columns.forEach(([key]) => {
            const cell = document.createElement('td');
            cell.textContent = student[key] ?? '';
            row.appendChild(cell);
        });
        tbody.appendChild(row);
    });

    table.append(thead, tbody);
    container.appendChild(table);
}

export function renderTableError(message) {
    const container = document.querySelector('#table-container');
    container.replaceChildren();

    const errorState = document.createElement('div');
    errorState.className = 'empty-state error-message';
    errorState.textContent = message;
    container.appendChild(errorState);
}

export function renderSummary(summary) {
    document.querySelector('#data-all').textContent = summary.all;
    document.querySelector('#data-male').textContent = summary.male;
    document.querySelector('#data-female').textContent = summary.female;
}