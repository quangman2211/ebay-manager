import api from './api';

export interface ProfileData {
  id: number;
  username: string;
  email: string;
  role: string;
  is_active: boolean;
  created_at: string;
  bio?: string;
  phone?: string;
  avatar_url?: string;
  last_login?: string;
}

export interface ProfileUpdate {
  bio?: string;
  phone?: string;
}

export interface UserActivity {
  id: number;
  activity_type: string;
  description?: string;
  activity_metadata?: Record<string, any>;
  created_at: string;
}

export interface UserStats {
  accounts_managed: number;
  orders_processed: number;
  listings_created: number;
  recent_logins: number;
  total_csv_uploads: number;
  last_activity?: string;
}

class ProfileAPI {
  /**
   * Get current user's complete profile data
   */
  async getProfile(): Promise<ProfileData> {
    const response = await api.get<ProfileData>('/user/profile');
    return response.data;
  }

  /**
   * Update current user's profile information
   */
  async updateProfile(profileData: ProfileUpdate): Promise<ProfileData> {
    const response = await api.put<ProfileData>('/user/profile', profileData);
    return response.data;
  }

  /**
   * Upload profile avatar/picture
   */
  async uploadAvatar(file: File): Promise<{ message: string; avatar_url: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await api.post<{ message: string; avatar_url: string }>(
      '/user/avatar',
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );

    return response.data;
  }

  /**
   * Get user activity timeline
   */
  async getActivityHistory(limit: number = 50): Promise<UserActivity[]> {
    const response = await api.get<UserActivity[]>(`/user/activity?limit=${limit}`);
    return response.data;
  }

  /**
   * Get user statistics
   */
  async getUserStats(): Promise<UserStats> {
    const response = await api.get<UserStats>('/user/stats');
    return response.data;
  }

  /**
   * Get avatar URL with fallback
   */
  getAvatarUrl(avatarUrl?: string): string {
    if (avatarUrl) {
      // If the avatar URL is relative, prepend the API base URL
      if (avatarUrl.startsWith('/api/v1/')) {
        return `${api.defaults.baseURL?.replace('/api/v1', '')}${avatarUrl}`;
      }
      return avatarUrl;
    }
    // Return a default avatar placeholder
    return '/default-avatar.png';
  }

  /**
   * Format activity type for display
   */
  formatActivityType(activityType: string): string {
    const formatMap: Record<string, string> = {
      login: 'Logged in',
      logout: 'Logged out',
      profile_update: 'Updated profile',
      avatar_upload: 'Changed profile picture',
      csv_upload: 'Uploaded CSV file',
      order_update: 'Updated order status',
      account_created: 'Created account',
    };

    return formatMap[activityType] || activityType;
  }

  /**
   * Get activity icon for display
   */
  getActivityIcon(activityType: string): string {
    const iconMap: Record<string, string> = {
      login: '🔐',
      logout: '🚪',
      profile_update: '✏️',
      avatar_upload: '🖼️',
      csv_upload: '📄',
      order_update: '📦',
      account_created: '➕',
    };

    return iconMap[activityType] || '📝';
  }

  /**
   * Format stats for display
   */
  formatStatsValue(value: number): string {
    if (value >= 1000000) {
      return `${(value / 1000000).toFixed(1)}M`;
    } else if (value >= 1000) {
      return `${(value / 1000).toFixed(1)}K`;
    }
    return value.toString();
  }
}

const profileAPI = new ProfileAPI();
export default profileAPI;