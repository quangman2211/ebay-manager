import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import '@testing-library/jest-dom';
import ProgressBar from '../ProgressBar';

describe('ProgressBar Component', () => {
  const mockOnCancel = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders progress bar in processing state', () => {
    render(
      <ProgressBar
        uploadId="test-id"
        filename="test.csv"
        state="processing"
        message="Processing..."
        progressPercent={50}
        startedAt="2025-01-01T00:00:00Z"
        onCancel={mockOnCancel}
        showCancel={true}
      />
    );

    expect(screen.getByText('Upload Progress')).toBeInTheDocument();
    expect(screen.getByText('Processing')).toBeInTheDocument();
    expect(screen.getByText('Processing...')).toBeInTheDocument();
    expect(screen.getByText('File: test.csv')).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument();
  });

  it('renders progress bar in completed state', () => {
    render(
      <ProgressBar
        state="completed"
        message="Upload completed successfully"
        progressPercent={100}
      />
    );

    expect(screen.getByText('Completed')).toBeInTheDocument();
    expect(screen.getByText('Upload completed successfully')).toBeInTheDocument();
    expect(screen.getByText('100%')).toBeInTheDocument();
  });

  it('renders progress bar in failed state', () => {
    render(
      <ProgressBar
        state="failed"
        message="Upload failed"
        progressPercent={75}
      />
    );

    expect(screen.getByText('Failed')).toBeInTheDocument();
    expect(screen.getByText('Upload failed')).toBeInTheDocument();
  });

  it('renders progress bar in cancelled state', () => {
    render(
      <ProgressBar
        state="cancelled"
        message="Upload cancelled"
        progressPercent={30}
      />
    );

    expect(screen.getByText('Cancelled')).toBeInTheDocument();
    expect(screen.getByText('Upload cancelled')).toBeInTheDocument();
  });

  it('shows cancel button when in processing state and showCancel is true', () => {
    render(
      <ProgressBar
        state="processing"
        message="Processing..."
        progressPercent={25}
        onCancel={mockOnCancel}
        showCancel={true}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    expect(cancelButton).toBeInTheDocument();
  });

  it('does not show cancel button when showCancel is false', () => {
    render(
      <ProgressBar
        state="processing"
        message="Processing..."
        progressPercent={25}
        onCancel={mockOnCancel}
        showCancel={false}
      />
    );

    expect(screen.queryByText('Cancel')).not.toBeInTheDocument();
  });

  it('does not show cancel button when not in processing state', () => {
    render(
      <ProgressBar
        state="completed"
        message="Completed"
        progressPercent={100}
        onCancel={mockOnCancel}
        showCancel={true}
      />
    );

    expect(screen.queryByText('Cancel')).not.toBeInTheDocument();
  });

  it('calls onCancel when cancel button is clicked', () => {
    render(
      <ProgressBar
        state="processing"
        message="Processing..."
        progressPercent={25}
        onCancel={mockOnCancel}
        showCancel={true}
      />
    );

    const cancelButton = screen.getByText('Cancel');
    fireEvent.click(cancelButton);
    expect(mockOnCancel).toHaveBeenCalledTimes(1);
  });

  it('displays file information when provided', () => {
    render(
      <ProgressBar
        uploadId="test-upload-123"
        filename="sample.csv"
        state="processing"
        message="Processing..."
        progressPercent={60}
      />
    );

    expect(screen.getByText(/File: sample\.csv/)).toBeInTheDocument();
    expect(screen.getByText(/ID: test-upl\.\.\./)).toBeInTheDocument();
  });

  it('does not display file information when not provided', () => {
    render(
      <ProgressBar
        state="processing"
        message="Processing..."
        progressPercent={60}
      />
    );

    expect(screen.queryByText(/File:/)).not.toBeInTheDocument();
    expect(screen.queryByText(/ID:/)).not.toBeInTheDocument();
  });

  it('displays elapsed time when startedAt is provided', () => {
    const pastTime = new Date(Date.now() - 5000).toISOString(); // 5 seconds ago
    
    render(
      <ProgressBar
        state="completed"
        message="Completed"
        progressPercent={100}
        startedAt={pastTime}
      />
    );

    expect(screen.getByText(/Completed for 5s/)).toBeInTheDocument();
  });

  it('estimates time remaining during processing', () => {
    const pastTime = new Date(Date.now() - 2000).toISOString(); // 2 seconds ago
    
    render(
      <ProgressBar
        state="processing"
        message="Processing..."
        progressPercent={50}
        startedAt={pastTime}
      />
    );

    // Should show estimated time remaining
    expect(screen.getByText(/~.*remaining/)).toBeInTheDocument();
  });

  it('handles progress percentage at bounds correctly', () => {
    const { rerender } = render(
      <ProgressBar
        state="processing"
        message="Starting..."
        progressPercent={0}
      />
    );

    expect(screen.getByText('0%')).toBeInTheDocument();

    rerender(
      <ProgressBar
        state="completed"
        message="Completed"
        progressPercent={100}
      />
    );

    expect(screen.getByText('100%')).toBeInTheDocument();

    // Test over 100%
    rerender(
      <ProgressBar
        state="processing"
        message="Processing..."
        progressPercent={150}
      />
    );

    expect(screen.getByText('150%')).toBeInTheDocument();
  });

  it('handles missing optional props gracefully', () => {
    render(
      <ProgressBar
        state="processing"
        message="Processing..."
        progressPercent={50}
      />
    );

    expect(screen.getByText('Upload Progress')).toBeInTheDocument();
    expect(screen.getByText('Processing...')).toBeInTheDocument();
    expect(screen.getByText('50%')).toBeInTheDocument();
  });
});