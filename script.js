// Highlight the active nav link based on the current URL
const path = window.location.pathname.replace(/\/+$/, '') || '/';
document.querySelectorAll('nav.tabs a.tab').forEach(a => {
  const href = a.getAttribute('href');
  const isActive = (path === '/' && href === '/') || (path !== '/' && href === path);
  a.classList.toggle('active', isActive);
});

// Report form submit (only runs on the report page where the form exists)
const form = document.getElementById('reportForm');
const result = document.getElementById('result');

if (form && result) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    result.textContent = 'Sending…';
    result.className = 'result';

    try {
      const data = new FormData(form);
      const res = await fetch('/api/report', { method: 'POST', body: data, credentials: 'same-origin' });
      const json = await res.json();

      if (!json.ok) {
        result.textContent = json.message || 'There was a problem submitting your report.';
        result.className = 'result error';
        return;
      }

      result.textContent = json.message || 'Report received. Thank you!';
      result.className = 'result success';
      form.reset();
    } catch {
      result.textContent = 'Network error. Please try again.';
      result.className = 'result error';
    }
  });
}
