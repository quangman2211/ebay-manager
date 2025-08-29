# Frontend Phase 6: Communication Center Implementation

## Overview
Implement unified Communication Center with Gmail API integration, AI-powered message classification, response templates, and comprehensive customer communication management. Includes conversation threading, priority classification, and automated response suggestions.

## SOLID/YAGNI Compliance Strategy

### Single Responsibility Principle (SRP)
- **UnifiedInbox**: Only handle message display and organization
- **MessageComposer**: Only compose and send messages
- **ConversationThread**: Only manage threaded conversation display
- **MessageClassifier**: Only categorize and prioritize messages
- **TemplateManager**: Only manage response templates and automation
- **CustomerCommunicationHistory**: Only track customer interaction timeline

### Open/Closed Principle (OCP)
- **Message Sources**: Extensible to support multiple email providers
- **Classification Rules**: Add new message categories without core changes
- **Template Engine**: Support multiple template formats through strategy pattern
- **Response Automation**: Configurable automation rules and triggers

### Liskov Substitution Principle (LSP)
- **Email Providers**: Gmail and other providers interchangeable
- **Message Filters**: All filtering strategies follow same interface
- **Template Renderers**: Different template engines substitutable

### Interface Segregation Principle (ISP)
- **Message Interfaces**: Separate read-only vs actionable message operations
- **Template Interfaces**: Different interfaces for simple vs dynamic templates
- **Communication Interfaces**: Segregate email vs message platform operations

### Dependency Inversion Principle (DIP)
- **Communication Services**: Components depend on abstract communication interfaces
- **Classification Services**: Pluggable AI and rule-based classification engines
- **Template Services**: Configurable template rendering and automation engines

## Communication Center Architecture

### Main Communication Center Layout
```typescript
// src/components/communication/CommunicationCenter.tsx - Single Responsibility: Communication interface composition
import React, { useState, useMemo } from 'react';
import { 
  Box, 
  Container, 
  Paper, 
  Tabs, 
  Tab, 
  Grid,
  Typography,
  Card,
  CardContent,
  Badge,
  Button
} from '@mui/material';
import {
  Inbox,
  Send,
  Archive,
  Label,
  PriorityHigh,
  Schedule,
  CheckCircle,
  Refresh
} from '@mui/icons-material';
import { UnifiedInbox } from './UnifiedInbox';
import { MessageComposer } from './MessageComposer';
import { TemplateManager } from './TemplateManager';
import { CommunicationAnalytics } from './CommunicationAnalytics';
import { CustomerCommunicationHistory } from './CustomerCommunicationHistory';
import { useCommunicationData } from '../../hooks/useCommunicationData';
import { useMessageClassification } from '../../hooks/useMessageClassification';

type CommunicationTab = 'inbox' | 'compose' | 'templates' | 'analytics' | 'history';

interface CommunicationStatsProps {
  unreadCount: number;
  urgentCount: number;
  pendingCount: number;
  responseTimeAvg: number;
}

const CommunicationStats: React.FC<CommunicationStatsProps> = ({
  unreadCount,
  urgentCount,
  pendingCount,
  responseTimeAvg
}) => {
  const stats = [
    {
      label: 'Unread Messages',
      value: unreadCount,
      icon: <Inbox />,
      color: 'primary' as const,
      urgent: unreadCount > 50
    },
    {
      label: 'Urgent Messages',
      value: urgentCount,
      icon: <PriorityHigh />,
      color: 'error' as const,
      urgent: urgentCount > 0
    },
    {
      label: 'Pending Response',
      value: pendingCount,
      icon: <Schedule />,
      color: 'warning' as const,
      urgent: pendingCount > 10
    },
    {
      label: 'Avg Response Time',
      value: `${responseTimeAvg}h`,
      icon: <CheckCircle />,
      color: 'success' as const,
      urgent: responseTimeAvg > 24
    }
  ];

  return (
    <Grid container spacing={2} sx={{ mb: 3 }}>
      {stats.map((stat, index) => (
        <Grid item xs={12} sm={6} md={3} key={index}>
          <Card sx={{ 
            bgcolor: stat.urgent ? `${stat.color}.light` : 'background.paper',
            border: stat.urgent ? 2 : 1,
            borderColor: stat.urgent ? `${stat.color}.main` : 'divider'
          }}>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Box>
                  <Typography variant="body2" color="text.secondary" gutterBottom>
                    {stat.label}
                  </Typography>
                  <Typography variant="h4" component="div" color={stat.urgent ? `${stat.color}.main` : 'inherit'}>
                    {stat.value}
                  </Typography>
                </Box>
                <Box sx={{ 
                  p: 1, 
                  borderRadius: 1, 
                  bgcolor: `${stat.color}.light`,
                  color: `${stat.color}.main`
                }}>
                  {stat.icon}
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );
};

export const CommunicationCenter: React.FC = () => {
  const [activeTab, setActiveTab] = useState<CommunicationTab>('inbox');
  const [selectedMessages, setSelectedMessages] = useState<string[]>([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState<string | null>(null);

  const { 
    messages, 
    conversations,
    communicationStats, 
    loading, 
    refresh: refreshCommunication 
  } = useCommunicationData();

  const {
    classifyMessage,
    getMessagePriority,
    getSuggestedResponse,
    loading: classificationLoading
  } = useMessageClassification();

  const handleTabChange = (_: React.SyntheticEvent, newValue: CommunicationTab) => {
    setActiveTab(newValue);
    setSelectedMessages([]);
  };

  const handleRefreshAll = async () => {
    await refreshCommunication();
  };

  const unreadMessages = messages.filter(msg => !msg.read);
  const urgentMessages = messages.filter(msg => msg.priority === 'urgent');
  const pendingMessages = messages.filter(msg => msg.status === 'pending_response');

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Communication Center
          </Typography>
          <Typography variant="body1" color="text.secondary">
            Manage customer communications across all channels
          </Typography>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<Refresh />}
            onClick={handleRefreshAll}
            disabled={loading}
          >
            Sync Messages
          </Button>
          <Button
            variant="contained"
            startIcon={<Send />}
            onClick={() => setActiveTab('compose')}
          >
            New Message
          </Button>
        </Box>
      </Box>

      {/* Communication Stats */}
      <CommunicationStats
        unreadCount={unreadMessages.length}
        urgentCount={urgentMessages.length}
        pendingCount={pendingMessages.length}
        responseTimeAvg={communicationStats.averageResponseTime}
      />

      {/* Tab Navigation */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={handleTabChange}>
          <Tab 
            label={
              <Badge badgeContent={unreadMessages.length} color="primary">
                Inbox
              </Badge>
            }
            value="inbox"
            icon={<Inbox />}
            iconPosition="start"
          />
          <Tab 
            label="Compose" 
            value="compose"
            icon={<Send />}
            iconPosition="start"
          />
          <Tab 
            label="Templates" 
            value="templates"
            icon={<Label />}
            iconPosition="start"
          />
          <Tab 
            label="Analytics" 
            value="analytics"
            icon={<CheckCircle />}
            iconPosition="start"
          />
          <Tab 
            label="History" 
            value="history"
            icon={<Archive />}
            iconPosition="start"
          />
        </Tabs>
      </Box>

      {/* Tab Content */}
      <Box>
        {activeTab === 'inbox' && (
          <UnifiedInbox
            messages={messages}
            conversations={conversations}
            loading={loading}
            selectedMessages={selectedMessages}
            onSelectionChange={setSelectedMessages}
            onMessageClassify={classifyMessage}
            onRefresh={refreshCommunication}
          />
        )}
        
        {activeTab === 'compose' && (
          <MessageComposer
            onSend={() => refreshCommunication()}
            getSuggestedResponse={getSuggestedResponse}
            classificationLoading={classificationLoading}
          />
        )}
        
        {activeTab === 'templates' && (
          <TemplateManager
            onRefresh={refreshCommunication}
          />
        )}
        
        {activeTab === 'analytics' && (
          <CommunicationAnalytics
            data={communicationStats}
            messages={messages}
            loading={loading}
          />
        )}
        
        {activeTab === 'history' && (
          <CustomerCommunicationHistory
            messages={messages}
            selectedCustomerId={selectedCustomerId}
            onCustomerSelect={setSelectedCustomerId}
            loading={loading}
          />
        )}
      </Box>
    </Container>
  );
};
```

### Unified Inbox Component
```typescript
// src/components/communication/UnifiedInbox.tsx - Single Responsibility: Message inbox display and management
import React, { useState, useMemo } from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  Typography,
  Box,
  Grid,
  Chip,
  IconButton,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Badge
} from '@mui/material';
import {
  Email,
  Reply,
  Forward,
  Archive,
  Delete,
  Star,
  StarBorder,
  PriorityHigh,
  Schedule,
  Search,
  FilterList,
  CheckCircle,
  Person,
  AccessTime
} from '@mui/icons-material';
import { Message, Conversation, MessageFilter } from '../../types';
import { formatDate, formatDistanceToNow } from '../../utils/formatters';

interface UnifiedInboxProps {
  messages: Message[];
  conversations: Conversation[];
  loading: boolean;
  selectedMessages: string[];
  onSelectionChange: (messageIds: string[]) => void;
  onMessageClassify: (messageId: string) => Promise<void>;
  onRefresh: () => void;
}

interface MessageItemProps {
  message: Message;
  isSelected: boolean;
  onSelect: (messageId: string, selected: boolean) => void;
  onView: (message: Message) => void;
  onReply: (message: Message) => void;
  onClassify: (messageId: string) => void;
}

const MessageItem: React.FC<MessageItemProps> = ({
  message,
  isSelected,
  onSelect,
  onView,
  onReply,
  onClassify
}) => {
  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'urgent': return 'error';
      case 'high': return 'warning';
      case 'normal': return 'info';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'pending_response': return 'warning';
      case 'responded': return 'success';
      case 'closed': return 'default';
      default: return 'info';
    }
  };

  return (
    <ListItem
      sx={{
        bgcolor: !message.read ? 'action.hover' : 'transparent',
        borderLeft: !message.read ? 4 : 0,
        borderColor: 'primary.main',
        '&:hover': { bgcolor: 'action.selected' },
        cursor: 'pointer'
      }}
      onClick={() => onView(message)}
    >
      <ListItemAvatar>
        <Badge
          badgeContent={message.attachments?.length || 0}
          color="secondary"
          invisible={!message.attachments?.length}
        >
          <Avatar sx={{ bgcolor: getPriorityColor(message.priority) + '.light' }}>
            <Email />
          </Avatar>
        </Badge>
      </ListItemAvatar>
      
      <ListItemText
        primary={
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <Typography
              variant="subtitle2"
              fontWeight={!message.read ? 'bold' : 'normal'}
              noWrap
              sx={{ flex: 1 }}
            >
              {message.senderName || message.senderEmail}
            </Typography>
            
            <Box sx={{ display: 'flex', gap: 0.5 }}>
              <Chip
                label={message.priority}
                size="small"
                color={getPriorityColor(message.priority)}
                variant={message.priority === 'urgent' ? 'filled' : 'outlined'}
              />
              <Chip
                label={message.status}
                size="small"
                color={getStatusColor(message.status)}
                variant="outlined"
              />
              {message.category && (
                <Chip
                  label={message.category}
                  size="small"
                  variant="outlined"
                />
              )}
            </Box>
          </Box>
        }
        secondary={
          <Box>
            <Typography
              variant="body2"
              color="text.secondary"
              noWrap
              sx={{ mb: 0.5 }}
            >
              {message.subject}
            </Typography>
            <Typography
              variant="body2"
              color="text.secondary"
              noWrap
              sx={{ 
                maxHeight: 32, 
                overflow: 'hidden',
                display: '-webkit-box',
                WebkitLineClamp: 2,
                WebkitBoxOrient: 'vertical'
              }}
            >
              {message.preview || message.content}
            </Typography>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
              <AccessTime fontSize="small" />
              <Typography variant="caption" color="text.secondary">
                {formatDistanceToNow(message.receivedAt)} ago
              </Typography>
              {message.customerInfo && (
                <>
                  <Person fontSize="small" />
                  <Typography variant="caption" color="text.secondary">
                    {message.customerInfo.type} customer
                  </Typography>
                </>
              )}
            </Box>
          </Box>
        }
      />
      
      <ListItemSecondaryAction>
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              onReply(message);
            }}
            color="primary"
            title="Reply"
          >
            <Reply fontSize="small" />
          </IconButton>
          
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              onClassify(message.id);
            }}
            title="Classify Message"
          >
            <CheckCircle fontSize="small" />
          </IconButton>
          
          <IconButton
            size="small"
            onClick={(e) => {
              e.stopPropagation();
              // Toggle star
            }}
            color={message.starred ? 'warning' : 'default'}
            title={message.starred ? 'Remove Star' : 'Add Star'}
          >
            {message.starred ? <Star fontSize="small" /> : <StarBorder fontSize="small" />}
          </IconButton>
        </Box>
      </ListItemSecondaryAction>
    </ListItem>
  );
};

export const UnifiedInbox: React.FC<UnifiedInboxProps> = ({
  messages,
  conversations,
  loading,
  selectedMessages,
  onSelectionChange,
  onMessageClassify,
  onRefresh
}) => {
  const [filters, setFilters] = useState<MessageFilter>({
    search: '',
    priority: 'all',
    status: 'all',
    category: 'all',
    timeRange: '7d'
  });
  
  const [selectedMessage, setSelectedMessage] = useState<Message | null>(null);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [showFilters, setShowFilters] = useState(false);

  const filteredMessages = useMemo(() => {
    return messages.filter(message => {
      if (filters.search && !message.subject.toLowerCase().includes(filters.search.toLowerCase()) 
          && !message.content.toLowerCase().includes(filters.search.toLowerCase())
          && !message.senderEmail.toLowerCase().includes(filters.search.toLowerCase())) return false;
      if (filters.priority !== 'all' && message.priority !== filters.priority) return false;
      if (filters.status !== 'all' && message.status !== filters.status) return false;
      if (filters.category !== 'all' && message.category !== filters.category) return false;
      
      // Time range filter
      const messageDate = new Date(message.receivedAt);
      const now = new Date();
      const timeDiff = now.getTime() - messageDate.getTime();
      const daysDiff = timeDiff / (1000 * 3600 * 24);
      
      switch (filters.timeRange) {
        case '1d': if (daysDiff > 1) return false; break;
        case '7d': if (daysDiff > 7) return false; break;
        case '30d': if (daysDiff > 30) return false; break;
        case '90d': if (daysDiff > 90) return false; break;
      }
      
      return true;
    });
  }, [messages, filters]);

  const sortedMessages = useMemo(() => {
    return filteredMessages.sort((a, b) => {
      // Sort by priority first (urgent first), then by received date (newest first)
      const priorityOrder = { urgent: 0, high: 1, normal: 2, low: 3 };
      const aPriority = priorityOrder[a.priority] ?? 2;
      const bPriority = priorityOrder[b.priority] ?? 2;
      
      if (aPriority !== bPriority) {
        return aPriority - bPriority;
      }
      
      return new Date(b.receivedAt).getTime() - new Date(a.receivedAt).getTime();
    });
  }, [filteredMessages]);

  const handleMessageSelect = (messageId: string, selected: boolean) => {
    if (selected) {
      onSelectionChange([...selectedMessages, messageId]);
    } else {
      onSelectionChange(selectedMessages.filter(id => id !== messageId));
    }
  };

  const handleViewMessage = (message: Message) => {
    setSelectedMessage(message);
    setViewDialogOpen(true);
    
    // Mark as read if unread
    if (!message.read) {
      // Call API to mark as read
    }
  };

  const handleReplyMessage = (message: Message) => {
    // Open compose dialog with reply context
    console.log('Reply to message:', message);
  };

  const unreadCount = sortedMessages.filter(msg => !msg.read).length;
  const urgentCount = sortedMessages.filter(msg => msg.priority === 'urgent').length;

  return (
    <Box>
      <Grid container spacing={2}>
        {/* Main Inbox */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardHeader
              title={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <Typography variant="h6">
                    Unified Inbox
                  </Typography>
                  {unreadCount > 0 && (
                    <Badge badgeContent={unreadCount} color="primary">
                      <Chip label="Unread" size="small" color="primary" />
                    </Badge>
                  )}
                  {urgentCount > 0 && (
                    <Badge badgeContent={urgentCount} color="error">
                      <Chip label="Urgent" size="small" color="error" />
                    </Badge>
                  )}
                </Box>
              }
              subheader={`${sortedMessages.length} messages (${messages.length} total)`}
              action={
                <Box sx={{ display: 'flex', gap: 1 }}>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<FilterList />}
                    onClick={() => setShowFilters(!showFilters)}
                  >
                    Filters
                  </Button>
                  <Button variant="outlined" size="small" onClick={onRefresh}>
                    Refresh
                  </Button>
                </Box>
              }
            />
            
            {/* Filters */}
            {showFilters && (
              <CardContent sx={{ pt: 0, pb: 1 }}>
                <Grid container spacing={2}>
                  <Grid item xs={12} md={3}>
                    <TextField
                      fullWidth
                      label="Search"
                      placeholder="Subject, content, or sender"
                      value={filters.search}
                      onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                      InputProps={{
                        startAdornment: <Search sx={{ mr: 1, color: 'text.secondary' }} />
                      }}
                      size="small"
                    />
                  </Grid>
                  
                  <Grid item xs={12} md={2}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Priority</InputLabel>
                      <Select
                        value={filters.priority}
                        label="Priority"
                        onChange={(e) => setFilters({ ...filters, priority: e.target.value })}
                      >
                        <MenuItem value="all">All Priorities</MenuItem>
                        <MenuItem value="urgent">Urgent</MenuItem>
                        <MenuItem value="high">High</MenuItem>
                        <MenuItem value="normal">Normal</MenuItem>
                        <MenuItem value="low">Low</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  
                  <Grid item xs={12} md={2}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Status</InputLabel>
                      <Select
                        value={filters.status}
                        label="Status"
                        onChange={(e) => setFilters({ ...filters, status: e.target.value })}
                      >
                        <MenuItem value="all">All Status</MenuItem>
                        <MenuItem value="pending_response">Pending Response</MenuItem>
                        <MenuItem value="responded">Responded</MenuItem>
                        <MenuItem value="closed">Closed</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  
                  <Grid item xs={12} md={2}>
                    <FormControl fullWidth size="small">
                      <InputLabel>Time Range</InputLabel>
                      <Select
                        value={filters.timeRange}
                        label="Time Range"
                        onChange={(e) => setFilters({ ...filters, timeRange: e.target.value })}
                      >
                        <MenuItem value="1d">Last 24 hours</MenuItem>
                        <MenuItem value="7d">Last 7 days</MenuItem>
                        <MenuItem value="30d">Last 30 days</MenuItem>
                        <MenuItem value="90d">Last 90 days</MenuItem>
                        <MenuItem value="all">All time</MenuItem>
                      </Select>
                    </FormControl>
                  </Grid>
                  
                  <Grid item xs={12} md={3}>
                    <Button
                      variant="outlined"
                      onClick={() => setFilters({
                        search: '',
                        priority: 'all',
                        status: 'all',
                        category: 'all',
                        timeRange: '7d'
                      })}
                      fullWidth
                    >
                      Clear Filters
                    </Button>
                  </Grid>
                </Grid>
              </CardContent>
            )}

            <CardContent sx={{ pt: 0, px: 0 }}>
              <List>
                {sortedMessages.map((message, index) => (
                  <React.Fragment key={message.id}>
                    <MessageItem
                      message={message}
                      isSelected={selectedMessages.includes(message.id)}
                      onSelect={handleMessageSelect}
                      onView={handleViewMessage}
                      onReply={handleReplyMessage}
                      onClassify={onMessageClassify}
                    />
                    {index < sortedMessages.length - 1 && <Divider />}
                  </React.Fragment>
                ))}
              </List>
              
              {sortedMessages.length === 0 && !loading && (
                <Box sx={{ textAlign: 'center', py: 4 }}>
                  <Typography variant="h6" color="text.secondary" gutterBottom>
                    No messages found
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Try adjusting your filters or refresh to check for new messages
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Conversation Panel */}
        <Grid item xs={12} lg={4}>
          <Card>
            <CardHeader
              title="Recent Conversations"
              subheader={`${conversations.length} active threads`}
            />
            <CardContent sx={{ px: 0 }}>
              <List>
                {conversations.slice(0, 10).map((conversation, index) => (
                  <React.Fragment key={conversation.id}>
                    <ListItem button onClick={() => {
                      // View full conversation
                    }}>
                      <ListItemAvatar>
                        <Avatar>
                          {conversation.customerName?.charAt(0) || <Person />}
                        </Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={conversation.customerName || conversation.customerEmail}
                        secondary={
                          <Box>
                            <Typography variant="body2" noWrap>
                              {conversation.subject}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {conversation.messageCount} messages • {formatDistanceToNow(conversation.lastMessageAt)} ago
                            </Typography>
                          </Box>
                        }
                      />
                      <Badge
                        badgeContent={conversation.unreadCount}
                        color="primary"
                        invisible={conversation.unreadCount === 0}
                      />
                    </ListItem>
                    {index < Math.min(conversations.length - 1, 9) && <Divider />}
                  </React.Fragment>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* View Message Dialog */}
      <Dialog
        open={viewDialogOpen}
        onClose={() => setViewDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        {selectedMessage && (
          <>
            <DialogTitle>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                <Typography variant="h6">
                  {selectedMessage.subject}
                </Typography>
                <Box sx={{ display: 'flex', gap: 0.5 }}>
                  <Chip
                    label={selectedMessage.priority}
                    size="small"
                    color={selectedMessage.priority === 'urgent' ? 'error' : 'default'}
                  />
                  <Chip
                    label={selectedMessage.category || 'Uncategorized'}
                    size="small"
                    variant="outlined"
                  />
                </Box>
              </Box>
            </DialogTitle>
            <DialogContent>
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" color="text.secondary">
                  <strong>From:</strong> {selectedMessage.senderName} &lt;{selectedMessage.senderEmail}&gt;
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  <strong>Received:</strong> {formatDate(selectedMessage.receivedAt)}
                </Typography>
                {selectedMessage.customerInfo && (
                  <Typography variant="body2" color="text.secondary">
                    <strong>Customer:</strong> {selectedMessage.customerInfo.type} • {selectedMessage.customerInfo.orderCount} orders
                  </Typography>
                )}
              </Box>
              
              <Divider sx={{ my: 2 }} />
              
              <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                {selectedMessage.content}
              </Typography>
              
              {selectedMessage.attachments && selectedMessage.attachments.length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Attachments ({selectedMessage.attachments.length})
                  </Typography>
                  {selectedMessage.attachments.map((attachment, index) => (
                    <Chip
                      key={index}
                      label={attachment.filename}
                      variant="outlined"
                      size="small"
                      sx={{ mr: 1, mb: 1 }}
                    />
                  ))}
                </Box>
              )}
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setViewDialogOpen(false)}>
                Close
              </Button>
              <Button 
                variant="outlined"
                onClick={() => handleReplyMessage(selectedMessage)}
              >
                Reply
              </Button>
              <Button 
                variant="contained"
                onClick={() => onMessageClassify(selectedMessage.id)}
              >
                Auto-Classify
              </Button>
            </DialogActions>
          </>
        )}
      </Dialog>
    </Box>
  );
};
```

### Message Composer Component
```typescript
// src/components/communication/MessageComposer.tsx - Single Responsibility: Message composition and sending
import React, { useState, useEffect } from 'react';
import {
  Card,
  CardHeader,
  CardContent,
  TextField,
  Button,
  Box,
  Grid,
  Typography,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Autocomplete,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  IconButton,
  Paper,
  Divider
} from '@mui/material';
import {
  Send,
  AttachFile,
  Save,
  Delete,
  Template,
  SmartToy,
  Close,
  Preview
} from '@mui/icons-material';
import { Customer, MessageTemplate, ResponseSuggestion } from '../../types';

interface MessageComposerProps {
  onSend: (message: any) => Promise<void>;
  getSuggestedResponse: (context: string) => Promise<ResponseSuggestion[]>;
  classificationLoading: boolean;
  replyToMessage?: any;
  selectedCustomer?: Customer;
}

interface ComposedMessage {
  to: string;
  cc?: string;
  bcc?: string;
  subject: string;
  content: string;
  priority: 'urgent' | 'high' | 'normal' | 'low';
  category: string;
  templateId?: string;
  attachments: File[];
}

export const MessageComposer: React.FC<MessageComposerProps> = ({
  onSend,
  getSuggestedResponse,
  classificationLoading,
  replyToMessage,
  selectedCustomer
}) => {
  const [message, setMessage] = useState<ComposedMessage>({
    to: selectedCustomer?.email || replyToMessage?.senderEmail || '',
    subject: replyToMessage ? `Re: ${replyToMessage.subject}` : '',
    content: '',
    priority: 'normal',
    category: '',
    attachments: []
  });

  const [templates, setTemplates] = useState<MessageTemplate[]>([]);
  const [suggestions, setSuggestions] = useState<ResponseSuggestion[]>([]);
  const [showTemplates, setShowTemplates] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [sending, setSending] = useState(false);

  useEffect(() => {
    // Load templates
    loadMessageTemplates();
    
    // If replying, get AI suggestions
    if (replyToMessage) {
      loadResponseSuggestions();
    }
  }, [replyToMessage]);

  const loadMessageTemplates = async () => {
    // Load from API
    const mockTemplates: MessageTemplate[] = [
      {
        id: '1',
        name: 'Order Confirmation',
        category: 'orders',
        subject: 'Your order has been confirmed - Order #{{orderNumber}}',
        content: `Dear {{customerName}},

Thank you for your order! We're excited to let you know that your order #{{orderNumber}} has been confirmed and is being processed.

Order Details:
- Items: {{itemsList}}
- Total: {{orderTotal}}
- Estimated Delivery: {{deliveryDate}}

We'll send you another update when your order ships.

Best regards,
{{senderName}}`,
        variables: ['customerName', 'orderNumber', 'itemsList', 'orderTotal', 'deliveryDate', 'senderName']
      },
      {
        id: '2',
        name: 'Shipping Notification',
        category: 'shipping',
        subject: 'Your order is on the way! - Order #{{orderNumber}}',
        content: `Dear {{customerName}},

Great news! Your order #{{orderNumber}} has been shipped.

Tracking Information:
- Carrier: {{carrier}}
- Tracking Number: {{trackingNumber}}
- Estimated Delivery: {{estimatedDelivery}}

You can track your package at: {{trackingUrl}}

Thank you for your business!

Best regards,
{{senderName}}`
      }
    ];
    setTemplates(mockTemplates);
  };

  const loadResponseSuggestions = async () => {
    if (!replyToMessage) return;
    
    try {
      const context = `Original message: ${replyToMessage.content}`;
      const responseSuggestions = await getSuggestedResponse(context);
      setSuggestions(responseSuggestions);
    } catch (error) {
      console.error('Failed to get response suggestions:', error);
    }
  };

  const handleTemplateSelect = (template: MessageTemplate) => {
    setMessage(prev => ({
      ...prev,
      subject: template.subject,
      content: template.content,
      category: template.category,
      templateId: template.id
    }));
    setShowTemplates(false);
  };

  const handleSuggestionSelect = (suggestion: ResponseSuggestion) => {
    setMessage(prev => ({
      ...prev,
      content: suggestion.content,
      category: suggestion.category || prev.category
    }));
    setShowSuggestions(false);
  };

  const handleAttachFile = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (files) {
      setMessage(prev => ({
        ...prev,
        attachments: [...prev.attachments, ...Array.from(files)]
      }));
    }
  };

  const handleRemoveAttachment = (index: number) => {
    setMessage(prev => ({
      ...prev,
      attachments: prev.attachments.filter((_, i) => i !== index)
    }));
  };

  const handleSend = async () => {
    if (!message.to || !message.subject || !message.content) {
      alert('Please fill in all required fields');
      return;
    }

    setSending(true);
    try {
      await onSend({
        ...message,
        replyToId: replyToMessage?.id
      });
      
      // Reset form
      setMessage({
        to: '',
        subject: '',
        content: '',
        priority: 'normal',
        category: '',
        attachments: []
      });
      
      alert('Message sent successfully!');
    } catch (error) {
      console.error('Failed to send message:', error);
      alert('Failed to send message. Please try again.');
    } finally {
      setSending(false);
    }
  };

  const renderPreview = () => (
    <Box sx={{ p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
      <Typography variant="subtitle2" gutterBottom>
        <strong>To:</strong> {message.to}
      </Typography>
      {message.cc && (
        <Typography variant="subtitle2" gutterBottom>
          <strong>CC:</strong> {message.cc}
        </Typography>
      )}
      <Typography variant="subtitle2" gutterBottom>
        <strong>Subject:</strong> {message.subject}
      </Typography>
      <Divider sx={{ my: 1 }} />
      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
        {message.content}
      </Typography>
      {message.attachments.length > 0 && (
        <Box sx={{ mt: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Attachments:
          </Typography>
          {message.attachments.map((file, index) => (
            <Chip key={index} label={file.name} size="small" sx={{ mr: 1 }} />
          ))}
        </Box>
      )}
    </Box>
  );

  return (
    <Box>
      <Card>
        <CardHeader
          title={replyToMessage ? 'Reply to Message' : 'Compose New Message'}
          subheader={replyToMessage ? `Replying to: ${replyToMessage.subject}` : 'Send a new message to customer'}
          action={
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                startIcon={<Template />}
                onClick={() => setShowTemplates(true)}
              >
                Templates
              </Button>
              {replyToMessage && (
                <Button
                  variant="outlined"
                  startIcon={<SmartToy />}
                  onClick={() => setShowSuggestions(true)}
                  disabled={classificationLoading}
                >
                  AI Suggest
                </Button>
              )}
              <Button
                variant="outlined"
                startIcon={<Preview />}
                onClick={() => setPreviewOpen(true)}
              >
                Preview
              </Button>
            </Box>
          }
        />
        
        <CardContent>
          <Grid container spacing={3}>
            {/* Recipients */}
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="To"
                required
                value={message.to}
                onChange={(e) => setMessage(prev => ({ ...prev, to: e.target.value }))}
                placeholder="customer@example.com"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="CC"
                value={message.cc || ''}
                onChange={(e) => setMessage(prev => ({ ...prev, cc: e.target.value }))}
                placeholder="cc@example.com"
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="BCC"
                value={message.bcc || ''}
                onChange={(e) => setMessage(prev => ({ ...prev, bcc: e.target.value }))}
                placeholder="bcc@example.com"
              />
            </Grid>

            {/* Subject and Priority */}
            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                label="Subject"
                required
                value={message.subject}
                onChange={(e) => setMessage(prev => ({ ...prev, subject: e.target.value }))}
                placeholder="Enter message subject"
              />
            </Grid>
            
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Priority</InputLabel>
                <Select
                  value={message.priority}
                  label="Priority"
                  onChange={(e) => setMessage(prev => ({ ...prev, priority: e.target.value as any }))}
                >
                  <MenuItem value="urgent">Urgent</MenuItem>
                  <MenuItem value="high">High</MenuItem>
                  <MenuItem value="normal">Normal</MenuItem>
                  <MenuItem value="low">Low</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  value={message.category}
                  label="Category"
                  onChange={(e) => setMessage(prev => ({ ...prev, category: e.target.value }))}
                >
                  <MenuItem value="">None</MenuItem>
                  <MenuItem value="orders">Orders</MenuItem>
                  <MenuItem value="shipping">Shipping</MenuItem>
                  <MenuItem value="returns">Returns</MenuItem>
                  <MenuItem value="support">Support</MenuItem>
                </Select>
              </FormControl>
            </Grid>

            {/* Message Content */}
            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={12}
                label="Message"
                required
                value={message.content}
                onChange={(e) => setMessage(prev => ({ ...prev, content: e.target.value }))}
                placeholder="Type your message here..."
              />
            </Grid>

            {/* Attachments */}
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 2 }}>
                <Button
                  variant="outlined"
                  component="label"
                  startIcon={<AttachFile />}
                >
                  Attach Files
                  <input
                    type="file"
                    hidden
                    multiple
                    onChange={handleAttachFile}
                  />
                </Button>
                
                <Typography variant="body2" color="text.secondary">
                  {message.attachments.length} file(s) attached
                </Typography>
              </Box>
              
              {message.attachments.length > 0 && (
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1 }}>
                  {message.attachments.map((file, index) => (
                    <Chip
                      key={index}
                      label={file.name}
                      onDelete={() => handleRemoveAttachment(index)}
                      color="primary"
                      variant="outlined"
                    />
                  ))}
                </Box>
              )}
            </Grid>

            {/* Actions */}
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button variant="outlined" startIcon={<Save />}>
                  Save Draft
                </Button>
                <Button
                  variant="contained"
                  startIcon={<Send />}
                  onClick={handleSend}
                  disabled={sending || !message.to || !message.subject || !message.content}
                >
                  {sending ? 'Sending...' : 'Send Message'}
                </Button>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Templates Dialog */}
      <Dialog
        open={showTemplates}
        onClose={() => setShowTemplates(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Message Templates
        </DialogTitle>
        <DialogContent>
          <List>
            {templates.map((template) => (
              <ListItem
                key={template.id}
                button
                onClick={() => handleTemplateSelect(template)}
              >
                <ListItemText
                  primary={template.name}
                  secondary={
                    <Box>
                      <Typography variant="body2">{template.subject}</Typography>
                      <Chip label={template.category} size="small" sx={{ mt: 0.5 }} />
                    </Box>
                  }
                />
              </ListItem>
            ))}
          </List>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowTemplates(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>

      {/* AI Suggestions Dialog */}
      <Dialog
        open={showSuggestions}
        onClose={() => setShowSuggestions(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          AI Response Suggestions
        </DialogTitle>
        <DialogContent>
          {suggestions.length > 0 ? (
            <List>
              {suggestions.map((suggestion, index) => (
                <ListItem
                  key={index}
                  button
                  onClick={() => handleSuggestionSelect(suggestion)}
                >
                  <ListItemText
                    primary={`Suggestion ${index + 1}`}
                    secondary={
                      <Box>
                        <Typography variant="body2" sx={{ mb: 1 }}>
                          {suggestion.content.substring(0, 200)}...
                        </Typography>
                        <Chip
                          label={`${(suggestion.confidence * 100).toFixed(0)}% confidence`}
                          size="small"
                          color={suggestion.confidence > 0.8 ? 'success' : 'warning'}
                        />
                      </Box>
                    }
                  />
                </ListItem>
              ))}
            </List>
          ) : (
            <Typography>No suggestions available</Typography>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSuggestions(false)}>Cancel</Button>
        </DialogActions>
      </Dialog>

      {/* Preview Dialog */}
      <Dialog
        open={previewOpen}
        onClose={() => setPreviewOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Message Preview
        </DialogTitle>
        <DialogContent>
          {renderPreview()}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPreviewOpen(false)}>Close</Button>
          <Button
            variant="contained"
            onClick={() => {
              setPreviewOpen(false);
              handleSend();
            }}
            disabled={sending || !message.to || !message.subject || !message.content}
          >
            Send Message
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};
```

## Implementation Tasks

### Task 1: Communication Center Foundation
1. **Create Communication Center Layout**
   - Implement unified communication interface with tabbed navigation
   - Add communication stats dashboard with real-time metrics
   - Set up responsive layout for inbox management

2. **Build Gmail API Integration**
   - Implement OAuth2 authentication for Gmail
   - Create email fetching and synchronization service
   - Add real-time email monitoring and notifications

3. **Test Communication Foundation**
   - Gmail API authentication and token management
   - Email synchronization accuracy and performance
   - Real-time notification system functionality

### Task 2: Unified Inbox Implementation
1. **Create Unified Inbox Interface**
   - Implement message list with priority and status indicators
   - Add advanced filtering and search functionality
   - Create conversation threading and grouping

2. **Build Message Classification System**
   - Implement AI-powered message categorization
   - Add priority detection and urgency classification
   - Create customer type identification

3. **Test Inbox Features**
   - Message filtering and search accuracy
   - Classification algorithm performance
   - Conversation threading correctness

### Task 3: Message Composition
1. **Implement Message Composer**
   - Create comprehensive email composition interface
   - Add template system with variable substitution
   - Implement attachment handling and file management

2. **Build AI Response Suggestions**
   - Create response suggestion engine
   - Add context-aware reply generation
   - Implement confidence scoring for suggestions

3. **Test Composition Features**
   - Template rendering accuracy
   - AI suggestion quality and relevance
   - Attachment handling and file validation

### Task 4: Advanced Communication Features
1. **Template Management System**
   - Create template library with categorization
   - Add dynamic template variables and rendering
   - Implement template sharing and versioning

2. **Communication Analytics**
   - Build response time tracking and metrics
   - Add communication volume and trend analysis
   - Create customer satisfaction indicators

3. **Test Advanced Features**
   - Template system functionality and performance
   - Analytics accuracy and calculation correctness
   - Cross-module data integration

### Task 5: Integration & Optimization
1. **Customer Communication History**
   - Link messages to customer profiles and orders
   - Create comprehensive communication timeline
   - Add interaction pattern analysis

2. **Performance Optimization**
   - Implement message caching and pagination
   - Add background sync and offline capabilities
   - Optimize large conversation handling

3. **Test Integration**
   - Customer data linking accuracy
   - Performance with high message volumes
   - Data consistency across communication channels

## Quality Gates

### Performance Requirements
- [ ] Inbox loading: <1 second for 1000 messages
- [ ] Message composition: Real-time auto-save
- [ ] AI suggestions: <3 seconds generation time
- [ ] Gmail sync: <30 seconds for new messages
- [ ] Memory usage: <150MB for full message dataset

### Functionality Requirements
- [ ] Gmail API integration works reliably
- [ ] Message classification accuracy >85%
- [ ] Template rendering works correctly
- [ ] Conversation threading is accurate
- [ ] Customer communication history is complete

### SOLID Compliance Checklist
- [ ] Each component has single responsibility
- [ ] Email provider system is extensible
- [ ] Message sources are interchangeable
- [ ] Communication interfaces are properly segregated
- [ ] All services depend on abstractions

---
**Next Phase**: CSV Import Wizard with intelligent data mapping and validation.