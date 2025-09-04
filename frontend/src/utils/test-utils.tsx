import React, { ReactElement, ReactNode } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { AuthProvider } from '../context/AuthContext';
import { AccountProvider } from '../context/AccountContext';
import { themeConfig } from '../styles';

const theme = createTheme({
  palette: themeConfig.palette,
});

/**
 * All Providers Wrapper - Following Dependency Inversion Principle
 * Provides all necessary contexts for testing components
 */
interface AllProvidersProps {
  children: ReactNode;
}

const AllProviders: React.FC<AllProvidersProps> = ({ children }) => {
  return (
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <AuthProvider>
          <AccountProvider>
            {children}
          </AccountProvider>
        </AuthProvider>
      </ThemeProvider>
    </BrowserRouter>
  );
};

/**
 * Custom render function with all providers
 * Following SOLID principles - Interface Segregation
 */
const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllProviders, ...options });

/**
 * Render with specific providers - Open/Closed Principle
 * Allows testing with subset of providers when needed
 */
interface CustomProviderOptions {
  withAuth?: boolean;
  withAccount?: boolean;
  withRouter?: boolean;
  withTheme?: boolean;
}

const renderWithProviders = (
  ui: ReactElement,
  options: CustomProviderOptions & Omit<RenderOptions, 'wrapper'> = {}
) => {
  const {
    withAuth = true,
    withAccount = true,
    withRouter = true,
    withTheme = true,
    ...renderOptions
  } = options;

  const Wrapper: React.FC<{ children: ReactNode }> = ({ children }) => {
    let content = children;

    if (withTheme) {
      content = (
        <ThemeProvider theme={theme}>
          <CssBaseline />
          {content}
        </ThemeProvider>
      );
    }

    if (withAuth) {
      content = <AuthProvider>{content}</AuthProvider>;
    }

    if (withAccount) {
      content = <AccountProvider>{content}</AccountProvider>;
    }

    if (withRouter) {
      content = <BrowserRouter>{content}</BrowserRouter>;
    }

    return <>{content}</>;
  };

  return render(ui, { wrapper: Wrapper, ...renderOptions });
};

/**
 * Async testing utilities
 */
export const waitForNextTick = () => new Promise((resolve) => setTimeout(resolve, 0));

export const waitForTime = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms));

/**
 * Mock localStorage for testing
 */
export const createMockLocalStorage = () => {
  let store: Record<string, string> = {};

  return {
    getItem: jest.fn((key: string) => store[key] || null),
    setItem: jest.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: jest.fn((key: string) => {
      delete store[key];
    }),
    clear: jest.fn(() => {
      store = {};
    }),
    length: Object.keys(store).length,
    key: jest.fn((index: number) => Object.keys(store)[index] || null),
  };
};

/**
 * Mock timer utilities for testing time-dependent code
 */
export const setupMockTimers = () => {
  beforeEach(() => {
    jest.useFakeTimers();
  });

  afterEach(() => {
    jest.runOnlyPendingTimers();
    jest.useRealTimers();
  });
};

/**
 * Error boundary for testing error scenarios
 */
interface TestErrorBoundaryState {
  hasError: boolean;
  error?: Error;
}

export class TestErrorBoundary extends React.Component<
  { children: ReactNode },
  TestErrorBoundaryState
> {
  constructor(props: { children: ReactNode }) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error: Error): TestErrorBoundaryState {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Test Error Boundary caught an error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return <div data-testid="error-boundary">Something went wrong</div>;
    }

    return this.props.children;
  }
}

/**
 * Mock IntersectionObserver for components that use it
 */
export const mockIntersectionObserver = () => {
  const mockIntersectionObserver = jest.fn();
  mockIntersectionObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null,
  });
  window.IntersectionObserver = mockIntersectionObserver;
};

/**
 * Mock ResizeObserver for components that use it
 */
export const mockResizeObserver = () => {
  const mockResizeObserver = jest.fn();
  mockResizeObserver.mockReturnValue({
    observe: () => null,
    unobserve: () => null,
    disconnect: () => null,
  });
  window.ResizeObserver = mockResizeObserver;
};

// Re-export everything from React Testing Library
export * from '@testing-library/react';

// Export our custom render as the default render
export { customRender as render, renderWithProviders };