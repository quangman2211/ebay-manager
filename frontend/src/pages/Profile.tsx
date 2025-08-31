import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Grid,
  Typography,
  Snackbar,
  Alert,
  Breadcrumbs,
  Link,
} from '@mui/material';
import {
  Home as HomeIcon,
  Person as PersonIcon,
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

import ProfileHeader from '../components/Profile/ProfileHeader';
import ProfileStats from '../components/Profile/ProfileStats';
import ActivityTimeline from '../components/Profile/ActivityTimeline';
import ProfileEditForm from '../components/Profile/ProfileEditForm';
import ProfilePictureUpload from '../components/Profile/ProfilePictureUpload';

import profileAPI, { ProfileData, ProfileUpdate, UserStats, UserActivity } from '../services/profileAPI';
import { useAuth } from '../context/AuthContext';

const Profile: React.FC = () => {
  const navigate = useNavigate();
  const { user } = useAuth();

  // State management
  const [profile, setProfile] = useState<ProfileData | null>(null);
  const [stats, setStats] = useState<UserStats | null>(null);
  const [activities, setActivities] = useState<UserActivity[]>([]);
  
  // Loading states
  const [profileLoading, setProfileLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);
  const [activitiesLoading, setActivitiesLoading] = useState(true);
  const [updateLoading, setUpdateLoading] = useState(false);
  const [avatarLoading, setAvatarLoading] = useState(false);

  // Dialog states
  const [editFormOpen, setEditFormOpen] = useState(false);
  const [avatarUploadOpen, setAvatarUploadOpen] = useState(false);

  // Notification states
  const [notification, setNotification] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'warning' | 'info';
  }>({
    open: false,
    message: '',
    severity: 'info',
  });

  // Load profile data
  const loadProfile = async () => {
    try {
      setProfileLoading(true);
      const profileData = await profileAPI.getProfile();
      setProfile(profileData);
    } catch (error) {
      console.error('Error loading profile:', error);
      showNotification('Failed to load profile data', 'error');
    } finally {
      setProfileLoading(false);
    }
  };

  // Load user statistics
  const loadStats = async () => {
    try {
      setStatsLoading(true);
      const statsData = await profileAPI.getUserStats();
      setStats(statsData);
    } catch (error) {
      console.error('Error loading stats:', error);
      showNotification('Failed to load statistics', 'error');
    } finally {
      setStatsLoading(false);
    }
  };

  // Load activity history
  const loadActivities = async () => {
    try {
      setActivitiesLoading(true);
      const activitiesData = await profileAPI.getActivityHistory(20);
      setActivities(activitiesData);
    } catch (error) {
      console.error('Error loading activities:', error);
      showNotification('Failed to load activity history', 'error');
    } finally {
      setActivitiesLoading(false);
    }
  };

  // Load all data
  const loadAllData = async () => {
    await Promise.all([
      loadProfile(),
      loadStats(),
      loadActivities(),
    ]);
  };

  // Show notification
  const showNotification = (message: string, severity: 'success' | 'error' | 'warning' | 'info') => {
    setNotification({ open: true, message, severity });
  };

  // Handle profile update
  const handleProfileUpdate = async (updateData: ProfileUpdate) => {
    try {
      setUpdateLoading(true);
      const updatedProfile = await profileAPI.updateProfile(updateData);
      setProfile(updatedProfile);
      showNotification('Profile updated successfully', 'success');
      
      // Reload activities to show the update action
      setTimeout(() => {
        loadActivities();
      }, 500);
    } catch (error) {
      console.error('Error updating profile:', error);
      throw new Error('Failed to update profile');
    } finally {
      setUpdateLoading(false);
    }
  };

  // Handle avatar upload
  const handleAvatarUpload = async (file: File) => {
    try {
      setAvatarLoading(true);
      const result = await profileAPI.uploadAvatar(file);
      
      // Update profile with new avatar URL
      if (profile) {
        setProfile({ ...profile, avatar_url: result.avatar_url });
      }
      
      showNotification('Profile picture updated successfully', 'success');
      
      // Reload activities to show the upload action
      setTimeout(() => {
        loadActivities();
      }, 500);
    } catch (error) {
      console.error('Error uploading avatar:', error);
      throw new Error('Failed to upload profile picture');
    } finally {
      setAvatarLoading(false);
    }
  };

  // Handle notification close
  const handleNotificationClose = () => {
    setNotification(prev => ({ ...prev, open: false }));
  };

  // Initial data load
  useEffect(() => {
    loadAllData();
  }, []);

  // If user is not authenticated, redirect
  if (!user) {
    navigate('/login');
    return null;
  }

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {/* Breadcrumbs */}
      <Box sx={{ mb: 3 }}>
        <Breadcrumbs aria-label="breadcrumb">
          <Link
            color="inherit"
            href="#"
            onClick={() => navigate('/')}
            sx={{ display: 'flex', alignItems: 'center' }}
          >
            <HomeIcon sx={{ mr: 0.5 }} fontSize="inherit" />
            Dashboard
          </Link>
          <Box sx={{ display: 'flex', alignItems: 'center', color: 'text.primary' }}>
            <PersonIcon sx={{ mr: 0.5 }} fontSize="inherit" />
            Profile
          </Box>
        </Breadcrumbs>
      </Box>

      {/* Page Header */}
      <Box sx={{ mb: 4 }}>
        <Typography
          variant="h4"
          sx={{ fontWeight: 600, mb: 1 }}
        >
          Profile
        </Typography>
        <Typography
          variant="body1"
          sx={{ color: 'text.secondary' }}
        >
          Manage your profile information, view statistics, and track your activity
        </Typography>
      </Box>

      {/* Profile Content */}
      <Grid container spacing={3}>
        {/* Left Column */}
        <Grid item xs={12} lg={8}>
          {/* Profile Header */}
          {profile && (
            <ProfileHeader
              profile={profile}
              onEditClick={() => setEditFormOpen(true)}
              onAvatarChange={() => setAvatarUploadOpen(true)}
              isLoading={profileLoading || avatarLoading}
            />
          )}

          {/* Statistics */}
          <ProfileStats
            stats={stats}
            isLoading={statsLoading}
          />
        </Grid>

        {/* Right Column */}
        <Grid item xs={12} lg={4}>
          <ActivityTimeline
            activities={activities}
            isLoading={activitiesLoading}
            onRefresh={loadActivities}
          />
        </Grid>
      </Grid>

      {/* Profile Edit Form Dialog */}
      {profile && (
        <ProfileEditForm
          open={editFormOpen}
          onClose={() => setEditFormOpen(false)}
          onSave={handleProfileUpdate}
          profile={profile}
          isLoading={updateLoading}
        />
      )}

      {/* Avatar Upload Dialog */}
      <ProfilePictureUpload
        open={avatarUploadOpen}
        onClose={() => setAvatarUploadOpen(false)}
        onUpload={handleAvatarUpload}
        currentAvatarUrl={profile?.avatar_url}
        isLoading={avatarLoading}
      />

      {/* Notification Snackbar */}
      <Snackbar
        open={notification.open}
        autoHideDuration={6000}
        onClose={handleNotificationClose}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert
          onClose={handleNotificationClose}
          severity={notification.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {notification.message}
        </Alert>
      </Snackbar>
    </Container>
  );
};

export default Profile;