import React from 'react';
import {
  Box,
  Card,
  Typography,
  Grid,
  Avatar,
  Skeleton,
  LinearProgress,
} from '@mui/material';
import {
  AccountBox as AccountBoxIcon,
  Receipt as ReceiptIcon,
  Inventory as InventoryIcon,
  LoginIcon,
  Upload as UploadIcon,
  Activity as ActivityIcon,
} from '@mui/icons-material';
import { UserStats } from '../../services/profileAPI';
import profileAPI from '../../services/profileAPI';

interface ProfileStatsProps {
  stats: UserStats | null;
  isLoading: boolean;
}

interface StatCardProps {
  title: string;
  value: number;
  icon: React.ReactNode;
  color: string;
  subtitle?: string;
  isLoading: boolean;
  showProgress?: boolean;
  progressMax?: number;
}

const StatCard: React.FC<StatCardProps> = ({
  title,
  value,
  icon,
  color,
  subtitle,
  isLoading,
  showProgress = false,
  progressMax = 100,
}) => {
  if (isLoading) {
    return (
      <Card sx={{ p: 3, height: '100%' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <Skeleton variant="circular" width={48} height={48} />
          <Box sx={{ ml: 2, flex: 1 }}>
            <Skeleton variant="text" width="60%" />
            <Skeleton variant="text" width="40%" />
          </Box>
        </Box>
        <Skeleton variant="text" width="30%" height={40} />
      </Card>
    );
  }

  const progressValue = showProgress ? Math.min((value / progressMax) * 100, 100) : 0;

  return (
    <Card
      sx={{
        p: 3,
        height: '100%',
        position: 'relative',
        overflow: 'hidden',
        '&:hover': {
          transform: 'translateY(-2px)',
          boxShadow: 4,
        },
        transition: 'all 0.2s ease-in-out',
      }}
    >
      {/* Background decoration */}
      <Box
        sx={{
          position: 'absolute',
          top: -20,
          right: -20,
          width: 80,
          height: 80,
          backgroundColor: color,
          borderRadius: '50%',
          opacity: 0.1,
        }}
      />

      <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
        <Avatar
          sx={{
            backgroundColor: color,
            color: 'white',
            width: 48,
            height: 48,
          }}
        >
          {icon}
        </Avatar>
        <Box sx={{ ml: 2, flex: 1 }}>
          <Typography
            variant="body2"
            sx={{
              color: 'text.secondary',
              fontWeight: 500,
              textTransform: 'uppercase',
              letterSpacing: 0.5,
            }}
          >
            {title}
          </Typography>
          {subtitle && (
            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
              {subtitle}
            </Typography>
          )}
        </Box>
      </Box>

      <Typography
        variant="h3"
        sx={{
          fontWeight: 700,
          color: 'text.primary',
          mb: showProgress ? 1 : 0,
        }}
      >
        {profileAPI.formatStatsValue(value)}
      </Typography>

      {showProgress && (
        <Box sx={{ mt: 2 }}>
          <LinearProgress
            variant="determinate"
            value={progressValue}
            sx={{
              height: 6,
              borderRadius: 3,
              backgroundColor: 'grey.200',
              '& .MuiLinearProgress-bar': {
                backgroundColor: color,
                borderRadius: 3,
              },
            }}
          />
          <Typography
            variant="caption"
            sx={{
              color: 'text.secondary',
              mt: 0.5,
              display: 'block',
            }}
          >
            {Math.round(progressValue)}% of target
          </Typography>
        </Box>
      )}
    </Card>
  );
};

const ProfileStats: React.FC<ProfileStatsProps> = ({ stats, isLoading }) => {
  const formatLastActivity = (lastActivity?: string) => {
    if (!lastActivity) return 'No recent activity';
    
    const date = new Date(lastActivity);
    const now = new Date();
    const diffInHours = (now.getTime() - date.getTime()) / (1000 * 60 * 60);
    
    if (diffInHours < 1) {
      return 'Less than an hour ago';
    } else if (diffInHours < 24) {
      return `${Math.floor(diffInHours)} hours ago`;
    } else {
      const diffInDays = Math.floor(diffInHours / 24);
      if (diffInDays === 1) {
        return 'Yesterday';
      } else if (diffInDays < 7) {
        return `${diffInDays} days ago`;
      } else {
        return date.toLocaleDateString();
      }
    }
  };

  return (
    <Box sx={{ mb: 3 }}>
      <Typography variant="h5" sx={{ mb: 3, fontWeight: 600 }}>
        Statistics Overview
      </Typography>

      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={4}>
          <StatCard
            title="Accounts Managed"
            value={stats?.accounts_managed || 0}
            icon={<AccountBoxIcon />}
            color="#1976d2"
            subtitle="Active eBay accounts"
            isLoading={isLoading}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <StatCard
            title="Orders Processed"
            value={stats?.orders_processed || 0}
            icon={<ReceiptIcon />}
            color="#388e3c"
            subtitle="Total orders handled"
            isLoading={isLoading}
            showProgress
            progressMax={1000}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <StatCard
            title="Listings Created"
            value={stats?.listings_created || 0}
            icon={<InventoryIcon />}
            color="#f57c00"
            subtitle="Product listings"
            isLoading={isLoading}
            showProgress
            progressMax={500}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <StatCard
            title="Recent Logins"
            value={stats?.recent_logins || 0}
            icon={<LoginIcon />}
            color="#7b1fa2"
            subtitle="Last 30 days"
            isLoading={isLoading}
            showProgress
            progressMax={30}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <StatCard
            title="CSV Uploads"
            value={stats?.total_csv_uploads || 0}
            icon={<UploadIcon />}
            color="#c2185b"
            subtitle="Total files uploaded"
            isLoading={isLoading}
          />
        </Grid>

        <Grid item xs={12} sm={6} md={4}>
          <Card
            sx={{
              p: 3,
              height: '100%',
              position: 'relative',
              overflow: 'hidden',
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
              <Avatar
                sx={{
                  backgroundColor: '#00796b',
                  color: 'white',
                  width: 48,
                  height: 48,
                }}
              >
                <ActivityIcon />
              </Avatar>
              <Box sx={{ ml: 2, flex: 1 }}>
                <Typography
                  variant="body2"
                  sx={{
                    color: 'text.secondary',
                    fontWeight: 500,
                    textTransform: 'uppercase',
                    letterSpacing: 0.5,
                  }}
                >
                  Last Activity
                </Typography>
              </Box>
            </Box>

            {isLoading ? (
              <Box>
                <Skeleton variant="text" width="80%" height={32} />
                <Skeleton variant="text" width="60%" />
              </Box>
            ) : (
              <Box>
                <Typography
                  variant="body1"
                  sx={{
                    fontWeight: 600,
                    color: 'text.primary',
                    mb: 1,
                  }}
                >
                  {formatLastActivity(stats?.last_activity)}
                </Typography>
                <Typography
                  variant="body2"
                  sx={{
                    color: 'text.secondary',
                  }}
                >
                  {stats?.last_activity 
                    ? `Active user with recent engagement` 
                    : 'Get started by uploading your first CSV file'
                  }
                </Typography>
              </Box>
            )}
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ProfileStats;