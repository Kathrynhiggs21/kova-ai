const { start } = require('../src/index');

test('start function exists', () => {
  expect(typeof start).toBe('function');
});
