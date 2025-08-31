import React, { useState } from 'react';
import {
  Box,
  Typography,
  TextField,
  Button,
  Paper,
  Divider,
  Avatar,
  CircularProgress,
  Snackbar,
  Alert,
} from '@mui/material';
import { Add, Person } from '@mui/icons-material';
import OrderDataService from '../../services/OrderDataService';
import { colors } from '../../styles/common/colors';
import { spacing } from '../../styles/common/spacing';
import type { Order, OrderNote } from '../../types';

interface OrderNotesManagerProps {
  order: Order;
  onNotesUpdate: (orderId: number, notes: OrderNote[]) => void;
}

interface INoteManager {
  validateNote(note: string): string[];
  formatNoteDate(dateString: string): string;
}

class NoteManager implements INoteManager {
  validateNote(note: string): string[] {
    const errors: string[] = [];
    
    if (!note.trim()) {
      errors.push('Note cannot be empty');
    } else if (note.trim().length < 3) {
      errors.push('Note must be at least 3 characters');
    } else if (note.length > 500) {
      errors.push('Note cannot exceed 500 characters');
    }
    
    return errors;
  }

  formatNoteDate(dateString: string): string {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  }
}

const noteManager = new NoteManager();

const OrderNotesManager: React.FC<OrderNotesManagerProps> = ({ order, onNotesUpdate }) => {
  const [newNote, setNewNote] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const notes = order.notes || [];

  const handleAddNote = async () => {
    const trimmedNote = newNote.trim();
    const validationErrors = noteManager.validateNote(trimmedNote);
    
    if (validationErrors.length > 0) {
      setError(validationErrors.join(', '));
      return;
    }

    setLoading(true);
    try {
      const addedNote = await OrderDataService.addOrderNote(order.id, trimmedNote);
      const updatedNotes = [...notes, addedNote];
      onNotesUpdate(order.id, updatedNotes);
      setNewNote('');
      setError(null);
    } catch (error) {
      console.error('Failed to add note:', error);
      setError('Failed to add note. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const NoteItem: React.FC<{ note: OrderNote }> = ({ note }) => (
    <Paper
      elevation={1}
      sx={{
        padding: spacing.medium,
        marginBottom: spacing.small,
        backgroundColor: colors.background.paper,
        border: `1px solid ${colors.divider}`,
      }}
    >
      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: spacing.small }}>
        <Avatar sx={{ width: 32, height: 32, backgroundColor: colors.primary }}>
          <Person sx={{ fontSize: 18 }} />
        </Avatar>
        
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="body2" sx={{ marginBottom: spacing.xsmall }}>
            {note.note}
          </Typography>
          <Typography 
            variant="caption" 
            sx={{ color: colors.text.secondary }}
          >
            {noteManager.formatNoteDate(note.created_at)}
          </Typography>
        </Box>
      </Box>
    </Paper>
  );

  return (
    <Box>
      <Typography variant="h6" sx={{ marginBottom: spacing.medium, fontWeight: 600 }}>
        Order Notes
      </Typography>

      {notes.length > 0 ? (
        <Box sx={{ marginBottom: spacing.medium, maxHeight: 300, overflowY: 'auto' }}>
          {notes.map((note) => (
            <NoteItem key={note.id} note={note} />
          ))}
        </Box>
      ) : (
        <Typography 
          variant="body2" 
          sx={{ 
            color: colors.text.secondary, 
            marginBottom: spacing.medium,
            fontStyle: 'italic',
          }}
        >
          No notes added yet
        </Typography>
      )}

      <Divider sx={{ marginY: spacing.medium }} />

      <Box>
        <Typography variant="subtitle2" sx={{ marginBottom: spacing.small, fontWeight: 600 }}>
          Add New Note
        </Typography>
        
        <TextField
          fullWidth
          multiline
          rows={3}
          value={newNote}
          onChange={(e) => setNewNote(e.target.value)}
          placeholder="Add a note about this order..."
          variant="outlined"
          disabled={loading}
          error={!!error}
          helperText={error || `${newNote.length}/500 characters`}
          sx={{ marginBottom: spacing.medium }}
        />

        <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
          <Button
            variant="contained"
            startIcon={loading ? <CircularProgress size={16} /> : <Add />}
            onClick={handleAddNote}
            disabled={loading || !newNote.trim()}
          >
            Add Note
          </Button>
        </Box>
      </Box>

      <Snackbar 
        open={!!error} 
        autoHideDuration={6000} 
        onClose={() => setError(null)}
      >
        <Alert severity="error" onClose={() => setError(null)}>
          {error}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default OrderNotesManager;