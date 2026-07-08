// ─────────────────────────────────────────────────────────────
// Scraven Modal — unified confirm/alert/prompt dialogs
// Replaces native browser prompt(), confirm(), alert()
// Usage:
//   const ok = await scravenConfirm('Are you sure?');
//   const val = await scravenPrompt('Enter URL:', 'https://...');
//   await scravenAlert('Done!');
// ─────────────────────────────────────────────────────────────
(function() {
  if (window.scravenConfirm && window.scravenAlert && window.scravenPrompt) return;

  const CSS = `
    .scr-overlay { position: fixed; inset: 0; background: rgba(5,10,20,0.85); z-index: 1000; display: flex; align-items: center; justify-content: center; backdrop-filter: blur(3px); animation: scrFadeIn .15s ease; }
    @keyframes scrFadeIn { from { opacity: 0 } to { opacity: 1 } }
    .scr-modal { background: linear-gradient(180deg, #0A1224 0%, #050A14 100%); border: 1px solid rgba(0,229,255,0.25); border-radius: 14px; padding: 24px; width: 92%; max-width: 460px; box-shadow: 0 24px 64px rgba(0,0,0,0.6); animation: scrSlideIn .2s ease; }
    @keyframes scrSlideIn { from { transform: translateY(20px); opacity: 0 } to { transform: translateY(0); opacity: 1 } }
    .scr-head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
    .scr-title { font-size: 16px; font-weight: 700; color: #F8FAFC; display: flex; align-items: center; gap: 8px; }
    .scr-close { background: transparent; border: 1px solid rgba(255,255,255,0.15); color: #94A3B8; width: 30px; height: 30px; border-radius: 6px; cursor: pointer; font-size: 18px; line-height: 1; transition: all .15s; }
    .scr-close:hover { background: rgba(255,255,255,0.08); color: #F8FAFC; }
    .scr-body { font-size: 14px; color: #CBD5E1; line-height: 1.5; margin-bottom: 16px; white-space: pre-wrap; word-break: break-word; }
    .scr-input { width: 100%; padding: 11px 13px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; color: #F8FAFC; font-size: 14px; font-family: inherit; box-sizing: border-box; margin-bottom: 16px; }
    .scr-input:focus { border-color: #00E5FF; outline: none; background: rgba(0,229,255,0.05); }
    .scr-actions { display: flex; gap: 8px; }
    .scr-btn { flex: 1; padding: 11px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 14px; border: none; transition: all .15s; font-family: inherit; }
    .scr-btn-primary { background: linear-gradient(135deg, #0A4FD9, #00E5FF); color: #fff; }
    .scr-btn-primary:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(10,79,217,0.4); }
    .scr-btn-danger { background: linear-gradient(135deg, #DC2626, #EF4444); color: #fff; }
    .scr-btn-danger:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(220,38,38,0.4); }
    .scr-btn-secondary { padding: 11px 18px; flex: 0 0 auto; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.15); color: #94A3B8; }
    .scr-btn-secondary:hover { background: rgba(255,255,255,0.08); color: #F8FAFC; }
  `;

  function injectCss() {
    if (document.getElementById('scr-modal-styles')) return;
    const s = document.createElement('style');
    s.id = 'scr-modal-styles';
    s.textContent = CSS;
    document.head.appendChild(s);
  }

  function makeModal({ icon, title, body, inputPlaceholder, inputValue, primaryLabel, primaryClass, showCancel }) {
    return new Promise((resolve) => {
      injectCss();
      const overlay = document.createElement('div');
      overlay.className = 'scr-overlay';
      const inputHtml = inputPlaceholder !== undefined
        ? `<input type="text" class="scr-input" placeholder="${inputPlaceholder.replace(/"/g, '&quot;')}" value="${(inputValue || '').replace(/"/g, '&quot;')}" />`
        : '';
      const cancelHtml = showCancel !== false ? `<button class="scr-btn scr-btn-secondary" id="scrCancel">Cancel</button>` : '';
      overlay.innerHTML = `
        <div class="scr-modal">
          <div class="scr-head">
            <div class="scr-title">${icon ? `<span style="font-size:20px">${icon}</span>` : ''}${title}</div>
            <button class="scr-close" id="scrClose">×</button>
          </div>
          ${body ? `<div class="scr-body">${body}</div>` : ''}
          ${inputHtml}
          <div class="scr-actions">
            <button class="scr-btn ${primaryClass || 'scr-btn-primary'}" id="scrOk">${primaryLabel || 'OK'}</button>
            ${cancelHtml}
          </div>
        </div>
      `;
      document.body.appendChild(overlay);
      const input = overlay.querySelector('.scr-input');
      const ok = overlay.querySelector('#scrOk');
      const cancel = overlay.querySelector('#scrCancel');
      const close = overlay.querySelector('#scrClose');
      if (input) setTimeout(() => { input.focus(); input.select(); }, 50);
      function done(val) {
        if (overlay.parentNode) document.body.removeChild(overlay);
        resolve(val);
      }
      ok.onclick = () => done(input ? input.value : true);
      if (cancel) cancel.onclick = () => done(input ? null : false);
      close.onclick = () => done(input ? null : false);
      overlay.onclick = (e) => { if (e.target === overlay) done(input ? null : false); };
      if (input) {
        input.onkeydown = (e) => {
          if (e.key === 'Enter') done(input.value);
          else if (e.key === 'Escape') done(null);
        };
      } else {
        document.addEventListener('keydown', function escHandler(e) {
          if (e.key === 'Escape') { document.removeEventListener('keydown', escHandler); done(false); }
          else if (e.key === 'Enter') { document.removeEventListener('keydown', escHandler); done(true); }
        });
      }
    });
  }

  window.scravenConfirm = function(message, opts = {}) {
    return makeModal({
      icon: opts.icon || '⚠️',
      title: opts.title || 'Confirm',
      body: message,
      primaryLabel: opts.primaryLabel || 'Confirm',
      primaryClass: opts.danger ? 'scr-btn-danger' : 'scr-btn-primary',
      showCancel: true,
    });
  };

  window.scravenAlert = function(message, opts = {}) {
    return makeModal({
      icon: opts.icon || 'ℹ️',
      title: opts.title || 'Notice',
      body: message,
      primaryLabel: opts.primaryLabel || 'OK',
      primaryClass: 'scr-btn-primary',
      showCancel: false,
    });
  };

  window.scravenPrompt = function(message, placeholder = '', defaultValue = '') {
    return makeModal({
      icon: '✏️',
      title: 'Input Required',
      body: message,
      inputPlaceholder: placeholder,
      inputValue: defaultValue,
      primaryLabel: 'Submit',
      primaryClass: 'scr-btn-primary',
      showCancel: true,
    });
  };

  window.scravenNote = function(message, defaultValue = '', opts = {}) {
    return new Promise((resolve) => {
      injectCss();
      const overlay = document.createElement('div');
      overlay.className = 'scr-overlay';
      const noteCss = `
        .scr-textarea { width: 100%; min-height: 110px; padding: 11px 13px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.15); border-radius: 8px; color: #F8FAFC; font-size: 14px; font-family: inherit; box-sizing: border-box; margin-bottom: 16px; resize: vertical; }
        .scr-textarea:focus { border-color: #00E5FF; outline: none; background: rgba(0,229,255,0.05); }
      `;
      if (!document.getElementById('scr-note-styles')) {
        const s = document.createElement('style');
        s.id = 'scr-note-styles';
        s.textContent = noteCss;
        document.head.appendChild(s);
      }
      overlay.innerHTML = `
        <div class="scr-modal" style="max-width:520px">
          <div class="scr-head">
            <div class="scr-title">${opts.icon || '📝'} <span>${opts.title || 'Add Note'}</span></div>
            <button class="scr-close" id="scrNoteClose">×</button>
          </div>
          ${message ? `<div class="scr-body">${message}</div>` : ''}
          <textarea class="scr-textarea" id="scrNoteInput" placeholder="${(opts.placeholder || 'What happened? (e.g., called, messaged, awaiting reply)').replace(/"/g, '&quot;')}">${(defaultValue || '').replace(/</g, '&lt;')}</textarea>
          <div class="scr-actions">
            <button class="scr-btn scr-btn-secondary" id="scrNoteCancel">Cancel</button>
            <button class="scr-btn scr-btn-primary" id="scrNoteOk">${opts.primaryLabel || 'Save Note'}</button>
          </div>
        </div>
      `;
      document.body.appendChild(overlay);
      const ta = overlay.querySelector('#scrNoteInput');
      const ok = overlay.querySelector('#scrNoteOk');
      const cancel = overlay.querySelector('#scrNoteCancel');
      const close = overlay.querySelector('#scrNoteClose');
      setTimeout(() => ta.focus(), 50);
      function done(val) {
        if (overlay.parentNode) document.body.removeChild(overlay);
        resolve(val);
      }
      ok.onclick = () => done(ta.value.trim());
      cancel.onclick = () => done(null);
      close.onclick = () => done(null);
      overlay.onclick = (e) => { if (e.target === overlay) done(null); };
      ta.onkeydown = (e) => {
        if (e.key === 'Escape') done(null);
        // Allow newlines with Enter; Ctrl+Enter / Cmd+Enter to submit
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') done(ta.value.trim());
      };
    });
  };
})();