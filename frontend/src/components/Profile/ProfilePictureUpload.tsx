import React, { useState, useRef, useCallback } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Box,
  Typography,
  Alert,
  IconButton,
  LinearProgress,
  Avatar,
} from '@mui/material';
import {
  Close as CloseIcon,
  Upload as UploadIcon,
  Crop as CropIcon,
  PhotoCamera as PhotoCameraIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';

interface ProfilePictureUploadProps {
  open: boolean;
  onClose: () => void;
  onUpload: (file: File) => Promise<void>;
  currentAvatarUrl?: string;
  isLoading?: boolean;
}

const ProfilePictureUpload: React.FC<ProfilePictureUploadProps> = ({
  open,
  onClose,
  onUpload,
  currentAvatarUrl,
  isLoading = false,
}) => {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string>('');
  const [error, setError] = useState<string>('');
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const resetState = () => {
    setSelectedFile(null);
    setPreviewUrl('');
    setError('');
    setDragOver(false);
  };

  const handleClose = () => {
    resetState();
    onClose();
  };

  const validateFile = (file: File): string | null => {
    // Check file type
    const validTypes = ['image/jpeg', 'image/png', 'image/gif', 'image/webp'];
    if (!validTypes.includes(file.type)) {
      return 'Please select a valid image file (JPEG, PNG, GIF, or WebP)';
    }

    // Check file size (5MB limit)
    const maxSize = 5 * 1024 * 1024;
    if (file.size > maxSize) {
      return 'File size must be less than 5MB';
    }

    return null;
  };

  const processFile = (file: File) => {
    const validationError = validateFile(file);
    if (validationError) {
      setError(validationError);
      return;
    }

    setError('');
    setSelectedFile(file);

    // Create preview URL
    const url = URL.createObjectURL(file);
    setPreviewUrl(url);

    // Clean up previous URL
    return () => URL.revokeObjectURL(url);
  };

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      processFile(file);
    }
  };

  const handleDrop = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    setDragOver(false);

    const file = event.dataTransfer.files[0];
    if (file) {
      processFile(file);
    }
  }, []);

  const handleDragOver = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    setDragOver(true);
  }, []);

  const handleDragLeave = useCallback((event: React.DragEvent) => {
    event.preventDefault();
    setDragOver(false);
  }, []);

  const handleUpload = async () => {
    if (!selectedFile) return;

    try {
      await onUpload(selectedFile);
      handleClose();
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Upload failed');
    }
  };

  const handleBrowseClick = () => {
    fileInputRef.current?.click();
  };

  const getFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  // Clean up preview URL on unmount
  React.useEffect(() => {
    return () => {
      if (previewUrl) {
        URL.revokeObjectURL(previewUrl);
      }
    };
  }, [previewUrl]);

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="sm"
      fullWidth
      PaperProps={{
        sx: { borderRadius: 2 }
      }}
    >
      <DialogTitle sx={{ pb: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6" component="div" sx={{ fontWeight: 600 }}>
            Change Profile Picture
          </Typography>
          <IconButton
            onClick={handleClose}
            size="small"
            sx={{ color: 'grey.500' }}
            disabled={isLoading}
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent sx={{ pt: 2 }}>
        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {isLoading && (
          <Box sx={{ mb: 2 }}>
            <LinearProgress />
            <Typography variant="caption" sx={{ color: 'text.secondary', mt: 1, display: 'block' }}>
              Uploading and processing image...
            </Typography>
          </Box>
        )}

        {/* Current Avatar */}
        {currentAvatarUrl && !selectedFile && (
          <Box sx={{ mb: 3, textAlign: 'center' }}>
            <Typography variant="subtitle2" sx={{ mb: 2, color: 'text.secondary' }}>
              Current Profile Picture
            </Typography>
            <Avatar
              src={currentAvatarUrl}
              sx={{ width: 120, height: 120, mx: 'auto', mb: 2 }}
            />
          </Box>
        )}

        {/* File Drop Zone */}
        <Box
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          sx={{
            border: '2px dashed',
            borderColor: dragOver ? 'primary.main' : 'grey.300',
            borderRadius: 2,
            p: 4,
            textAlign: 'center',
            backgroundColor: dragOver ? 'primary.50' : 'background.paper',
            transition: 'all 0.2s ease-in-out',
            cursor: 'pointer',
            mb: 2,
          }}
          onClick={handleBrowseClick}
        >
          {selectedFile ? (
            <Box>
              <Avatar
                src={previewUrl}
                sx={{ width: 120, height: 120, mx: 'auto', mb: 2 }}
              />
              <Typography variant="h6" sx={{ mb: 1 }}>
                {selectedFile.name}
              </Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary', mb: 1 }}>
                {getFileSize(selectedFile.size)}
              </Typography>
              <Button
                startIcon={<DeleteIcon />}
                onClick={(e) => {
                  e.stopPropagation();
                  resetState();
                }}
                size="small"
                color="error"
                disabled={isLoading}
              >
                Remove
              </Button>
            </Box>
          ) : (
            <Box>
              <PhotoCameraIcon
                sx={{
                  fontSize: 48,
                  color: 'text.secondary',
                  mb: 2,
                }}
              />
              <Typography variant="h6" sx={{ mb: 1 }}>
                {dragOver ? 'Drop your image here' : 'Choose Profile Picture'}
              </Typography>
              <Typography variant="body2" sx={{ color: 'text.secondary', mb: 2 }}>
                Drag and drop an image here, or click to browse
              </Typography>
              <Button
                variant="outlined"
                startIcon={<UploadIcon />}
                disabled={isLoading}
              >
                Browse Files
              </Button>
            </Box>
          )}
        </Box>

        <input
          ref={fileInputRef}
          type="file"
          hidden
          accept="image/*"
          onChange={handleFileSelect}
        />

        {/* Upload Guidelines */}
        <Box
          sx={{
            backgroundColor: 'grey.50',
            borderRadius: 1,
            p: 2,
            mt: 2,
          }}
        >
          <Typography variant="body2" sx={{ fontWeight: 500, mb: 1 }}>
            Image Guidelines:
          </Typography>
          <Typography variant="caption" sx={{ display: 'block', mb: 0.5 }}>
            • Supported formats: JPEG, PNG, GIF, WebP
          </Typography>
          <Typography variant="caption" sx={{ display: 'block', mb: 0.5 }}>
            • Maximum file size: 5MB
          </Typography>
          <Typography variant="caption" sx={{ display: 'block', mb: 0.5 }}>
            • Recommended dimensions: 300x300px or larger
          </Typography>
          <Typography variant="caption" sx={{ display: 'block' }}>
            • Images will be automatically resized and cropped to 300x300px
          </Typography>
        </Box>
      </DialogContent>

      <DialogActions sx={{ px: 3, py: 2 }}>
        <Button
          onClick={handleClose}
          disabled={isLoading}
          sx={{ minWidth: 80 }}
        >
          Cancel
        </Button>
        <Button
          onClick={handleUpload}
          variant="contained"
          disabled={isLoading || !selectedFile}
          startIcon={<UploadIcon />}
          sx={{ minWidth: 120 }}
        >
          {isLoading ? 'Uploading...' : 'Upload Picture'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ProfilePictureUpload;