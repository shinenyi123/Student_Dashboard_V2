async function postJson(url, payload = {}) {
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(result.error || 'Unable to complete the request.');
    return result;
}

document.addEventListener('DOMContentLoaded', () => {
    document.querySelector('#logout-button')?.addEventListener('click', async () => {
        try {
            const result = await postJson('/api/logout');
            window.location.href = result.redirect || '/';
        } catch (error) {
            window.alert(error.message);
        }
    });
});
