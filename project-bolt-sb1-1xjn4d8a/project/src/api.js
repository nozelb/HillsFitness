// src/api.js - Updated API Client for Specification Compliance
import { API_ENDPOINTS, APP_CONFIG, ERROR_CODES } from './utils/constants';

class EnhancedApiClient {
  constructor() {
    this.baseURL = APP_CONFIG.API_BASE_URL;
    this.timeout = APP_CONFIG.API_TIMEOUT;
    this.imageTimeout = APP_CONFIG.IMAGE_UPLOAD_TIMEOUT;
    this.retryAttempts = APP_CONFIG.RETRY_ATTEMPTS;
  }

  // Enhanced request method with retry logic
  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      timeout: options.timeout || this.timeout,
      ...options,
    };

    for (let attempt = 1; attempt <= this.retryAttempts; attempt++) {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), config.timeout);

        const response = await fetch(url, {
          ...config,
          signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({}));
          throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
        }

        return await response.json();
      } catch (error) {
        if (attempt === this.retryAttempts || error.name === 'AbortError') {
          if (error.name === 'AbortError') {
            throw new Error('Request timeout - please check your connection');
          }
          throw error;
        }
        // Wait before retry (exponential backoff)
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
      }
    }
  }

  // Form data request for file uploads
  async requestFormData(endpoint, formData, token, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      method: 'POST',
      body: formData,
      headers: {
        'Authorization': `Bearer ${token}`,
        ...options.headers,
      },
      timeout: options.timeout || this.imageTimeout,
      ...options,
    };

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), config.timeout);

    try {
      const response = await fetch(url, {
        ...config,
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}: ${response.statusText}`);
      }

      return await response.json();
    } catch (error) {
      if (error.name === 'AbortError') {
        throw new Error('Upload timeout - please try a smaller image');
      }
      throw error;
    }
  }

  // Authenticated request helper
  async requestWithAuth(endpoint, token, options = {}) {
    return this.request(endpoint, {
      ...options,
      headers: {
        'Authorization': `Bearer ${token}`,
        ...options.headers,
      },
    });
  }

  // AUTHENTICATION ENDPOINTS
  async login(email, password) {
    return this.request(API_ENDPOINTS.LOGIN, {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async register(email, password, full_name) {
    return this.request(API_ENDPOINTS.REGISTER, {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name }),
    });
  }

  // PROFILE MANAGEMENT (STATIC - persisted once)
  async createProfile(profileData, token) {
    return this.requestWithAuth(API_ENDPOINTS.CREATE_PROFILE, token, {
      method: 'POST',
      body: JSON.stringify(profileData),
    });
  }

  async updateProfile(profileData, token) {
    return this.requestWithAuth(API_ENDPOINTS.UPDATE_PROFILE, token, {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });
  }

  async getProfile(token) {
    return this.requestWithAuth(API_ENDPOINTS.PROFILE, token);
  }

  // PLAN GENERATION WORKFLOW (DYNAMIC - each time)
  async submitWizardData(wizardData, token) {
    return this.requestWithAuth(API_ENDPOINTS.WIZARD_DATA, token, {
      method: 'POST',
      body: JSON.stringify(wizardData),
    });
  }

  async uploadAndAnalyzeImage(file, token) {
    const formData = new FormData();
    formData.append('file', file);
    return this.requestFormData(API_ENDPOINTS.UPLOAD_ANALYZE_IMAGE, formData, token);
  }

  async generatePlan(token) {
    return this.requestWithAuth(API_ENDPOINTS.GENERATE_PLAN, token, {
      method: 'POST',
    });
  }

  // PLAN MANAGEMENT
  async acceptPlan(planId, token) {
    return this.requestWithAuth(`${API_ENDPOINTS.ACCEPT_PLAN}/${planId}`, token, {
      method: 'POST',
    });
  }

  async regeneratePlan(planId, userComment, token) {
    return this.requestWithAuth(API_ENDPOINTS.REGENERATE_PLAN, token, {
      method: 'POST',
      body: JSON.stringify({
        plan_id: planId,
        user_comment: userComment,
        preserve_difficulty: true,
        preserve_muscle_emphasis: true
      }),
    });
  }

  async getUserPlans(token) {
    return this.requestWithAuth(API_ENDPOINTS.PLANS, token);
  }

  // PROGRESS TRACKING AND COMPLIANCE
  async logWorkoutSession(sessionData, token) {
    return this.requestWithAuth(API_ENDPOINTS.LOG_SESSION, token, {
      method: 'POST',
      body: JSON.stringify(sessionData),
    });
  }

  async getDashboard(token) {
    return this.requestWithAuth(API_ENDPOINTS.DASHBOARD, token);
  }

  async getProgressCharts(token, timeframe = 'last_90_days') {
    return this.requestWithAuth(`${API_ENDPOINTS.PROGRESS_CHARTS}?timeframe=${timeframe}`, token);
  }

  // LEGACY ENDPOINTS (backward compatibility)
  async uploadImage(file, token) {
    console.warn('uploadImage is deprecated, use uploadAndAnalyzeImage instead');
    return this.uploadAndAnalyzeImage(file, token);
  }

  async storeUserData(userData, token) {
    console.warn('storeUserData is deprecated, use submitWizardData instead');
    return this.requestWithAuth(API_ENDPOINTS.USER_DATA, token, {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  // MEASUREMENT TRACKING
  async logMeasurements(measurementData, token) {
    return this.requestWithAuth(API_ENDPOINTS.MEASUREMENTS, token, {
      method: 'POST',
      body: JSON.stringify({
        ...measurementData,
        timestamp: new Date().toISOString(),
      }),
    });
  }

  async getMeasurements(token, days = 90) {
    return this.requestWithAuth(`${API_ENDPOINTS.MEASUREMENTS}?days=${days}`, token);
  }

  // SMART SCALE INTEGRATION
  async syncSmartScaleData(scaleData, token) {
    return this.requestWithAuth('/api/smart-scale-sync', token, {
      method: 'POST',
      body: JSON.stringify({
        body_fat_pct: scaleData.bodyFatPct,
        muscle_pct: scaleData.musclePct,
        visceral_fat_score: scaleData.visceralFatScore,
        weight_kg: scaleData.weightKg,
        timestamp: scaleData.timestamp || new Date().toISOString(),
      }),
    });
  }

  // NOTIFICATIONS AND COMPLIANCE
  async getNotifications(token) {
    return this.requestWithAuth(API_ENDPOINTS.NOTIFICATIONS, token);
  }

  async markNotificationRead(notificationId, token) {
    return this.requestWithAuth(`${API_ENDPOINTS.NOTIFICATIONS}/${notificationId}/read`, token, {
      method: 'PATCH',
    });
  }

  async getComplianceStatus(token) {
    return this.requestWithAuth('/api/compliance-status', token);
  }

  // HEALTH AND SYSTEM STATUS
  async healthCheck() {
    return this.request('/api/health');
  }

  async getSystemStatus() {
    return this.request('/api/status');
  }

  // VISION ANALYSIS UTILITIES
  async getVisionMetrics(token) {
    return this.requestWithAuth('/api/vision-metrics', token);
  }

  async reprocessImage(imageId, token) {
    return this.requestWithAuth(`/api/reprocess-image/${imageId}`, token, {
      method: 'POST',
    });
  }

  // PDF GENERATION
  async downloadPlanPDF(planId, token) {
    const response = await fetch(`${this.baseURL}/api/plans/${planId}/pdf`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to generate PDF');
    }

    return response.blob();
  }

  // PLAN COMPARISON AND ANALYTICS
  async comparePlans(planIds, token) {
    return this.requestWithAuth('/api/compare-plans', token, {
      method: 'POST',
      body: JSON.stringify({ plan_ids: planIds }),
    });
  }

  async getPlanAnalytics(planId, token) {
    return this.requestWithAuth(`/api/plans/${planId}/analytics`, token);
  }

  // EXERCISE DATABASE
  async searchExercises(query, filters = {}) {
    const params = new URLSearchParams({
      q: query,
      ...filters,
    });
    return this.request(`/api/exercises/search?${params}`);
  }

  async getExerciseDetails(exerciseId) {
    return this.request(`/api/exercises/${exerciseId}`);
  }

  // NUTRITION DATABASE
  async searchFoods(query, filters = {}) {
    const params = new URLSearchParams({
      q: query,
      ...filters,
    });
    return this.request(`/api/nutrition/search?${params}`);
  }

  async getFoodNutrition(foodId) {
    return this.request(`/api/nutrition/${foodId}`);
  }

  // PROGRESS INSIGHTS
  async getProgressInsights(token, timeframe = '30d') {
    return this.requestWithAuth(`/api/insights?timeframe=${timeframe}`, token);
  }

  async getPersonalRecords(token) {
    return this.requestWithAuth('/api/personal-records', token);
  }

  // SOCIAL FEATURES (if implemented)
  async shareProgress(progressData, token) {
    return this.requestWithAuth('/api/share-progress', token, {
      method: 'POST',
      body: JSON.stringify(progressData),
    });
  }

  async getLeaderboard(category, token) {
    return this.requestWithAuth(`/api/leaderboard/${category}`, token);
  }

  // ERROR HANDLING UTILITIES
  parseError(error) {
    if (typeof error.detail === 'object' && error.detail.errors) {
      // Validation errors
      return {
        type: 'validation',
        errors: error.detail.errors,
        message: 'Please check your input and try again',
      };
    }

    if (error.detail && typeof error.detail === 'object' && error.detail.error) {
      // Vision analysis errors
      return {
        type: 'vision_analysis',
        code: error.detail.error,
        message: this.getVisionErrorMessage(error.detail.error),
        quality_score: error.detail.quality_score,
      };
    }

    return {
      type: 'general',
      message: error.message || 'An unexpected error occurred',
    };
  }

  getVisionErrorMessage(errorCode) {
    const messages = {
      [ERROR_CODES.LOW_QUALITY_IMAGE]: 'Image quality is too low. Please upload a clearer photo with better lighting.',
      [ERROR_CODES.POSE_DETECTION_FAILED]: 'Could not detect your pose in the image. Please ensure your full body is visible.',
      [ERROR_CODES.PROCESSING_FAILED]: 'Image processing failed. Please try uploading a different image.',
      [ERROR_CODES.INVALID_RANGE]: 'Some measurements are outside the valid range. Please check your inputs.',
    };

    return messages[errorCode] || 'Image analysis failed. Please try again.';
  }

  // BATCH OPERATIONS
  async batchLogSessions(sessionsData, token) {
    return this.requestWithAuth('/api/sessions/batch', token, {
      method: 'POST',
      body: JSON.stringify({ sessions: sessionsData }),
    });
  }

  async batchUpdateMeasurements(measurementsData, token) {
    return this.requestWithAuth('/api/measurements/batch', token, {
      method: 'POST',
      body: JSON.stringify({ measurements: measurementsData }),
    });
  }

  // EXPORT/IMPORT DATA
  async exportUserData(token, format = 'json') {
    const response = await fetch(`${this.baseURL}/api/export?format=${format}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });

    if (!response.ok) {
      throw new Error('Failed to export data');
    }

    return format === 'json' ? response.json() : response.blob();
  }

  async importUserData(file, token) {
    const formData = new FormData();
    formData.append('file', file);
    return this.requestFormData('/api/import', formData, token);
  }

  // SUBSCRIPTION AND BILLING (if applicable)
  async getSubscriptionStatus(token) {
    return this.requestWithAuth('/api/subscription', token);
  }

  async updatePaymentMethod(paymentData, token) {
    return this.requestWithAuth('/api/payment-method', token, {
      method: 'PUT',
      body: JSON.stringify(paymentData),
    });
  }

  // ADMIN ENDPOINTS (if user has admin role)
  async getSystemMetrics(token) {
    return this.requestWithAuth('/api/admin/metrics', token);
  }

  async getUsersList(token, page = 1, limit = 50) {
    return this.requestWithAuth(`/api/admin/users?page=${page}&limit=${limit}`, token);
  }

  // WEBHOOK HANDLING (for integrations)
  async registerWebhook(webhookData, token) {
    return this.requestWithAuth('/api/webhooks', token, {
      method: 'POST',
      body: JSON.stringify(webhookData),
    });
  }

  async testWebhook(webhookId, token) {
    return this.requestWithAuth(`/api/webhooks/${webhookId}/test`, token, {
      method: 'POST',
    });
  }
}

// Create singleton instance
const apiClient = new EnhancedApiClient();

// Export both the class and the instance
export { EnhancedApiClient };
export default apiClient;

// Additional utility functions for common API patterns
export const withErrorHandling = (apiCall) => {
  return async (...args) => {
    try {
      return await apiCall(...args);
    } catch (error) {
      const parsedError = apiClient.parseError(error);
      console.error('API Error:', parsedError);
      throw parsedError;
    }
  };
};

export const withRetry = (apiCall, maxRetries = 3) => {
  return async (...args) => {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await apiCall(...args);
      } catch (error) {
        if (attempt === maxRetries) throw error;
        await new Promise(resolve => setTimeout(resolve, Math.pow(2, attempt) * 1000));
      }
    }
  };
};

export const withCache = (apiCall, cacheTime = 5 * 60 * 1000) => {
  const cache = new Map();
  
  return async (...args) => {
    const key = JSON.stringify(args);
    const cached = cache.get(key);
    
    if (cached && Date.now() - cached.timestamp < cacheTime) {
      return cached.data;
    }
    
    const data = await apiCall(...args);
    cache.set(key, { data, timestamp: Date.now() });
    
    return data;
  };
};