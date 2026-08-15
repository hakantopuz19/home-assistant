function requireAuth() {
  const token = localStorage.getItem('device_token');
  if (!token) {
    window.location.href = '/login';
    return false;
  }
  return token;
}

function decorateLinks(token) {
  const links = document.querySelectorAll('a');
  links.forEach(function (link) {
    if (!link.href) {
      return;
    }

    const url = new URL(link.href, window.location.href);
    url.searchParams.set('token', token);
    link.href = url.toString();
  });
}

async function logout() {
  const token = localStorage.getItem('device_token');
  try {
    if (token) {
      await fetch('/api/logout', {
        method: 'POST',
        headers: { Authorization: 'Bearer ' + token }
      });
    }
  } catch (error) {
    // ignore network error during logout cleanup
  } finally {
    localStorage.removeItem('device_token');
    window.location.href = '/login';
  }
}

function applySidebarState(isCollapsed) {
  const sidebar = document.getElementById('sidebar');
  if (!sidebar) {
    return;
  }

  sidebar.classList.toggle('collapsed', Boolean(isCollapsed));
  try {
    localStorage.setItem('device_sidebar_collapsed', String(Boolean(isCollapsed)));
  } catch (error) {
    // ignore storage issues in restricted environments
  }
}

function toggleSidebar() {
  const sidebar = document.getElementById('sidebar');
  if (!sidebar) {
    return;
  }

  const nextState = !sidebar.classList.contains('collapsed');
  applySidebarState(nextState);
}

function setLogMeta(text) {
  const meta = document.getElementById('logMeta');
  if (meta) {
    meta.textContent = text;
  }
}

function formatLogDisplay(logs) {
  const safeLogs = Array.isArray(logs) ? logs.filter(function (entry) {
    return typeof entry === 'string' && entry.trim();
  }) : [];

  if (!safeLogs.length) {
    return {
      text: 'No log entries yet.',
      count: 0
    };
  }

  const ordered = safeLogs.slice().reverse();
  return {
    text: ordered.join('\n'),
    count: ordered.length
  };
}

let autoRefreshHandle = null;

function setAutoRefresh(enabled) {
  const button = document.getElementById('toggleAutoRefresh');
  if (button) {
    button.textContent = 'Auto refresh: ' + (enabled ? 'On' : 'Off');
    button.classList.toggle('is-off', !enabled);
  }

  if (enabled) {
    if (!autoRefreshHandle) {
      autoRefreshHandle = window.setInterval(function () {
        loadLogs();
      }, 15000);
    }
  } else if (autoRefreshHandle) {
    window.clearInterval(autoRefreshHandle);
    autoRefreshHandle = null;
  }
}

async function loadLogs() {
  const token = requireAuth();
  if (!token) {
    return;
  }

  const output = document.getElementById('logOutput');
  if (!output) {
    return;
  }

  output.textContent = 'Loading logs...';
  setLogMeta('Refreshing...');

  try {
    const response = await fetch('/api/logs', {
      headers: { Authorization: 'Bearer ' + token }
    });

    if (!response.ok) {
      output.textContent = 'Unable to load logs.';
      setLogMeta('Request failed');
      return;
    }

    const payload = await response.json();
    const logs = Array.isArray(payload.logs) ? payload.logs : [];
    const formatted = formatLogDisplay(logs);
    output.textContent = formatted.text;

    const timestamp = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setLogMeta(formatted.count ? formatted.count + ' entries • updated ' + timestamp : 'No activity yet');
  } catch (error) {
    output.textContent = 'Log fetch failed.';
    setLogMeta('Fetch failed');
  }
}

const token = requireAuth();
if (token) {
  decorateLinks(token);

  const logoutButton = document.getElementById('logoutBtn');
  if (logoutButton) {
    logoutButton.addEventListener('click', function () {
      logout();
    });
  }

  const sidebarToggleButton = document.getElementById('sidebarToggle');
  const sidebarToggleTop = document.getElementById('sidebarToggleTop');

  try {
    const stored = localStorage.getItem('device_sidebar_collapsed');
    applySidebarState(stored === 'true');
  } catch (error) {
    applySidebarState(false);
  }

  if (sidebarToggleButton) {
    sidebarToggleButton.addEventListener('click', toggleSidebar);
  }

  if (sidebarToggleTop) {
    sidebarToggleTop.addEventListener('click', toggleSidebar);
  }

  const refreshButton = document.getElementById('refreshLogs');
  if (refreshButton) {
    refreshButton.addEventListener('click', loadLogs);
  }

  const autoRefreshButton = document.getElementById('toggleAutoRefresh');
  if (autoRefreshButton) {
    autoRefreshButton.addEventListener('click', function () {
      const nextState = autoRefreshButton.textContent.indexOf('Off') !== -1;
      setAutoRefresh(nextState);
    });
  }

  setAutoRefresh(true);
  loadLogs();
}
