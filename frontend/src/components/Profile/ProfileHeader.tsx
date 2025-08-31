import React, { useState } from 'react';
import {
  Box,
  Card,
  Avatar,
  Typography,
  Button,
  Chip,
  IconButton,
  Badge,
  Tooltip,
} from '@mui/material';
import {
  Edit as EditIcon,
  PhotoCamera as PhotoCameraIcon,
  VerifiedUser as VerifiedUserIcon,
} from '@mui/icons-material';
import { ProfileData } from '../../services/profileAPI';

interface ProfileHeaderProps {
  profile: ProfileData;
  onEditClick: () => void;
  onAvatarChange: (file: File) => void;
  isLoading?: boolean;
}

const ProfileHeader: React.FC<ProfileHeaderProps> = ({
  profile,
  onEditClick,
  onAvatarChange,
  isLoading = false,
}) => {
  const [avatarError, setAvatarError] = useState(false);

  const handleAvatarUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      // Validate file type and size
      const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
      const maxSize = 5 * 1024 * 1024; // 5MB

      if (!validTypes.includes(file.type)) {
        alert('Please select a valid image file (JPEG, PNG, or GIF)');
        return;
      }

      if (file.size > maxSize) {
        alert('File size must be less than 5MB');
        return;
      }

      onAvatarChange(file);
    }
  };

  const getRoleColor = (role: string) => {
    switch (role.toLowerCase()) {
      case 'admin':
        return '#d32f2f';
      case 'staff':
        return '#1976d2';
      default:
        return '#757575';
    }
  };

  const getRoleIcon = (role: string) => {
    switch (role.toLowerCase()) {
      case 'admin':
        return <VerifiedUserIcon sx={{ fontSize: 16 }} />;
      default:
        return null;
    }
  };

  const formatJoinDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
    });
  };

  const getInitials = (username: string, email: string) => {
    if (username) {
      return username.substring(0, 2).toUpperCase();
    }
    if (email) {
      return email.substring(0, 2).toUpperCase();
    }
    return 'U';
  };

  return (
    <Card sx={{ p: 3, mb: 3 }}>
      <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 3 }}>
        {/* Avatar Section */}
        <Box sx={{ position: 'relative' }}>
          <Badge
            overlap="circular"
            anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            badgeContent={
              <Tooltip title="Change profile picture">
                <IconButton
                  size="small"
                  component="label"
                  sx={{
                    backgroundColor: 'primary.main',
                    color: 'white',
                    width: 32,
                    height: 32,
                    '&:hover': {
                      backgroundColor: 'primary.dark',
                    },
                  }}
                  disabled={isLoading}
                >
                  <PhotoCameraIcon sx={{ fontSize: 16 }} />
                  <input
                    type="file"
                    hidden
                    accept="image/*"
                    onChange={handleAvatarUpload}
                  />
                </IconButton>
              </Tooltip>
            }
          >
            <Avatar
              sx={{
                width: 120,
                height: 120,
                fontSize: '2rem',
                fontWeight: 'bold',
                border: '4px solid',
                borderColor: 'background.paper',
                boxShadow: 2,
              }}
              src={!avatarError && profile.avatar_url ? profile.avatar_url : undefined}
              onError={() => setAvatarError(true)}
            >
              {getInitials(profile.username, profile.email)}
            </Avatar>
          </Badge>
        </Box>

        {/* Profile Information */}
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2, mb: 2 }}>
            <Box sx={{ flex: 1 }}>
              <Typography
                variant="h4"
                sx={{
                  fontWeight: 600,
                  mb: 1,
                  color: 'text.primary',
                }}
              >
                {profile.username}
              </Typography>
              <Typography
                variant="body1"
                sx={{
                  color: 'text.secondary',
                  mb: 2,
                }}
              >
                {profile.email}
              </Typography>

              {/* Role and Status */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1.5, mb: 2 }}>
                <Chip
                  label={profile.role.charAt(0).toUpperCase() + profile.role.slice(1)}
                  icon={getRoleIcon(profile.role)}
                  sx={{
                    backgroundColor: getRoleColor(profile.role),
                    color: 'white',
                    fontWeight: 600,
                    '& .MuiChip-icon': {
                      color: 'white',
                    },
                  }}
                />
                <Chip
                  label={profile.is_active ? 'Active' : 'Inactive'}
                  color={profile.is_active ? 'success' : 'default'}
                  variant="outlined"
                  size="small"
                />
              </Box>

              {/* Bio */}
              {profile.bio && (
                <Typography
                  variant="body2"
                  sx={{
                    color: 'text.secondary',
                    mb: 2,
                    lineHeight: 1.6,
                  }}
                >
                  {profile.bio}
                </Typography>
              )}

              {/* Join Date and Contact */}
              <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 3 }}>
                <Box>
                  <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block' }}>
                    Member since
                  </Typography>
                  <Typography variant="body2" sx={{ fontWeight: 500 }}>
                    {formatJoinDate(profile.created_at)}
                  </Typography>
                </Box>
                {profile.phone && (
                  <Box>
                    <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block' }}>
                      Phone
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {profile.phone}
                    </Typography>
                  </Box>
                )}
                {profile.last_login && (
                  <Box>
                    <Typography variant="caption" sx={{ color: 'text.secondary', display: 'block' }}>
                      Last login
                    </Typography>
                    <Typography variant="body2" sx={{ fontWeight: 500 }}>
                      {new Date(profile.last_login).toLocaleDateString()}
                    </Typography>
                  </Box>
                )}
              </Box>
            </Box>

            {/* Edit Button */}
            <Button
              variant="outlined"
              startIcon={<EditIcon />}
              onClick={onEditClick}
              disabled={isLoading}
              sx={{
                flexShrink: 0,
              }}
            >
              Edit Profile
            </Button>
          </Box>
        </Box>
      </Box>
    </Card>
  );
};

export default ProfileHeader;