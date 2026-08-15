// Login page logic: validate credentials, store token and redirect to the dashboard.
const form = document.getElementById('loginForm');
const message = document.getElementById('message');

form.addEventListener('submit', async function (event) {
  event.preventDefault();

  const username = document.getElementById('username').value.trim();
  const password = document.getElementById('password').value.trim();

  message.textContent = 'Signing in...';
  message.style.color = '#fbbf24';

  try {
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      },
      body: 'username=' + encodeURIComponent(username) + '&password=' + encodeURIComponent(password)
    });

    const data = await response.json();
    if (data.ok) {
      localStorage.setItem('device_token', data.token);
      window.location.href = '/hardware_cfg_page/?token=' + encodeURIComponent(data.token);
      return;
    }

    message.textContent = data.error || 'Invalid credentials';
    message.style.color = '#fca5a5';
  } catch (error) {
    message.textContent = 'Login failed. Please try again.';
    message.style.color = '#fca5a5';
  }
});
