var AUTH_USER = 'admin';
var AUTH_PASSWORD = '1234';

document.getElementById('btn-login').addEventListener('click', function () {
  var username = document.getElementById('username').value.trim();
  var password = document.getElementById('password').value;
  if (username === AUTH_USER && password === AUTH_PASSWORD) {
    localStorage.setItem('user_type', AUTH_USER);
    location.href = 'admin.html';
  }
});

document.addEventListener('keypress', function (e) {
  if (e.key === 'Enter') document.getElementById('btn-login').click();
});
