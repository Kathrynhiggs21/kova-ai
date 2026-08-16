const { startApp, askGemini } = require('./index');

describe('startApp', () => {
  test('logs and returns start message', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation(() => {});
    const message = startApp();
    expect(consoleSpy).toHaveBeenCalledWith('Kova AI application started');
    expect(message).toBe('Kova AI application started');
    consoleSpy.mockRestore();
  });
});

describe('askGemini', () => {
  test('throws when GEMINI_API_KEY is not set', async () => {
    const original = process.env.GEMINI_API_KEY;
    delete process.env.GEMINI_API_KEY;
    await expect(askGemini('hello')).rejects.toThrow('GEMINI_API_KEY environment variable is not set');
    if (original !== undefined) process.env.GEMINI_API_KEY = original;
  });

  test('calls Gemini API and returns text when key is set', async () => {
    process.env.GEMINI_API_KEY = 'test-key';

    const mockGenerateContent = jest.fn().mockResolvedValue({
      response: { text: () => 'Gemini response' },
    });
    const mockGetGenerativeModel = jest.fn().mockReturnValue({ generateContent: mockGenerateContent });
    const mockGenAI = jest.fn().mockImplementation(() => ({ getGenerativeModel: mockGetGenerativeModel }));

    jest.resetModules();
    jest.doMock('@google/generative-ai', () => ({ GoogleGenerativeAI: mockGenAI }));

    const { askGemini: askGeminiMocked } = require('./index');
    const result = await askGeminiMocked('test prompt');
    expect(result).toBe('Gemini response');
    expect(mockGetGenerativeModel).toHaveBeenCalledWith({ model: 'gemini-pro' });
    expect(mockGenerateContent).toHaveBeenCalledWith('test prompt');

    delete process.env.GEMINI_API_KEY;
    jest.resetModules();
  });
});
