import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import '@testing-library/jest-dom';
import ErrorRecoveryPanel from '../ErrorRecoveryPanel';

describe('ErrorRecoveryPanel Component', () => {
  const mockOnRetry = jest.fn();
  const mockOnCancel = jest.fn();

  const mockError = {
    code: 'FILE_TOO_LARGE',
    message: 'File size exceeds 50MB limit',
    suggestions: ['Try splitting the CSV file', 'Remove unnecessary columns']
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders error recovery panel with basic error info', () => {
    render(
      <ErrorRecoveryPanel
        error={mockError}
        filename="test.csv"
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('Upload Failed')).toBeInTheDocument();
    expect(screen.getByText('FILE_TOO_LARGE')).toBeInTheDocument();
    expect(screen.getByText('File size exceeds 50MB limit')).toBeInTheDocument();
    expect(screen.getByText('File: test.csv')).toBeInTheDocument();
  });

  it('displays quick fix suggestions', () => {
    render(
      <ErrorRecoveryPanel
        error={mockError}
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('Quick Fixes')).toBeInTheDocument();
    expect(screen.getByText('Try splitting the CSV file')).toBeInTheDocument();
    expect(screen.getByText('Remove unnecessary columns')).toBeInTheDocument();
  });

  it('shows retry button with correct text', () => {
    render(
      <ErrorRecoveryPanel
        error={mockError}
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('Retry Upload')).toBeInTheDocument();
  });

  it('shows retry count when retryCount > 0', () => {
    render(
      <ErrorRecoveryPanel
        error={mockError}
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
        retryCount={2}
        maxRetries={3}
      />
    );

    expect(screen.getByText('Retry (1 left)')).toBeInTheDocument();
  });

  it('shows retrying text when retrying is true', () => {
    render(
      <ErrorRecoveryPanel
        error={mockError}
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
        retrying={true}
      />
    );

    expect(screen.getByText('Retrying...')).toBeInTheDocument();
  });

  it('disables retry button when max retries reached', () => {
    render(
      <ErrorRecoveryPanel
        error={mockError}
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
        retryCount={3}
        maxRetries={3}
      />
    );

    const retryButton = screen.getByRole('button', { name: /retry/i });
    expect(retryButton).toBeDisabled();
  });

  it('shows retry limit warning when max retries reached', () => {
    render(
      <ErrorRecoveryPanel
        error={mockError}
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
        retryCount={3}
        maxRetries={3}
      />
    );

    expect(screen.getByText(/Maximum retry attempts reached/)).toBeInTheDocument();
  });

  it('calls onRetry when retry button is clicked', () => {
    render(
      <ErrorRecoveryPanel
        error={mockError}
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
      />
    );

    const retryButton = screen.getByText('Retry Upload');
    fireEvent.click(retryButton);
    expect(mockOnRetry).toHaveBeenCalledTimes(1);
  });

  it('calls onCancel when cancel button is clicked', () => {
    render(
      <ErrorRecoveryPanel
        error={mockError}
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);
    expect(mockOnCancel).toHaveBeenCalledTimes(1);
  });

  it('expands and collapses error details', () => {
    render(
      <ErrorRecoveryPanel
        error={mockError}
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
        retryCount={1}
        maxRetries={3}
      />
    );

    // Initially collapsed
    expect(screen.queryByText(/Code: FILE_TOO_LARGE/)).not.toBeInTheDocument();

    // Find and click the expand button
    const expandButton = screen.getByRole('button', { name: 'show details' });
    fireEvent.click(expandButton);

    // Should show details
    expect(screen.getByText(/Code: FILE_TOO_LARGE/)).toBeInTheDocument();
    expect(screen.getByText(/Retry Count: 1\/3/)).toBeInTheDocument();
  });

  it('expands and collapses troubleshooting guide', () => {
    render(
      <ErrorRecoveryPanel
        error={mockError}
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
      />
    );

    // Initially collapsed
    expect(screen.queryByText(/Detailed Troubleshooting Steps/)).not.toBeInTheDocument();

    // Click troubleshooting button
    const troubleshootingButton = screen.getByText('Troubleshooting');
    fireEvent.click(troubleshootingButton);

    // Should show troubleshooting guide
    expect(screen.getByText(/🔧 Detailed Troubleshooting Steps/)).toBeInTheDocument();
  });

  it('provides different troubleshooting tips based on error code', () => {
    const invalidCsvError = {
      code: 'INVALID_CSV_FORMAT',
      message: 'Invalid CSV file format',
      suggestions: ['Check file formatting']
    };

    render(
      <ErrorRecoveryPanel
        error={invalidCsvError}
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
      />
    );

    // Click troubleshooting button
    const troubleshootingButton = screen.getByText('Troubleshooting');
    fireEvent.click(troubleshootingButton);

    // Should show CSV format specific tips
    expect(screen.getByText(/Ensure the file is saved as UTF-8 encoded CSV/)).toBeInTheDocument();
  });

  it('provides generic troubleshooting tips for unknown error codes', () => {
    const unknownError = {
      code: 'UNKNOWN_ERROR',
      message: 'Something went wrong',
      suggestions: ['Try again']
    };

    render(
      <ErrorRecoveryPanel
        error={unknownError}
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
      />
    );

    // Click troubleshooting button
    const troubleshootingButton = screen.getByText('Troubleshooting');
    fireEvent.click(troubleshootingButton);

    // Should show generic tips
    expect(screen.getByText(/Check your internet connection and try again/)).toBeInTheDocument();
  });

  it('disables cancel button when retrying', () => {
    render(
      <ErrorRecoveryPanel
        error={mockError}
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
        retrying={true}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    expect(cancelButton).toBeDisabled();
  });

  it('handles permission denied error correctly', () => {
    const permissionError = {
      code: 'PERMISSION_DENIED',
      message: 'Access denied to this account',
      suggestions: ['Contact administrator for access']
    };

    render(
      <ErrorRecoveryPanel
        error={permissionError}
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.getByText('Access denied to this account')).toBeInTheDocument();
    expect(screen.getByText('Contact administrator for access')).toBeInTheDocument();
  });

  it('renders without filename when not provided', () => {
    render(
      <ErrorRecoveryPanel
        error={mockError}
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
      />
    );

    expect(screen.queryByText(/File:/)).not.toBeInTheDocument();
  });

  it('shows correct error severity styling', () => {
    const warningError = {
      code: 'FILE_TOO_LARGE',
      message: 'File too large',
      suggestions: ['Reduce file size']
    };

    const { container } = render(
      <ErrorRecoveryPanel
        error={warningError}
        onRetry={mockOnRetry}
        onCancel={mockOnCancel}
      />
    );

    // Check if the alert has warning severity (orange/yellow styling)
    const alert = container.querySelector('.MuiAlert-standardWarning');
    expect(alert).toBeInTheDocument();
  });
});