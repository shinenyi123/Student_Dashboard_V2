export async function getStudents(params) {
    const query = new URLSearchParams(params);
    const response = await fetch(`/api/students?${query}`);
    if (!response.ok) {
        throw new Error('Unable to load student data.');
    }
    return response.json();
}

export async function getSummary(params = {}) {
    const queryString = new URLSearchParams(params).toString();
    const query = queryString ? `?${queryString}` : '';
    const response = await fetch(`/api/summary${query}`);
    if (!response.ok) {
        throw new Error('Unable to load summary data.');
    }
    return response.json();
}

export async function uploadFile(formData) {
    const response = await fetch('/api/upload', {
        method: 'POST',
        body: formData,
    });
    if (!response.ok) {
        throw new Error('Unable to upload student data.');
    }
    return response.json();
}

export async function downloadExcel(params) {
    const response = await fetch('/api/export', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams(params),
    });
    if (!response.ok) {
        throw new Error('Unable to export student data.');
    }

    const blob = await response.blob();
    const disposition = response.headers.get('Content-Disposition') || '';
    const filenameMatch = disposition.match(/filename="?([^";]+)"?/i);
    const filename = filenameMatch ? filenameMatch[1] : 'student_export.xlsx';
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
}

export async function exportSummary(params) {
    const response = await fetch('/api/export-summary', {
        method: 'POST',
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        body: new URLSearchParams(params),
    });
    if (!response.ok) {
        throw new Error('Unable to export summary data.');
    }

    const blob = await response.blob();
    const disposition = response.headers.get('Content-Disposition') || '';
    const filenameMatch = disposition.match(/filename="?([^";]+)"?/i);
    const filename = filenameMatch ? filenameMatch[1] : 'grade_class_summary.xlsx';
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
}

export async function uploadBugCheckFile(formData) {
    const response = await fetch('/api/bug-check/upload', {
        method: 'POST',
        body: formData,
    });
    if (!response.ok) {
        const error = await response.json().catch(() => ({}));
        throw new Error(error.error || 'Unable to check the Excel file.');
    }
    return response.json();
}

export async function getBugDetail(bugType) {
    const response = await fetch(`/api/bug-check/detail/${bugType}`);
    if (!response.ok) {
        throw new Error('Unable to load bug details.');
    }
    return response.json();
}

export async function getBugCheckSummary() {
    const response = await fetch('/api/bug-check/status');
    if (!response.ok) {
        throw new Error('Unable to load bug-check progress.');
    }
    return response.json();
}

export async function saveBugCheckProgress(payload) {
    const response = await fetch('/api/bug-check/save-progress', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    if (!response.ok) {
        throw new Error('Unable to save bug-check progress.');
    }
    return response.json();
}

export async function downloadBugTemplate() {
    const response = await fetch('/api/bug-check/template');
    if (!response.ok) {
        throw new Error('Unable to download the Excel template.');
    }
    return downloadBlob(response, 'student_upload_template.xlsx');
}

async function downloadBlob(response, fallbackFilename) {
    const blob = await response.blob();
    const disposition = response.headers.get('Content-Disposition') || '';
    const filenameMatch = disposition.match(/filename="?([^";]+)"?/i);
    const filename = filenameMatch ? filenameMatch[1] : fallbackFilename;
    const link = document.createElement('a');
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.click();
    URL.revokeObjectURL(link.href);
}