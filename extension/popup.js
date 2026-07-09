const fieldsConfig = [
  { key: 'business_name', label: 'Business Name' },
  { key: 'category', label: 'Category' },
  { key: 'followers', label: 'Followers' },
  { key: 'email', label: 'Email' },
  { key: 'phone', label: 'Phone' },
  { key: 'website', label: 'Website' },
  { key: 'has_website', label: 'Has Website' },
  { key: 'address', label: 'Address' },
  { key: 'last_post_date', label: 'Last Post Date' },
  { key: 'url', label: 'Page URL' },
];

function hasSupportedUrl(url) {
  return /^https?:\/\/(www\.)?(facebook\.com|instagram\.com)\//.test(url);
}

function getPlatform(url) {
  if (/facebook\.com/.test(url)) return 'facebook';
  if (/instagram\.com/.test(url)) return 'instagram';
  return 'unknown';
}

function getPostDateStatus(text) {
  if (!text) return '⚪ Unknown';
  const parsed = new Date(text);
  if (!isNaN(parsed.getTime())) {
    const diffDays = Math.floor((Date.now() - parsed.getTime()) / 86400000);
    if (diffDays <= 50) return '🟢 Active';
    if (diffDays <= 90) return '🟡 Slow';
    return '🔴 Inactive';
  }
  const t = text.toLowerCase();
  if (/just now/i.test(t) || /min/i.test(t)) return '🟢 Active';
  const num = parseInt(t.match(/\d+/)?.[0] || '0', 10);
  if (/hour/i.test(t)) return '🟢 Active';
  if (/day/i.test(t)) {
    if (num <= 50) return '🟢 Active';
    if (num <= 90) return '🟡 Slow';
    return '🔴 Inactive';
  }
  if (/week/i.test(t)) {
    if (num <= 7) return '🟢 Active';
    if (num <= 13) return '🟡 Slow';
    return '🔴 Inactive';
  }
  if (/month/i.test(t)) return '🔴 Inactive';
  if (/year/i.test(t)) return '🔴 Inactive';
  return '⚪ Unknown';
}

function isEmpty(value) {
  return value === undefined || value === null || value === '';
}

function getFieldId(key) {
  return 'field_' + key;
}

function renderFields(data) {
  const container = document.getElementById('fields');
  container.innerHTML = '';
  for (const cfg of fieldsConfig) {
    const val = data[cfg.key];
    const div = document.createElement('div');
    div.className = 'field';
    const id = getFieldId(cfg.key);
    const displayVal = isEmpty(val) ? '' : val;
    const placeholder = 'Not found';
    let inputHtml;
    if (cfg.key === 'has_website') {
      inputHtml = `<select class="field-input" id="${id}">
        <option value="" ${displayVal === '' ? 'selected' : ''}>Not found</option>
        <option value="Yes" ${displayVal === 'Yes' || displayVal === true || displayVal === 'true' ? 'selected' : ''}>Yes</option>
        <option value="No" ${displayVal === 'No' || displayVal === false || displayVal === 'false' || displayVal === '' ? 'selected' : ''}>No</option>
      </select>`;
    } else {
      inputHtml = `<input type="text" class="field-input" id="${id}" value="${escapeHtml(displayVal)}" placeholder="${placeholder}" />`;
    }
    div.innerHTML = `
      <div class="field-label">${cfg.label}</div>
      ${inputHtml}
    `;
    container.appendChild(div);
  }
}

function escapeHtml(str) {
  const d = document.createElement('div');
  d.textContent = str;
  return d.innerHTML;
}

function renderScore(score) {
  const badge = document.getElementById('scoreBadge');
  const detail = document.getElementById('scoreDetail');
  badge.textContent = score;
  badge.className = 'score-badge';
  if (score <= 4) {
    badge.classList.add('red');
    detail.textContent = 'Low priority — verify before outreach';
  } else if (score <= 6) {
    badge.classList.add('yellow');
    detail.textContent = 'Promising — add to outreach queue';
  } else {
    badge.classList.add('green');
    detail.textContent = 'Strong lead — prioritize outreach';
  }
}

function showStatus(message, type) {
  const el = document.getElementById('status');
  el.textContent = message;
  el.className = 'status ' + type;
  el.style.display = 'block';
  setTimeout(() => { el.style.display = 'none'; }, 4000);
}

async function getCurrentTabUrl() {
  const tabs = await chrome.tabs.query({ active: true, currentWindow: true });
  return tabs[0] ? tabs[0].url : null;
}

document.addEventListener('DOMContentLoaded', async () => {
  const loading = document.getElementById('loading');
  const noPage = document.getElementById('noPage');
  const dataSection = document.getElementById('dataSection');
  const btnSave = document.getElementById('btnSave');
  const btnCopyEmail = document.getElementById('btnCopyEmail');
  const btnCopyPhone = document.getElementById('btnCopyPhone');
  const authBanner = document.getElementById('authBanner');
  const tokenInput = document.getElementById('tokenInput');
  const btnSaveToken = document.getElementById('btnSaveToken');

  const DEFAULT_API_BASE = 'https://lead-gen-phcw.onrender.com';

chrome.storage.local.get(['skarbolAuthToken', 'skarbolNotifyTelegram', 'skarbolApiBase'], (cfg) => {
    if (!cfg.skarbolAuthToken) {
      if (authBanner) authBanner.style.display = 'block';
    }
    if (cfg.skarbolNotifyTelegram === false) {
      const chk = document.getElementById('chkNotifyTelegram');
      if (chk) chk.checked = false;
    }
    // Show configured server URL with option to change
    const apiBase = cfg.skarbolApiBase || DEFAULT_API_BASE;
    const apiBaseLabel = document.getElementById('apiBaseLabel');
    if (apiBaseLabel) apiBaseLabel.textContent = apiBase;
    const apiBaseInput = document.getElementById('apiBaseInput');
    if (apiBaseInput) apiBaseInput.value = apiBase;
  });

  const changeLink = document.getElementById('changeServer');
  const serverRow = document.getElementById('serverRow');
  if (changeLink && serverRow) {
    changeLink.addEventListener('click', (e) => {
      e.preventDefault();
      serverRow.style.display = serverRow.style.display === 'none' ? 'block' : 'none';
    });
  }
  const btnSaveServer = document.getElementById('btnSaveServer');
  if (btnSaveServer) {
    btnSaveServer.addEventListener('click', () => {
      const v = (document.getElementById('apiBaseInput').value || '').trim().replace(/\/+$/, '');
      if (!v) return;
      chrome.storage.local.set({ skarbolApiBase: v }, () => {
        const lbl = document.getElementById('apiBaseLabel');
        if (lbl) lbl.textContent = v;
        showStatus('Server URL saved: ' + v, 'success');
      });
    });
  }

  if (btnSaveToken) {
    btnSaveToken.addEventListener('click', () => {
      const t = (tokenInput.value || '').trim();
      if (!t) { tokenInput.focus(); return; }
      chrome.storage.local.set({ skarbolAuthToken: t }, () => {
        if (authBanner) authBanner.style.display = 'none';
        showStatus('Token saved. You can now save leads.', 'success');
      });
    });
    tokenInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') btnSaveToken.click();
    });
  }

  const chkNt = document.getElementById('chkNotifyTelegram');
  if (chkNt) {
    chkNt.addEventListener('change', () => {
      chrome.storage.local.set({ skarbolNotifyTelegram: chkNt.checked });
    });
  }

  const tabUrl = await getCurrentTabUrl();

  if (!tabUrl || !hasSupportedUrl(tabUrl)) {
    loading.style.display = 'none';
    noPage.style.display = 'block';
    return;
  }

  const platform = getPlatform(tabUrl);

  // Normalize tab URL
  function normalizeTabUrl(url) {
    try {
      const u = new URL(url);
      u.searchParams.delete('sk');
      u.searchParams.delete('v');
      u.searchParams.delete('ref');
      u.searchParams.delete('__tn__');
      u.searchParams.delete('igsh');
      u.searchParams.delete('igshid');
      u.hash = '';
      return u.toString().replace(/\/+$/, '');
    } catch (_) { return url; }
  }

  chrome.storage.local.get('currentLead', (result) => {
    loading.style.display = 'none';

    const tabNormalized = normalizeTabUrl(tabUrl);
    const mainUrl = tabNormalized.replace(/\/about\/?$/i, '');
    const leadUrl = result.currentLead ? normalizeTabUrl(result.currentLead.url || '') : '';
    if (!result.currentLead || (leadUrl !== tabNormalized && leadUrl !== mainUrl)) {
      noPage.style.display = 'block';
      const pageName = platform === 'instagram' ? 'Instagram' : 'Facebook';
      noPage.querySelector('p').textContent = 'No data extracted yet. Refresh the ' + pageName + ' page and try again.';
      return;
    }

    dataSection.style.display = 'block';
    const data = result.currentLead;
    renderFields(data);
    renderScore(data.qualification_score);

    function readField(key) {
      const el = document.getElementById(getFieldId(key));
      if (!el) return '';
      if (el.tagName === 'SELECT') return el.value === 'Not found' ? '' : el.value;
      return el.value.trim();
    }

    btnCopyEmail.addEventListener('click', () => {
      navigator.clipboard.writeText(readField('email') || data.email).then(() => {
        showStatus('Email copied to clipboard', 'success');
      });
    });

    btnCopyPhone.addEventListener('click', () => {
      navigator.clipboard.writeText(readField('phone') || data.phone).then(() => {
        showStatus('Phone copied to clipboard', 'success');
      });
    });

    btnSave.addEventListener('click', () => {
      btnSave.disabled = true;
      btnSave.textContent = 'Saving…';

      const finalBusinessName = readField('business_name') || data.business_name || '';
      const finalCategory = readField('category') || data.category || '';
      const finalFollowers = readField('followers') || data.followers || '';
      const finalEmail = readField('email') || data.email || '';
      const finalPhone = readField('phone') || data.phone || '';
      const finalWebsite = readField('website') || data.website || '';
      const finalHasWebsite = readField('has_website') === 'Yes';
      const finalAddress = readField('address') || data.address || '';
      const finalLastPostDate = readField('last_post_date') || data.last_post_date || '';
      const finalUrl = readField('url') || data.url || '';

      const followUpDate = (data.qualification_score || 0) >= 8
        ? new Date(Date.now() + 3 * 86400000).toISOString().split('T')[0]
        : '';

      let notes = 'Auto-extracted via extension.';

      const notifyTelegram = document.getElementById('chkNotifyTelegram').checked;

      const lead = {
        date: new Date().toISOString().split('T')[0],
        platform: platform,
        business_name: finalBusinessName,
        page_url: finalUrl,
        followers: finalFollowers,
        email: finalEmail,
        phone: finalPhone,
        website: finalWebsite,
        has_website: finalHasWebsite ? 'true' : 'false',
        address: finalAddress,
        last_post_date: finalLastPostDate,
        category: finalCategory,
        qualification_score: data.qualification_score || 5,
        status: 'new',
        notes: notes,
        follow_up_date: followUpDate,
        notify_telegram: notifyTelegram,
      };

      chrome.runtime.sendMessage({ action: 'save_lead', data: lead }, (response) => {
        btnSave.disabled = false;
        btnSave.textContent = 'Save Lead';
        if (chrome.runtime.lastError) {
          showStatus('Error: ' + chrome.runtime.lastError.message, 'error');
          return;
        }
        if (response && response.ok) {
          const telegramStatus = notifyTelegram ? ' + Telegram notified' : ' (DB only)';
          showStatus('Lead saved successfully' + telegramStatus, 'success');
        } else if (response && response.error === 'unauthorized') {
          document.getElementById('authBanner').style.display = 'block';
          showStatus('Not connected. Paste your API token above to enable saving.', 'error');
        } else {
          showStatus(response && response.error ? 'Error: ' + response.error : 'Could not connect to server', 'error');
        }
      });
    });
  });
});
