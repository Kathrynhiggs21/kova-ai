const { startApp } = require('./index');

describe('startApp', () => {
  test('logs and returns start message', () => {
    const consoleSpy = jest.spyOn(console, 'log').mockImplementation(() => {});
    const message = startApp();
    expect(consoleSpy).toHaveBeenCalledWith('Kova AI application started');
    expect(message).toBe('Kova AI application started');
    consoleSpy.mockRestore();
  });
});
