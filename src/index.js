const { GoogleGenerativeAI } = require('@google/generative-ai');

function startApp() {
  const message = 'Kova AI application started';
  console.log(message);
  return message;
}

async function askGemini(prompt) {
  const apiKey = process.env.GEMINI_API_KEY;
  if (!apiKey) {
    throw new Error('GEMINI_API_KEY environment variable is not set');
  }
  const genAI = new GoogleGenerativeAI(apiKey);
  const model = genAI.getGenerativeModel({ model: 'gemini-pro' });
  const result = await model.generateContent(prompt);
  return result.response.text();
}

if (require.main === module) {
  startApp();
}

module.exports = { startApp, askGemini };
