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
  statusEl.classList.toggle('error', !!isError);
  statusEl.classList.toggle('success', !isError);
}

function readValueFromField(fieldName, value) {
  if (fieldName.endsWith('.enabled') || fieldName.endsWith('.hidden') || fieldName.endsWith('.reconnect') || fieldName.endsWith('.broadcast')) {
    return value === true || value === 'on' || value === 'true';
  }
  if (fieldName === 'gpio.mode') {
    return value;
  }
  if (fieldName.endsWith('.pin') || fieldName.endsWith('.attenuation') || fieldName.endsWith('.sample_rate') || fieldName.endsWith('.value') || fieldName.endsWith('.freq') || fieldName.endsWith('.duty') || fieldName.endsWith('.scl_pin') || fieldName.endsWith('.sda_pin') || fieldName.endsWith('.sck_pin') || fieldName.endsWith('.ws_pin') || fieldName.endsWith('.sd_pin') || fieldName.endsWith('.bits') || fieldName.endsWith('.rate') || fieldName.endsWith('.mode') && fieldName !== 'gpio.mode') {
    const num = Number(value);
    return Number.isNaN(num) ? value : num;
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

function createGpioRow(pin) {
  const row = document.createElement('tr');
  const pinValue = pin && pin.id !== undefined && pin.id !== null ? pin.id : '';
  const modeValue = pin && pin.mode ? pin.mode : 'out';
  const pullValue = pin && pin.pull ? pin.pull : 'none';
  const valueValue = pin && pin.value !== undefined && pin.value !== null ? pin.value : '';

  row.innerHTML = [
    '<td><input type="number" value="' + pinValue + '" data-field="id" aria-label="GPIO pin id" /></td>',
    '<td><select data-field="mode"><option value="out" ' + (modeValue === 'out' ? 'selected' : '') + '>out</option><option value="in" ' + (modeValue === 'in' ? 'selected' : '') + '>in</option><option value="analog" ' + (modeValue === 'analog' ? 'selected' : '') + '>analog</option></select></td>',
    '<td><select data-field="pull"><option value="none" ' + (pullValue === 'none' ? 'selected' : '') + '>none</option><option value="up" ' + (pullValue === 'up' ? 'selected' : '') + '>up</option><option value="down" ' + (pullValue === 'down' ? 'selected' : '') + '>down</option></select></td>',
    '<td><input type="number" value="' + valueValue + '" data-field="value" aria-label="GPIO value" /></td>',
    '<td><button type="button" class="remove-row" data-action="remove-gpio">Remove</button></td>'
  ].join('');

  return row;
}

function renderGpioTable(data) {
  const tbody = document.getElementById('gpioTableBody');
  if (!tbody) {
    return;
  }

  const gpio = data && data.gpio ? data.gpio : {};
  const pins = Array.isArray(gpio.pins) ? gpio.pins : [];
  tbody.innerHTML = '';

  if (!pins.length) {
    tbody.appendChild(createGpioRow({ id: '', mode: 'out', pull: 'none', value: '' }));
    return;
  }

  pins.forEach(function (pin) {
    tbody.appendChild(createGpioRow(pin));
  });
}

function readGpioRows() {
  const tbody = document.getElementById('gpioTableBody');
  if (!tbody) {
    return [];
  }

  const result = [];
  tbody.querySelectorAll('tr').forEach(function (row) {
    const id = row.querySelector('[data-field="id"]').value;
    const mode = row.querySelector('[data-field="mode"]').value;
    const pull = row.querySelector('[data-field="pull"]').value;
    const value = row.querySelector('[data-field="value"]').value;

    const pin = {};
    if (id !== '') {
      pin.id = Number(id);
    }
    if (mode !== '') {
      pin.mode = mode;
    }
    if (pull !== 'none') {
      pin.pull = pull;
    }
    if (value !== '') {
      pin.value = Number(value);
    }

    if (Object.keys(pin).length > 0) {
      result.push(pin);
    }
  });

  return result;
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

  const response = await fetch('/api/config/hardware', {
    headers: { Authorization: 'Bearer ' + token }
  });

  if (!response.ok) {
    setStatus('Unable to load hardware configuration.', true);
    return;
  }

  const data = await response.json();
  const fields = document.querySelectorAll('[name]');
  fields.forEach(function (field) {
    const fieldName = field.name;
    if (fieldName === 'gpio.enabled') {
      return;
    }

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

  const gpioEnabledField = document.querySelector('[name="gpio.enabled"]');
  if (gpioEnabledField) {
    gpioEnabledField.checked = !!(data && data.gpio && data.gpio.enabled);
  }

  renderGpioTable(data);
}

async function saveConfig(event) {
  event.preventDefault();
  const token = requireAuth();
  if (!token) {
    return;
  }

  const form = event.currentTarget;
  const output = {};
  const gpioToggle = form.querySelector('[name="gpio.enabled"]');
  const gpioRows = readGpioRows();

  output.gpio = {
    enabled: gpioToggle ? gpioToggle.checked : false,
    pins: gpioRows
  };

  const fields = form.querySelectorAll('[name]');
  fields.forEach(function (field) {
    if (field.name === 'gpio.enabled') {
      return;
    }

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

  const response = await fetch('/api/config/hardware', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: 'Bearer ' + token
    },
    body: JSON.stringify(output)
  });

  const data = await response.json();
  if (!response.ok || !data.ok) {
    setStatus(data.error || 'Hardware configuration could not be saved.', true);
    return;
  }

  setStatus('Configuration saved successfully.');
}

function renderMetricCards(entries) {
  const readout = document.getElementById('liveReadout');
  if (!readout) {
    return;
  }

  if (!entries.length) {
    readout.innerHTML = '<div class="metric-empty">No enabled hardware blocks to read.</div>';
    return;
  }

  const cards = entries.map(function (entry) {
    return '<div class="metric-card"><span class="metric-label">' + entry.label + '</span><strong class="metric-value">' + entry.value + '</strong></div>';
  }).join('');

  readout.innerHTML = '<div class="metric-grid">' + cards + '</div>';
}

async function readHardwareState() {
  const token = requireAuth();
  if (!token) {
    return;
  }

  const readout = document.getElementById('liveReadout');
  if (!readout) {
    return;
  }

  readout.innerHTML = '<div class="metric-loading">Reading hardware values...</div>';

  try {
    const response = await fetch('/api/hardware/read', {
      headers: { Authorization: 'Bearer ' + token }
    });

    const data = await response.json();
    if (!response.ok || !data.ok) {
      readout.innerHTML = '<div class="metric-empty metric-error">' + (data.error || 'Unable to read live hardware values.') + '</div>';
      return;
    }

    const entries = [];
    if (data.adc && data.adc.enabled) {
      entries.push({ label: 'ADC', value: (data.adc.value !== null && data.adc.value !== undefined ? data.adc.value : 'n/a') });
    }
    if (data.dac && data.dac.enabled) {
      entries.push({ label: 'DAC', value: (data.dac.value !== null && data.dac.value !== undefined ? data.dac.value : 'n/a') });
    }
    if (data.gpio && data.gpio.enabled) {
      const pins = Array.isArray(data.gpio.pins) ? data.gpio.pins : [];
      if (pins.length) {
        const pinRows = pins.map(function (pin) {
          return 'GPIO' + pin.id + ': ' + pin.value;
        }).join(' | ');
        entries.push({ label: 'GPIO', value: pinRows });
      }
    }
    if (data.pwm && data.pwm.enabled) {
      entries.push({ label: 'PWM', value: 'freq=' + (data.pwm.freq !== null && data.pwm.freq !== undefined ? data.pwm.freq : 'n/a') + ' / duty=' + (data.pwm.duty !== null && data.pwm.duty !== undefined ? data.pwm.duty : 'n/a') });
    }
    if (data.i2c && data.i2c.enabled) {
      entries.push({ label: 'I2C', value: Array.isArray(data.i2c.devices) && data.i2c.devices.length ? data.i2c.devices.join(', ') : 'none' });
    }

    renderMetricCards(entries);
  } catch (error) {
    readout.innerHTML = '<div class="metric-empty metric-error">Hardware read failed.</div>';
  }
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

  const reloadButton = document.getElementById('reloadHardwareConfig');
  if (reloadButton) {
    reloadButton.addEventListener('click', reloadCurrentConfig);
  }

  const resetButton = document.getElementById('resetDeviceBtn');
  if (resetButton) {
    resetButton.addEventListener('click', resetDevice);
  }

  const readButton = document.getElementById('readHardwareBtn');
  if (readButton) {
    readButton.addEventListener('click', readHardwareState);
  }

  const addGpioButton = document.getElementById('addGpioRow');
  if (addGpioButton) {
    addGpioButton.addEventListener('click', function () {
      const tbody = document.getElementById('gpioTableBody');
      if (tbody) {
        tbody.appendChild(createGpioRow({ id: '', mode: 'out', pull: 'none', value: '' }));
      }
    });
  }

  const gpioTableBody = document.getElementById('gpioTableBody');
  if (gpioTableBody) {
    gpioTableBody.addEventListener('click', function (event) {
      const button = event.target.closest('[data-action="remove-gpio"]');
      if (!button) {
        return;
      }
      const row = button.closest('tr');
      if (row) {
        row.remove();
      }
    });
  }

  loadConfig();
  readHardwareState();
  window.setInterval(readHardwareState, 5000);
  document.getElementById('hardwareConfigForm').addEventListener('submit', async function (event) {
    await saveConfig(event);
    await readHardwareState();
  });
}
