// ---------------- Active tab highlight ----------------
(function () {
  const rawPath = window.location.pathname.replace(/\/+$/, '') || '/';
  const path = rawPath === '/' ? '/reporting.html' : rawPath;
  document.querySelectorAll('nav.tabs a.tab').forEach(a => {
    const href = a.getAttribute('href');
    const isActive = (path === href) || (href === '/reporting.html' && rawPath === '/');
    a.classList.toggle('active', isActive);
  });
})();

// ---------------- Report form submit ----------------
(function () {
  const form = document.getElementById('reportForm');
  const result = document.getElementById('result');
  if (!form || !result) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    result.textContent = 'Sending…';
    result.className = 'result';

    const fd = new FormData(form); // includes files automatically

    try {
      const res = await fetch('/api/report', {
        method: 'POST',
        body: fd
      });
      const json = await res.json().catch(() => ({}));

      if (!res.ok || json.ok === false) {
        result.textContent = json.message || 'There was a problem submitting your report.';
        result.className = 'result error';
        return;
      }

      result.textContent = json.message || 'Report received. Thank you!';
      result.className = 'result success';
      form.reset();
    } catch (err) {
      result.textContent = 'Network error. Please try again.';
      result.className = 'result error';
    }
  });
})();
