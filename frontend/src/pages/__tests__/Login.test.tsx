import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import Login from '../Login';
import * as api from '../../services/api';

// Mock the API module
jest.mock('../../services/api');
const mockApi = api as jest.Mocked<typeof api>;

// Mock react-router-dom
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

const theme = createTheme();

const renderLogin = () => {
  return render(
    <BrowserRouter>
      <ThemeProvider theme={theme}>
        <Login />
      </ThemeProvider>
    </BrowserRouter>
  );
};

describe('Login Component', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Clear localStorage
    localStorage.clear();
  });

  it('renders login form elements', () => {
    renderLogin();
    
    expect(screen.getByLabelText(/username/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/password/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /login/i })).toBeInTheDocument();
  });

  it('displays initial state correctly', () => {
    renderLogin();
    
    expect(screen.getByText(/ebay manager/i)).toBeInTheDocument();
    expect(screen.getByText(/sign in to your account/i)).toBeInTheDocument();
  });

  it('handles input changes', async () => {
    const user = userEvent.setup();
    renderLogin();
    
    const usernameInput = screen.getByLabelText(/username/i);
    const passwordInput = screen.getByLabelText(/password/i);
    
    await user.type(usernameInput, 'testuser');
    await user.type(passwordInput, 'testpass');
    
    expect(usernameInput).toHaveValue('testuser');
    expect(passwordInput).toHaveValue('testpass');
  });

  it('validates required fields', async () => {
    const user = userEvent.setup();
    renderLogin();
    
    const loginButton = screen.getByRole('button', { name: /login/i });
    await user.click(loginButton);
    
    // Should show validation messages for empty fields
    expect(screen.getByText(/username is required/i)).toBeInTheDocument();
    expect(screen.getByText(/password is required/i)).toBeInTheDocument();
  });

  it('handles successful login', async () => {
    const user = userEvent.setup();
    const mockLoginResponse = {
      access_token: 'mock-token',
      token_type: 'bearer'
    };
    
    mockApi.login.mockResolvedValue(mockLoginResponse);
    
    renderLogin();
    
    await user.type(screen.getByLabelText(/username/i), 'admin');
    await user.type(screen.getByLabelText(/password/i), 'admin123');
    await user.click(screen.getByRole('button', { name: /login/i }));
    
    await waitFor(() => {
      expect(mockApi.login).toHaveBeenCalledWith({
        username: 'admin',
        password: 'admin123'
      });
    });
    
    // Should store token and navigate
    expect(localStorage.getItem('token')).toBe('mock-token');
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
  });

  it('handles login error', async () => {
    const user = userEvent.setup();
    mockApi.login.mockRejectedValue(new Error('Invalid credentials'));
    
    renderLogin();
    
    await user.type(screen.getByLabelText(/username/i), 'invalid');
    await user.type(screen.getByLabelText(/password/i), 'invalid');
    await user.click(screen.getByRole('button', { name: /login/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
    
    expect(localStorage.getItem('token')).toBeNull();
    expect(mockNavigate).not.toHaveBeenCalled();
  });

  it('shows loading state during login', async () => {
    const user = userEvent.setup();
    // Create a promise that we can control
    let resolveLogin: (value: any) => void;
    const loginPromise = new Promise(resolve => {
      resolveLogin = resolve;
    });
    
    mockApi.login.mockReturnValue(loginPromise);
    
    renderLogin();
    
    await user.type(screen.getByLabelText(/username/i), 'admin');
    await user.type(screen.getByLabelText(/password/i), 'admin123');
    await user.click(screen.getByRole('button', { name: /login/i }));
    
    // Should show loading state
    expect(screen.getByRole('button')).toBeDisabled();
    expect(screen.getByText(/signing in/i)).toBeInTheDocument();
    
    // Resolve the promise
    resolveLogin!({ access_token: 'token', token_type: 'bearer' });
    
    await waitFor(() => {
      expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
    });
  });

  it('prevents double submission', async () => {
    const user = userEvent.setup();
    mockApi.login.mockImplementation(() => new Promise(resolve => 
      setTimeout(() => resolve({ access_token: 'token', token_type: 'bearer' }), 100)
    ));
    
    renderLogin();
    
    await user.type(screen.getByLabelText(/username/i), 'admin');
    await user.type(screen.getByLabelText(/password/i), 'admin123');
    
    const loginButton = screen.getByRole('button', { name: /login/i });
    await user.click(loginButton);
    await user.click(loginButton); // Second click should be ignored
    
    await waitFor(() => {
      expect(mockApi.login).toHaveBeenCalledTimes(1);
    });
  });

  it('handles keyboard navigation', async () => {
    const user = userEvent.setup();
    renderLogin();
    
    // Tab through form elements
    await user.tab();
    expect(screen.getByLabelText(/username/i)).toHaveFocus();
    
    await user.tab();
    expect(screen.getByLabelText(/password/i)).toHaveFocus();
    
    await user.tab();
    expect(screen.getByRole('button', { name: /login/i })).toHaveFocus();
  });

  it('handles enter key submission', async () => {
    const user = userEvent.setup();
    mockApi.login.mockResolvedValue({
      access_token: 'token',
      token_type: 'bearer'
    });
    
    renderLogin();
    
    await user.type(screen.getByLabelText(/username/i), 'admin');
    await user.type(screen.getByLabelText(/password/i), 'admin123');
    
    // Press enter on password field
    await user.keyboard('{Enter}');
    
    await waitFor(() => {
      expect(mockApi.login).toHaveBeenCalled();
    });
  });

  it('clears error message on input change', async () => {
    const user = userEvent.setup();
    mockApi.login.mockRejectedValue(new Error('Invalid credentials'));
    
    renderLogin();
    
    // Trigger error
    await user.type(screen.getByLabelText(/username/i), 'invalid');
    await user.type(screen.getByLabelText(/password/i), 'invalid');
    await user.click(screen.getByRole('button', { name: /login/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/invalid credentials/i)).toBeInTheDocument();
    });
    
    // Change input should clear error
    await user.type(screen.getByLabelText(/username/i), 'a');
    
    expect(screen.queryByText(/invalid credentials/i)).not.toBeInTheDocument();
  });

  it('handles network error gracefully', async () => {
    const user = userEvent.setup();
    mockApi.login.mockRejectedValue(new Error('Network Error'));
    
    renderLogin();
    
    await user.type(screen.getByLabelText(/username/i), 'admin');
    await user.type(screen.getByLabelText(/password/i), 'admin123');
    await user.click(screen.getByRole('button', { name: /login/i }));
    
    await waitFor(() => {
      expect(screen.getByText(/network error/i)).toBeInTheDocument();
    });
  });

  it('redirects if already logged in', () => {
    localStorage.setItem('token', 'existing-token');
    
    renderLogin();
    
    expect(mockNavigate).toHaveBeenCalledWith('/dashboard');
  });

  it('has proper accessibility attributes', () => {
    renderLogin();
    
    const form = screen.getByRole('main') || screen.getByRole('form');
    expect(form).toBeInTheDocument();
    
    const usernameInput = screen.getByLabelText(/username/i);
    expect(usernameInput).toHaveAttribute('type', 'text');
    expect(usernameInput).toHaveAttribute('required');
    
    const passwordInput = screen.getByLabelText(/password/i);
    expect(passwordInput).toHaveAttribute('type', 'password');
    expect(passwordInput).toHaveAttribute('required');
    
    const loginButton = screen.getByRole('button', { name: /login/i });
    expect(loginButton).toHaveAttribute('type', 'submit');
  });
});