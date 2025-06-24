const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

class ApiClient {
  constructor() {
    this.baseURL = API_BASE_URL;
  }

  async request(endpoint, options = {}) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ 
          detail: `HTTP ${response.status}: ${response.statusText}` 
        }));
        throw new Error(error.detail || 'Request failed');
      }

      return response.json();
    } catch (error) {
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error('Unable to connect to server. Please check if the backend is running.');
      }
      throw error;
    }
  }

  async requestWithAuth(endpoint, token, options = {}) {
    return this.request(endpoint, {
      ...options,
      headers: {
        ...options.headers,
        Authorization: `Bearer ${token}`,
      },
    });
  }

  async requestFormData(endpoint, formData, token = null) {
    const url = `${this.baseURL}${endpoint}`;
    const config = {
      method: 'POST',
      body: formData,
    };

    if (token) {
      config.headers = {
        Authorization: `Bearer ${token}`,
      };
    }

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const error = await response.json().catch(() => ({ 
          detail: `HTTP ${response.status}: ${response.statusText}` 
        }));
        throw new Error(error.detail || 'Request failed');
      }

      return response.json();
    } catch (error) {
      if (error.name === 'TypeError' && error.message.includes('fetch')) {
        throw new Error('Unable to connect to server. Please check if the backend is running.');
      }
      throw error;
    }
  }

  // Auth endpoints
  async login(email, password) {
    return this.request('/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
  }

  async register(email, password, full_name) {
    return this.request('/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, full_name }),
    });
  }

  // Image upload
  async uploadImage(file, token) {
    const formData = new FormData();
    formData.append('file', file);
    return this.requestFormData('/upload-image', formData, token);
  }

  // User data
  async storeUserData(userData, token) {
    return this.requestWithAuth('/user-data', token, {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  // Plan generation
  async generatePlan(planRequest, token) {
    return this.requestWithAuth('/generate-plan', token, {
      method: 'POST',
      body: JSON.stringify(planRequest),
    });
  }

  // Get user plans
  async getUserPlans(token) {
    return this.requestWithAuth('/plans', token);
  }

  // Health check
  async healthCheck() {
    return this.request('/health');
  }

  // NEW: Dashboard and progress tracking endpoints
  async getDashboard(token) {
    return this.requestWithAuth('/dashboard', token);
  }

  async logProgress(progressData, token) {
    return this.requestWithAuth('/progress', token, {
      method: 'POST',
      body: JSON.stringify(progressData),
    });
  }

  async logWorkout(workoutData, token) {
    return this.requestWithAuth('/workout-log', token, {
      method: 'POST',
      body: JSON.stringify(workoutData),
    });
  }

  async logWeight(weightData, token) {
    return this.requestWithAuth('/weight', token, {
      method: 'POST',
      body: JSON.stringify(weightData),
    });
  }

  async logMeasurements(measurementData, token) {
    return this.requestWithAuth('/measurements', token, {
      method: 'POST',
      body: JSON.stringify(measurementData),
    });
  }

  async getProgressHistory(days = 30, token) {
    return this.requestWithAuth(`/progress-history?days=${days}`, token);
  }

  async getWeightHistory(days = 90, token) {
    return this.requestWithAuth(`/weight-history?days=${days}`, token);
  }

  async getWorkoutHistory(days = 30, token) {
    return this.requestWithAuth(`/workout-history?days=${days}`, token);
  }
}

export default new ApiClient();