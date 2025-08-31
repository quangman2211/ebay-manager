import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import '@testing-library/jest-dom';
import InlineEditableField from '../InlineEditableField';

describe('InlineEditableField', () => {
  const mockOnSave = jest.fn();
  const mockValidation = jest.fn();

  const defaultProps = {
    value: 'Test Value',
    onSave: mockOnSave,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders value in display mode', () => {
    render(<InlineEditableField {...defaultProps} />);
    
    expect(screen.getByText('Test Value')).toBeInTheDocument();
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
  });

  it('shows edit icon on hover', async () => {
    const user = userEvent.setup();
    render(<InlineEditableField {...defaultProps} />);
    
    const displayElement = screen.getByText('Test Value').parentElement!;
    await user.hover(displayElement);
    
    expect(screen.getByTestId('EditIcon')).toBeVisible();
  });

  it('enters edit mode when clicked', async () => {
    const user = userEvent.setup();
    render(<InlineEditableField {...defaultProps} />);
    
    const displayElement = screen.getByText('Test Value');
    await user.click(displayElement);
    
    expect(screen.getByRole('textbox')).toBeInTheDocument();
    expect(screen.getByDisplayValue('Test Value')).toBeInTheDocument();
  });

  it('shows save and cancel buttons in edit mode', async () => {
    const user = userEvent.setup();
    render(<InlineEditableField {...defaultProps} />);
    
    await user.click(screen.getByText('Test Value'));
    
    expect(screen.getByTestId('CheckIcon')).toBeInTheDocument();
    expect(screen.getByTestId('CancelIcon')).toBeInTheDocument();
  });

  it('saves value when save button is clicked', async () => {
    const user = userEvent.setup();
    mockOnSave.mockResolvedValue(undefined);
    
    render(<InlineEditableField {...defaultProps} />);
    
    await user.click(screen.getByText('Test Value'));
    
    const input = screen.getByRole('textbox');
    await user.clear(input);
    await user.type(input, 'New Value');
    
    const saveButton = screen.getByTestId('CheckIcon');
    await user.click(saveButton);
    
    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledWith('New Value');
    });
    
    expect(screen.getByText('Test Value')).toBeInTheDocument(); // Back to display mode
  });

  it('cancels edit when cancel button is clicked', async () => {
    const user = userEvent.setup();
    render(<InlineEditableField {...defaultProps} />);
    
    await user.click(screen.getByText('Test Value'));
    
    const input = screen.getByRole('textbox');
    await user.clear(input);
    await user.type(input, 'New Value');
    
    const cancelButton = screen.getByTestId('CancelIcon');
    await user.click(cancelButton);
    
    expect(mockOnSave).not.toHaveBeenCalled();
    expect(screen.getByText('Test Value')).toBeInTheDocument();
  });

  it('saves value when Enter key is pressed', async () => {
    const user = userEvent.setup();
    mockOnSave.mockResolvedValue(undefined);
    
    render(<InlineEditableField {...defaultProps} />);
    
    await user.click(screen.getByText('Test Value'));
    
    const input = screen.getByRole('textbox');
    await user.clear(input);
    await user.type(input, 'New Value{enter}');
    
    await waitFor(() => {
      expect(mockOnSave).toHaveBeenCalledWith('New Value');
    });
  });

  it('cancels edit when Escape key is pressed', async () => {
    const user = userEvent.setup();
    render(<InlineEditableField {...defaultProps} />);
    
    await user.click(screen.getByText('Test Value'));
    
    const input = screen.getByRole('textbox');
    await user.clear(input);
    await user.type(input, 'New Value');
    
    fireEvent.keyDown(input, { key: 'Escape' });
    
    expect(mockOnSave).not.toHaveBeenCalled();
    expect(screen.getByText('Test Value')).toBeInTheDocument();
  });

  it('handles validation errors', async () => {
    const user = userEvent.setup();
    const validation = jest.fn().mockReturnValue('Invalid input');
    
    render(<InlineEditableField {...defaultProps} validation={validation} />);
    
    await user.click(screen.getByText('Test Value'));
    
    const input = screen.getByRole('textbox');
    await user.clear(input);
    await user.type(input, 'Invalid Value');
    
    const saveButton = screen.getByTestId('CheckIcon');
    await user.click(saveButton);
    
    expect(validation).toHaveBeenCalledWith('Invalid Value');
    expect(screen.getByText('Invalid input')).toBeInTheDocument();
    expect(mockOnSave).not.toHaveBeenCalled();
  });

  it('shows loading state during save', async () => {
    const user = userEvent.setup();
    mockOnSave.mockImplementation(() => new Promise(resolve => setTimeout(resolve, 1000)));
    
    render(<InlineEditableField {...defaultProps} />);
    
    await user.click(screen.getByText('Test Value'));
    const saveButton = screen.getByTestId('CheckIcon');
    await user.click(saveButton);
    
    expect(screen.getByRole('progressbar')).toBeInTheDocument();
    expect(screen.getByRole('textbox')).toBeDisabled();
  });

  it('handles save errors gracefully', async () => {
    const user = userEvent.setup();
    mockOnSave.mockRejectedValue({ response: { data: { detail: 'Save failed' } } });
    
    render(<InlineEditableField {...defaultProps} />);
    
    await user.click(screen.getByText('Test Value'));
    const saveButton = screen.getByTestId('CheckIcon');
    await user.click(saveButton);
    
    await waitFor(() => {
      expect(screen.getByText('Save failed')).toBeInTheDocument();
    });
    
    // Should stay in edit mode
    expect(screen.getByRole('textbox')).toBeInTheDocument();
  });

  it('formats price display correctly', () => {
    render(<InlineEditableField {...defaultProps} value="19.99" type="price" />);
    
    expect(screen.getByText('$19.99')).toBeInTheDocument();
  });

  it('shows dollar sign in price input', async () => {
    const user = userEvent.setup();
    render(<InlineEditableField {...defaultProps} value="19.99" type="price" />);
    
    await user.click(screen.getByText('$19.99'));
    
    expect(screen.getByText('$')).toBeInTheDocument();
  });

  it('configures number input correctly', async () => {
    const user = userEvent.setup();
    render(<InlineEditableField {...defaultProps} value="10" type="number" />);
    
    await user.click(screen.getByText('10'));
    
    const input = screen.getByRole('spinbutton');
    expect(input).toBeInTheDocument();
    expect(input).toHaveAttribute('min', '0');
  });

  it('does not enter edit mode when disabled', async () => {
    const user = userEvent.setup();
    render(<InlineEditableField {...defaultProps} disabled={true} />);
    
    await user.click(screen.getByText('Test Value'));
    
    expect(screen.queryByRole('textbox')).not.toBeInTheDocument();
  });

  it('shows disabled styling when disabled', () => {
    render(<InlineEditableField {...defaultProps} disabled={true} />);
    
    const textElement = screen.getByText('Test Value');
    expect(textElement).toHaveStyle('color: rgba(0, 0, 0, 0.38)'); // disabled color
  });

  it('does not show edit icon when disabled', async () => {
    const user = userEvent.setup();
    render(<InlineEditableField {...defaultProps} disabled={true} />);
    
    const displayElement = screen.getByText('Test Value').parentElement!;
    await user.hover(displayElement);
    
    const editIcon = screen.queryByTestId('EditIcon');
    expect(editIcon).toHaveStyle('opacity: 0');
  });

  it('updates display value when value prop changes', () => {
    const { rerender } = render(<InlineEditableField {...defaultProps} value="Original" />);
    
    expect(screen.getByText('Original')).toBeInTheDocument();
    
    rerender(<InlineEditableField {...defaultProps} value="Updated" />);
    
    expect(screen.getByText('Updated')).toBeInTheDocument();
  });

  it('shows placeholder in input', async () => {
    const user = userEvent.setup();
    render(<InlineEditableField {...defaultProps} placeholder="Enter value" />);
    
    await user.click(screen.getByText('Test Value'));
    
    expect(screen.getByPlaceholderText('Enter value')).toBeInTheDocument();
  });

  it('focuses input when entering edit mode', async () => {
    const user = userEvent.setup();
    render(<InlineEditableField {...defaultProps} />);
    
    await user.click(screen.getByText('Test Value'));
    
    const input = screen.getByRole('textbox');
    expect(input).toHaveFocus();
  });

  it('handles generic save errors', async () => {
    const user = userEvent.setup();
    mockOnSave.mockRejectedValue(new Error('Generic error'));
    
    render(<InlineEditableField {...defaultProps} />);
    
    await user.click(screen.getByText('Test Value'));
    const saveButton = screen.getByTestId('CheckIcon');
    await user.click(saveButton);
    
    await waitFor(() => {
      expect(screen.getByText('Failed to save')).toBeInTheDocument();
    });
  });
});