import React from 'react';
import {
  Box,
  Card,
  Typography,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  Chip,
  Skeleton,
  Divider,
  Button,
} from '@mui/material';
import {
  Login as LoginIcon,
  Logout as LogoutIcon,
  Edit as EditIcon,
  PhotoCamera as PhotoCameraIcon,
  Upload as UploadIcon,
  Update as UpdateIcon,
  Add as AddIcon,
  Refresh as RefreshIcon,
} from '@mui/icons-material';
import { UserActivity } from '../../services/profileAPI';
import profileAPI from '../../services/profileAPI';

interface ActivityTimelineProps {
  activities: UserActivity[];
  isLoading: boolean;
  onRefresh: () => void;
}

const ActivityTimeline: React.FC<ActivityTimelineProps> = ({
  activities,
  isLoading,
  onRefresh,
}) => {
  const getActivityIcon = (activityType: string) => {
    const iconProps = { fontSize: 'small' as const };
    
    switch (activityType) {
      case 'login':
        return <LoginIcon {...iconProps} />;
      case 'logout':
        return <LogoutIcon {...iconProps} />;
      case 'profile_update':
        return <EditIcon {...iconProps} />;
      case 'avatar_upload':
        return <PhotoCameraIcon {...iconProps} />;
      case 'csv_upload':
        return <UploadIcon {...iconProps} />;
      case 'order_update':
        return <UpdateIcon {...iconProps} />;
      case 'account_created':
        return <AddIcon {...iconProps} />;
      default:
        return <UpdateIcon {...iconProps} />;
    }
  };

  const getActivityColor = (activityType: string) => {
    switch (activityType) {
      case 'login':
        return '#4caf50';
      case 'logout':
        return '#f44336';
      case 'profile_update':
        return '#2196f3';
      case 'avatar_upload':
        return '#ff9800';
      case 'csv_upload':
        return '#9c27b0';
      case 'order_update':
        return '#00bcd4';
      case 'account_created':
        return '#8bc34a';
      default:
        return '#757575';
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInMinutes = (now.getTime() - date.getTime()) / (1000 * 60);
    
    if (diffInMinutes < 1) {
      return 'Just now';
    } else if (diffInMinutes < 60) {
      return `${Math.floor(diffInMinutes)} minutes ago`;
    } else if (diffInMinutes < 1440) { // 24 hours
      return `${Math.floor(diffInMinutes / 60)} hours ago`;
    } else if (diffInMinutes < 10080) { // 7 days
      return `${Math.floor(diffInMinutes / 1440)} days ago`;
    } else {
      return date.toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'short',
        day: 'numeric',
      });
    }
  };

  const getActivityDetails = (activity: UserActivity) => {
    const baseDescription = profileAPI.formatActivityType(activity.activity_type);
    
    if (activity.activity_metadata) {
      // Add context from activity_metadata
      if (activity.activity_type === 'csv_upload') {
        const count = activity.activity_metadata.record_count;
        const type = activity.activity_metadata.data_type;
        return `${baseDescription} - ${count} ${type} records`;
      }
      
      if (activity.activity_type === 'order_update') {
        const orderId = activity.activity_metadata.order_id;
        const status = activity.activity_metadata.new_status;
        return `${baseDescription} #${orderId} to ${status}`;
      }
    }
    
    return activity.description || baseDescription;
  };

  const renderSkeletonList = () => (
    <List>
      {Array.from({ length: 5 }).map((_, index) => (
        <ListItem key={index} sx={{ py: 2 }}>
          <ListItemAvatar>
            <Skeleton variant="circular" width={40} height={40} />
          </ListItemAvatar>
          <ListItemText
            primary={<Skeleton variant="text" width="70%" />}
            secondary={<Skeleton variant="text" width="40%" />}
          />
        </ListItem>
      ))}
    </List>
  );

  return (
    <Card sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h6" sx={{ fontWeight: 600 }}>
          Recent Activity
        </Typography>
        <Button
          size="small"
          startIcon={<RefreshIcon />}
          onClick={onRefresh}
          disabled={isLoading}
        >
          Refresh
        </Button>
      </Box>

      {isLoading ? (
        renderSkeletonList()
      ) : activities.length === 0 ? (
        <Box
          sx={{
            textAlign: 'center',
            py: 6,
            color: 'text.secondary',
          }}
        >
          <UpdateIcon sx={{ fontSize: 48, mb: 2, opacity: 0.5 }} />
          <Typography variant="h6" sx={{ mb: 1 }}>
            No activity yet
          </Typography>
          <Typography variant="body2">
            Your recent actions will appear here
          </Typography>
        </Box>
      ) : (
        <List sx={{ p: 0 }}>
          {activities.map((activity, index) => (
            <React.Fragment key={activity.id}>
              <ListItem
                sx={{
                  px: 0,
                  py: 2,
                  position: 'relative',
                  '&:hover': {
                    backgroundColor: 'action.hover',
                  },
                  borderRadius: 1,
                }}
              >
                <ListItemAvatar>
                  <Avatar
                    sx={{
                      backgroundColor: getActivityColor(activity.activity_type),
                      width: 40,
                      height: 40,
                    }}
                  >
                    {getActivityIcon(activity.activity_type)}
                  </Avatar>
                </ListItemAvatar>
                
                <ListItemText
                  primary={
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography
                        variant="body1"
                        sx={{ fontWeight: 500, flex: 1 }}
                      >
                        {getActivityDetails(activity)}
                      </Typography>
                      <Chip
                        label={formatTimeAgo(activity.created_at)}
                        size="small"
                        variant="outlined"
                        sx={{
                          fontSize: '0.75rem',
                          height: 20,
                        }}
                      />
                    </Box>
                  }
                  secondary={
                    activity.activity_metadata && (
                      <Box sx={{ mt: 0.5 }}>
                        {Object.entries(activity.activity_metadata).map(([key, value]) => (
                          <Chip
                            key={key}
                            label={`${key}: ${value}`}
                            size="small"
                            variant="outlined"
                            sx={{
                              mr: 0.5,
                              fontSize: '0.7rem',
                              height: 18,
                              backgroundColor: 'background.paper',
                            }}
                          />
                        ))}
                      </Box>
                    )
                  }
                />
              </ListItem>
              
              {index < activities.length - 1 && (
                <Divider sx={{ mx: 0 }} />
              )}
            </React.Fragment>
          ))}
        </List>
      )}

      {activities.length > 0 && (
        <Box sx={{ textAlign: 'center', mt: 2, pt: 2, borderTop: '1px solid', borderColor: 'divider' }}>
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
            Showing {activities.length} recent activities
          </Typography>
        </Box>
      )}
    </Card>
  );
};

export default ActivityTimeline;