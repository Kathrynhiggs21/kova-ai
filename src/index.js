function startApp() {
  const message = 'Kova AI application started';
  console.log(message);
  return message;
}

if (require.main === module) {
  startApp();
}

module.exports = { startApp };
