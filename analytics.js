// Anonymous session events. Never read form values, URLs or child information.
(() => {
  if (navigator.doNotTrack === '1' || location.protocol === 'file:') return;
  let session;
  try {
    session = sessionStorage.getItem('mlh-analytics-session') || crypto.randomUUID();
    sessionStorage.setItem('mlh-analytics-session', session);
  } catch (_) { return; }
  const endpoint = 'https://my-little-hero.onrender.com/api/events';
  window.mlhTrack = (event_name, details = {}) => {
    try {
    const body = JSON.stringify({event_id: crypto.randomUUID(), session_id: session,
      event_name, ...details});
    fetch(endpoint, {method: 'POST', headers: {'Content-Type': 'application/json'},
      body, keepalive: true}).catch(() => {});
    } catch (_) { /* Analytics must never interrupt creation or WhatsApp. */ }
  };
  document.addEventListener('DOMContentLoaded', () => {
    window.mlhTrack('page_view');
    document.addEventListener('click', event => {
      if (event.target.closest('[data-open-creation], [data-pack]')) window.mlhTrack('creation_started');
      const pack = event.target.closest('[data-pack], [data-wizard-pack]');
      if (pack) window.mlhTrack('pack_selected', {pack_id: Number(pack.dataset.pack || pack.dataset.wizardPack)});
      if (event.target.closest('#orderButton:not(:disabled)')) window.mlhTrack('whatsapp_clicked');
    }, true);
    setInterval(() => {
      if (document.visibilityState === 'visible') window.mlhTrack('heartbeat');
    }, 60000);
  });
})();
