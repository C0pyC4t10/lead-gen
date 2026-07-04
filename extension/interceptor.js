(function() {
  if (window.__skarbolInjected) return;
  window.__skarbolInjected = true;
  var origFetch = window.fetch;
  var lastTime = 0;
  window.fetch = function() {
    var args = arguments;
    return origFetch.apply(this, args).then(function(response) {
      if (!response.url || !response.url.includes('facebook.com')) return response;
      var clone = response.clone();
      clone.text().then(function(body) {
        try {
          var data = JSON.parse(body);
          scanForTimes(data);
        } catch(e) {}
      });
      return response;
    });
  };
  function scanForTimes(obj) {
    if (!obj || typeof obj !== 'object') return;
    if (Array.isArray(obj)) { obj.forEach(scanForTimes); return; }
    for (var k in obj) {
      var v = obj[k];
      var kl = k.toLowerCase();
      if ((kl === 'creation_time' || kl === 'publish_time' || kl === 'scheduled_publish_time') && typeof v === 'number' && v > 1e9) {
        if (v > lastTime) {
          lastTime = v;
          var d = new Date(v * 1000);
          var months = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
          var month = months[d.getMonth()];
          var day = d.getDate();
          var hours = d.getHours();
          var minutes = d.getMinutes();
          var ampm = hours >= 12 ? 'PM' : 'AM';
          hours = hours % 12 || 12;
          var text = month + ' ' + day + ', ' + d.getFullYear() + ' ' + hours + ':' + (minutes < 10 ? '0' : '') + minutes + ' ' + ampm;
          window.postMessage({ type: '__SKARBOL_POST_DATE', date: text }, '*');
        }
      }
      scanForTimes(v);
    }
  }
})();
