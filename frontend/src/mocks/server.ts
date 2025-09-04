// @ts-nocheck
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

/**
 * Mock Service Worker Server Setup for Testing
 * 
 * Following Single Responsibility Principle:
 * - Only handles MSW server setup and configuration
 */

// Setup MSW server with our handlers
export const server = setupServer(...handlers);

// Establish API mocking before all tests
beforeAll(() => {
  server.listen({
    onUnhandledRequest: 'warn',
  });
});

// Reset any runtime request handlers we may add during the tests
afterEach(() => {
  server.resetHandlers();
});

// Clean up after the tests are finished
afterAll(() => {
  server.close();
});

export default server;