const DEFAULT_API_BASE = 'https://lead-gen-phcw.onrender.com';

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'save_lead') {
    chrome.storage.local.get(['skarbolAuthToken', 'skarbolApiBase'], (cfg) => {
      const token = cfg.skarbolAuthToken || '';
      const apiBase = (cfg.skarbolApiBase || DEFAULT_API_BASE).replace(/\/+$/, '');
      const headers = { 'Content-Type': 'application/json' };
      if (token) headers['Authorization'] = 'Bearer ' + token;

      fetch(apiBase + '/api/lead', {
        method: 'POST',
        headers: headers,
        body: JSON.stringify(request.data),
      })
        .then(async (res) => {
          const text = await res.text();
          let result;
          try { result = JSON.parse(text); }
          catch (e) {
            sendResponse({ ok: false, error: 'Server returned invalid JSON (HTTP ' + res.status + '): ' + text.slice(0, 80) });
            return;
          }
          if (res.status === 401) {
            sendResponse({ ok: false, error: 'unauthorized' });
          } else if (!res.ok) {
            sendResponse({ ok: false, error: result.error || ('HTTP ' + res.status) });
          } else {
            sendResponse({ ok: true, result: result });
          }
        })
        .catch((err) => sendResponse({ ok: false, error: 'Network error: ' + err.message }));
    });
    return true;
  }
});
