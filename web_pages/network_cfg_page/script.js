// Network configuration page logic: secure the page, load config, and save nested JSON values.
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

function setStatus(message, isError) {
  const statusEl = document.getElementById('status');
  if (!statusEl) {
    return;
  }

  statusEl.textContent = message;
  statusEl.classList.remove('success', 'error');
  statusEl.classList.add(isError ? 'error' : 'success');
}

function readValueFromField(fieldName, value) {
  if (fieldName.endsWith('.enabled') || fieldName.endsWith('.hidden') || fieldName.endsWith('.reconnect') || fieldName.endsWith('.broadcast')) {
    return value === true || value === 'on' || value === 'true';
  }

  if (fieldName.endsWith('.channel') || fieldName.endsWith('.authmode') || fieldName.endsWith('.max_clients') || fieldName.endsWith('.timeout') || fieldName.endsWith('.reconnect_interval') || fieldName.endsWith('.listen_port') || fieldName.endsWith('.discovery_interval') || fieldName.endsWith('.port')) {
    return Number(value);
  }

  return value;
}

function setFieldValue(fieldName, value) {
  const field = document.querySelector('[name="' + fieldName + '"]');
  if (!field) {
    return;
  }

  if (field.type === 'checkbox') {
    field.checked = !!value;
    return;
  }

  field.value = value ?? '';
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

async function loadConfig() {
  const token = requireAuth();
  if (!token) {
    return;
  }

  const response = await fetch('/api/config/network', {
    headers: { Authorization: 'Bearer ' + token }
  });

  if (!response.ok) {
    setStatus('Unable to load network configuration.', true);
    return;
  }

  const data = await response.json();
  const fields = document.querySelectorAll('[name]');

  fields.forEach(function (field) {
    const fieldName = field.name;
    const path = fieldName.split('.');
    let current = data;

    for (let i = 0; i < path.length; i += 1) {
      if (current === null || typeof current !== 'object' || !(path[i] in current)) {
        current = undefined;
        break;
      }
      current = current[path[i]];
    }

    setFieldValue(fieldName, current);
  });
}

async function saveConfig(event) {
  event.preventDefault();
  const token = requireAuth();
  if (!token) {
    return;
  }

  const form = event.currentTarget;
  const output = {};
  const fields = form.querySelectorAll('[name]');

  fields.forEach(function (field) {
    const path = field.name.split('.');
    let cursor = output;

    for (let i = 0; i < path.length - 1; i += 1) {
      const segment = path[i];
      if (!cursor[segment] || typeof cursor[segment] !== 'object') {
        cursor[segment] = {};
      }
      cursor = cursor[segment];
    }

    cursor[path[path.length - 1]] = readValueFromField(field.name, field.type === 'checkbox' ? field.checked : field.value);
  });

  setStatus('Saving...', false);

  const response = await fetch('/api/config/network', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: 'Bearer ' + token
    },
    body: JSON.stringify(output)
  });

  const data = await response.json();
  if (!response.ok || !data.ok) {
    setStatus(data.error || 'Network configuration could not be saved.', true);
    return;
  }

  setStatus('Configuration saved successfully.');
}

async function reloadCurrentConfig() {
  const token = requireAuth();
  if (!token) {
    return;
  }

  setStatus('Reloading configuration...', false);
  await loadConfig();
  setStatus('Configuration reloaded from device.');
}

async function resetDevice() {
  const token = requireAuth();
  if (!token) {
    return;
  }

  if (!window.confirm('Reset the device and reboot it now?')) {
    return;
  }

  setStatus('Resetting device...', false);

  try {
    const response = await fetch('/api/device/reset', {
      method: 'POST',
      headers: { Authorization: 'Bearer ' + token }
    });
    const data = await response.json();
    if (!response.ok || !data.ok) {
      setStatus(data.error || 'Device reset failed.', true);
      return;
    }

    setStatus('Device reset requested. The device will restart.');
    setTimeout(function () {
      localStorage.removeItem('device_token');
      window.location.href = '/login';
    }, 1200);
  } catch (error) {
    setStatus('Device reset request failed.', true);
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

  const reloadButton = document.getElementById('reloadNetworkConfig');
  if (reloadButton) {
    reloadButton.addEventListener('click', reloadCurrentConfig);
  }

  const resetButton = document.getElementById('resetDeviceBtn');
  if (resetButton) {
    resetButton.addEventListener('click', resetDevice);
  }

  loadConfig();
  document.getElementById('networkConfigForm').addEventListener('submit', saveConfig);
}
