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

const token = requireAuth();
if (token) {
  decorateLinks(token);
  document.getElementById('logoutBtn').addEventListener('click', function () {
    localStorage.removeItem('device_token');
    window.location.href = '/login';
  });
}
