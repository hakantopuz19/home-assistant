const form = document.getElementById('loginForm');
const message = document.getElementById('message');

form.addEventListener('submit', async function (event) {
  event.preventDefault();
  const username = document.getElementById('username').value;
  const password = document.getElementById('password').value;

  message.textContent = 'Signing in...';

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
    } else {
      message.textContent = data.error || 'Invalid credentials';
    }
  } catch (error) {
    message.textContent = 'Login failed';
  }
});
