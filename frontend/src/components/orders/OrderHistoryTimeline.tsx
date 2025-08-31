import React from 'react';
import {
  Box,
  Typography,
  Paper,
  Avatar,
  Chip,
} from '@mui/material';
import {
  ShoppingCart,
  PlayArrow,
  LocalShipping,
  CheckCircle,
  Cancel,
  Note,
  Edit,
} from '@mui/icons-material';
import { colors } from '../../styles/common/colors';
import { spacing } from '../../styles/common/spacing';
import type { Order, OrderNote } from '../../types';

interface OrderHistoryTimelineProps {
  order: Order;
}

interface IHistoryEvent {
  id: string;
  type: 'status_change' | 'note_added' | 'tracking_updated' | 'order_created';
  timestamp: string;
  description: string;
  icon: React.ElementType;
  color: string;
  user?: string;
}

interface ITimelineProcessor {
  generateTimelineEvents(order: Order): IHistoryEvent[];
  formatEventTime(timestamp: string): string;
}

class TimelineProcessor implements ITimelineProcessor {
  generateTimelineEvents(order: Order): IHistoryEvent[] {
    const events: IHistoryEvent[] = [];

    events.push({
      id: `created-${order.id}`,
      type: 'order_created',
      timestamp: order.created_at,
      description: 'Order created',
      icon: ShoppingCart,
      color: colors.info,
    });

    const currentStatus = order.order_status?.status;
    if (currentStatus && currentStatus !== 'pending') {
      const statusEvents = this.generateStatusEvents(order);
      events.push(...statusEvents);
    }

    if (order.csv_row['Tracking Number']) {
      events.push({
        id: `tracking-${order.id}`,
        type: 'tracking_updated',
        timestamp: order.order_status?.updated_at || order.created_at,
        description: `Tracking number added: ${order.csv_row['Tracking Number']}`,
        icon: LocalShipping,
        color: colors.secondary,
      });
    }

    if (order.notes && order.notes.length > 0) {
      const noteEvents = order.notes.map((note) => ({
        id: `note-${note.id}`,
        type: 'note_added' as const,
        timestamp: note.created_at,
        description: `Note added: ${note.note}`,
        icon: Note,
        color: colors.primary,
        user: `User ${note.created_by}`,
      }));
      events.push(...noteEvents);
    }

    return events.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }

  private generateStatusEvents(order: Order): IHistoryEvent[] {
    const events: IHistoryEvent[] = [];
    const currentStatus = order.order_status?.status;
    
    const statusFlow: Record<string, { icon: React.ElementType; color: string; description: string }> = {
      processing: { icon: PlayArrow, color: colors.info, description: 'Order started processing' },
      shipped: { icon: LocalShipping, color: colors.secondary, description: 'Order shipped' },
      completed: { icon: CheckCircle, color: colors.success, description: 'Order completed' },
      cancelled: { icon: Cancel, color: colors.error, description: 'Order cancelled' },
    };

    if (currentStatus && statusFlow[currentStatus]) {
      const statusInfo = statusFlow[currentStatus];
      events.push({
        id: `status-${order.id}-${currentStatus}`,
        type: 'status_change',
        timestamp: order.order_status?.updated_at || order.created_at,
        description: statusInfo.description,
        icon: statusInfo.icon,
        color: statusInfo.color,
        user: `User ${order.order_status?.updated_by || 'System'}`,
      });
    }

    return events;
  }

  formatEventTime(timestamp: string): string {
    const date = new Date(timestamp);
    const now = new Date();
    const diffTime = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor(diffTime / (1000 * 60 * 60));
    const diffMinutes = Math.floor(diffTime / (1000 * 60));

    if (diffDays > 0) {
      return `${diffDays} day${diffDays > 1 ? 's' : ''} ago`;
    } else if (diffHours > 0) {
      return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    } else if (diffMinutes > 0) {
      return `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''} ago`;
    } else {
      return 'Just now';
    }
  }
}

const timelineProcessor = new TimelineProcessor();

const OrderHistoryTimeline: React.FC<OrderHistoryTimelineProps> = ({ order }) => {
  const events = timelineProcessor.generateTimelineEvents(order);

  const TimelineEvent: React.FC<{ event: IHistoryEvent; isLast: boolean }> = ({ event, isLast }) => {
    const IconComponent = event.icon;
    
    return (
      <Box sx={{ display: 'flex', position: 'relative' }}>
        <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', marginRight: spacing.medium }}>
          <Avatar
            sx={{
              width: 32,
              height: 32,
              backgroundColor: event.color,
              color: colors.background.paper,
            }}
          >
            <IconComponent sx={{ fontSize: 18 }} />
          </Avatar>
          
          {!isLast && (
            <Box
              sx={{
                width: 2,
                height: 40,
                backgroundColor: colors.divider,
                marginTop: spacing.small,
              }}
            />
          )}
        </Box>

        <Box sx={{ flexGrow: 1, paddingBottom: spacing.medium }}>
          <Typography variant="body2" sx={{ fontWeight: 600, marginBottom: spacing.xsmall }}>
            {event.description}
          </Typography>
          
          <Box sx={{ display: 'flex', alignItems: 'center', gap: spacing.small }}>
            <Typography variant="caption" sx={{ color: colors.text.secondary }}>
              {timelineProcessor.formatEventTime(event.timestamp)}
            </Typography>
            
            {event.user && (
              <Chip
                label={event.user}
                size="small"
                variant="outlined"
                sx={{
                  height: 20,
                  fontSize: '0.6rem',
                  '& .MuiChip-label': {
                    paddingX: spacing.xsmall,
                  },
                }}
              />
            )}
          </Box>
        </Box>
      </Box>
    );
  };

  return (
    <Box>
      <Typography variant="h6" sx={{ marginBottom: spacing.medium, fontWeight: 600 }}>
        Order History
      </Typography>

      {events.length > 0 ? (
        <Paper
          elevation={0}
          sx={{
            padding: spacing.medium,
            backgroundColor: colors.background.default,
            border: `1px solid ${colors.divider}`,
            maxHeight: 400,
            overflowY: 'auto',
          }}
        >
          {events.map((event, index) => (
            <TimelineEvent
              key={event.id}
              event={event}
              isLast={index === events.length - 1}
            />
          ))}
        </Paper>
      ) : (
        <Typography 
          variant="body2" 
          sx={{ 
            color: colors.text.secondary,
            fontStyle: 'italic',
          }}
        >
          No history available
        </Typography>
      )}
    </Box>
  );
};

export default OrderHistoryTimeline;