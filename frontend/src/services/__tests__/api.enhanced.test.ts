import axios from 'axios';
import { csvAPI } from '../api';

// Mock axios
jest.mock('axios');
const mockedAxios = axios as jest.Mocked<typeof axios>;

// Mock axios create
const mockAxiosInstance = {
  post: jest.fn(),
  get: jest.fn(),
  interceptors: {
    request: { use: jest.fn() },
    response: { use: jest.fn() }
  }
};

mockedAxios.create.mockReturnValue(mockAxiosInstance as any);

describe('Enhanced CSV API', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  describe('uploadCSVEnhanced', () => {
    it('should upload CSV with enhanced progress tracking', async () => {
      const mockFile = new File(['test content'], 'test.csv', { type: 'text/csv' });
      const mockResponse = {
        success: true,
        upload_id: 'test-upload-id',
        message: 'Upload started',
        inserted_count: 10,
        duplicate_count: 2,
        total_records: 12,
        detected_username: 'test_user'
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      const result = await csvAPI.uploadCSVEnhanced(mockFile, 1, 'order');

      expect(mockAxiosInstance.post).toHaveBeenCalledWith(
        '/csv/upload-enhanced',
        expect.any(FormData),
        expect.objectContaining({
          headers: {
            'Content-Type': 'multipart/form-data'
          },
          timeout: 600000
        })
      );

      expect(result).toEqual(mockResponse);
    });

    it('should handle enhanced upload error response', async () => {
      const mockFile = new File(['test content'], 'test.csv', { type: 'text/csv' });
      const mockErrorResponse = {
        success: false,
        message: 'Upload failed',
        error: {
          code: 'FILE_TOO_LARGE',
          message: 'File size exceeds limit',
          suggestions: ['Reduce file size', 'Split into chunks']
        }
      };

      mockAxiosInstance.post.mockResolvedValue({ data: mockErrorResponse });

      const result = await csvAPI.uploadCSVEnhanced(mockFile, 1, 'order');

      expect(result.success).toBe(false);
      expect(result.error?.code).toBe('FILE_TOO_LARGE');
      expect(result.error?.suggestions).toHaveLength(2);
    });

    it('should include correct form data for enhanced upload', async () => {
      const mockFile = new File(['test content'], 'test.csv', { type: 'text/csv' });
      const mockResponse = { success: true, upload_id: 'test-id' };

      mockAxiosInstance.post.mockResolvedValue({ data: mockResponse });

      await csvAPI.uploadCSVEnhanced(mockFile, 123, 'listing');

      const formDataCall = mockAxiosInstance.post.mock.calls[0];
      const formData = formDataCall[1] as FormData;

      // Verify FormData contents
      expect(formData.get('file')).toBe(mockFile);
      expect(formData.get('account_id')).toBe('123');
      expect(formData.get('data_type')).toBe('listing');
    });
  });

  describe('getUploadProgress', () => {
    it('should fetch upload progress successfully', async () => {
      const mockProgressResponse = {
        success: true,
        upload_id: 'test-upload-id',
        filename: 'test.csv',
        state: 'processing',
        message: 'Processing records...',
        progress_percent: 75,
        started_at: '2025-01-01T00:00:00Z'
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockProgressResponse });

      const result = await csvAPI.getUploadProgress('test-upload-id');

      expect(mockAxiosInstance.get).toHaveBeenCalledWith(
        '/upload/progress/test-upload-id',
        expect.objectContaining({
          timeout: 120000
        })
      );

      expect(result).toEqual(mockProgressResponse);
    });

    it('should handle progress not found', async () => {
      const mockNotFoundResponse = {
        success: false,
        error: 'Upload not found'
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockNotFoundResponse });

      const result = await csvAPI.getUploadProgress('nonexistent-id');

      expect(result.success).toBe(false);
      expect(result.error).toBe('Upload not found');
    });

    it('should handle network error for progress request', async () => {
      mockAxiosInstance.get.mockRejectedValue(new Error('Network error'));

      await expect(csvAPI.getUploadProgress('test-id')).rejects.toThrow('Network error');
    });

    it('should fetch progress for completed upload', async () => {
      const mockCompletedResponse = {
        success: true,
        upload_id: 'completed-id',
        filename: 'completed.csv',
        state: 'completed',
        message: 'Upload completed successfully',
        progress_percent: 100,
        started_at: '2025-01-01T00:00:00Z'
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockCompletedResponse });

      const result = await csvAPI.getUploadProgress('completed-id');

      expect(result.state).toBe('completed');
      expect(result.progress_percent).toBe(100);
    });

    it('should fetch progress for failed upload', async () => {
      const mockFailedResponse = {
        success: true,
        upload_id: 'failed-id',
        filename: 'failed.csv',
        state: 'failed',
        message: 'Upload failed due to invalid format',
        progress_percent: 50,
        started_at: '2025-01-01T00:00:00Z'
      };

      mockAxiosInstance.get.mockResolvedValue({ data: mockFailedResponse });

      const result = await csvAPI.getUploadProgress('failed-id');

      expect(result.state).toBe('failed');
      expect(result.message).toContain('failed');
    });
  });

  describe('Error Handling', () => {
    it('should handle axios request error in uploadCSVEnhanced', async () => {
      const mockFile = new File(['test content'], 'test.csv', { type: 'text/csv' });
      mockAxiosInstance.post.mockRejectedValue(new Error('Request failed'));

      await expect(csvAPI.uploadCSVEnhanced(mockFile, 1, 'order')).rejects.toThrow('Request failed');
    });

    it('should handle timeout in uploadCSVEnhanced', async () => {
      const mockFile = new File(['test content'], 'test.csv', { type: 'text/csv' });
      const timeoutError = new Error('Timeout');
      timeoutError.name = 'ECONNABORTED';
      
      mockAxiosInstance.post.mockRejectedValue(timeoutError);

      await expect(csvAPI.uploadCSVEnhanced(mockFile, 1, 'order')).rejects.toThrow('Timeout');
    });

    it('should handle server error response in uploadCSVEnhanced', async () => {
      const mockFile = new File(['test content'], 'test.csv', { type: 'text/csv' });
      const serverError = {
        response: {
          status: 500,
          data: { detail: 'Internal server error' }
        }
      };

      mockAxiosInstance.post.mockRejectedValue(serverError);

      await expect(csvAPI.uploadCSVEnhanced(mockFile, 1, 'order')).rejects.toEqual(serverError);
    });
  });

  describe('Type Safety', () => {
    it('should handle optional fields in upload response', async () => {
      const mockFile = new File(['test'], 'test.csv');
      const minimalResponse = {
        success: true,
        message: 'Upload started'
        // Optional fields omitted
      };

      mockAxiosInstance.post.mockResolvedValue({ data: minimalResponse });

      const result = await csvAPI.uploadCSVEnhanced(mockFile, 1, 'order');

      expect(result.success).toBe(true);
      expect(result.upload_id).toBeUndefined();
      expect(result.inserted_count).toBeUndefined();
    });

    it('should handle optional fields in progress response', async () => {
      const minimalProgressResponse = {
        success: true
        // Optional fields omitted
      };

      mockAxiosInstance.get.mockResolvedValue({ data: minimalProgressResponse });

      const result = await csvAPI.getUploadProgress('test-id');

      expect(result.success).toBe(true);
      expect(result.upload_id).toBeUndefined();
      expect(result.state).toBeUndefined();
    });
  });

  describe('Integration with existing API patterns', () => {
    it('should use same timeout pattern as existing CSV upload', async () => {
      const mockFile = new File(['test'], 'test.csv');
      mockAxiosInstance.post.mockResolvedValue({ data: { success: true } });

      await csvAPI.uploadCSVEnhanced(mockFile, 1, 'order');

      const callConfig = mockAxiosInstance.post.mock.calls[0][2];
      expect(callConfig.timeout).toBe(600000); // Same as existing CSV upload
    });

    it('should use correct content type for file upload', async () => {
      const mockFile = new File(['test'], 'test.csv');
      mockAxiosInstance.post.mockResolvedValue({ data: { success: true } });

      await csvAPI.uploadCSVEnhanced(mockFile, 1, 'order');

      const callConfig = mockAxiosInstance.post.mock.calls[0][2];
      expect(callConfig.headers['Content-Type']).toBe('multipart/form-data');
    });

    it('should use correct timeout for progress requests', async () => {
      mockAxiosInstance.get.mockResolvedValue({ data: { success: true } });

      await csvAPI.getUploadProgress('test-id');

      const callConfig = mockAxiosInstance.get.mock.calls[0][1];
      expect(callConfig.timeout).toBe(120000); // 2 minutes default timeout
    });
  });
});