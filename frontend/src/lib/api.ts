import axios, { AxiosInstance, AxiosResponse, AxiosRequestConfig } from 'axios';
import { Restaurant, MenuCategory, RestaurantMenuResponse } from '@/types/restaurant';
import { SessionData } from '@/types/order';

class ApiClient {
  private client: AxiosInstance;

  constructor(baseUrl: string = '') {
    this.client = axios.create({
      baseURL: baseUrl,
      timeout: 20000, // 20 second timeout (increased for audio processing)
      headers: {
        'Content-Type': 'application/json',
      },
    });

    // Add request interceptor for logging
    this.client.interceptors.request.use(
      (config) => {
        console.log(`API Request: ${config.method?.toUpperCase()} ${config.url}`);
        return config;
      },
      (error) => {
        console.error('API Request Error:', error);
        return Promise.reject(error);
      }
    );

    // Add response interceptor for error handling
    this.client.interceptors.response.use(
      (response) => response,
      (error) => {
        console.error('API Response Error:', error.response?.data || error.message);
        return Promise.reject(error);
      }
    );
  }

  private async request<T>(endpoint: string, options: AxiosRequestConfig = {}): Promise<T> {
    try {
      const response: AxiosResponse<T> = await this.client.request({
        url: endpoint,
        ...options,
      });
      return response.data;
    } catch (error: unknown) {
      if (axios.isAxiosError(error)) {
        if (error.response) {
          throw new Error(`API request failed: ${error.response.status} ${error.response.statusText}`);
        } else if (error.request) {
          throw new Error('Network error: Unable to reach the server');
        }
      }
      throw new Error(`Request error: ${error instanceof Error ? error.message : 'Unknown error'}`);
    }
  }

  // Restaurant & Menu endpoints
  async getRestaurantMenu(restaurantId: number): Promise<RestaurantMenuResponse> {
    return this.request<RestaurantMenuResponse>(`/api/restaurants/${restaurantId}/menu`);
  }

  // Session management endpoints
  async getCurrentSession(): Promise<{ success: boolean; data: { session: SessionData } }> {
    return this.request('/api/sessions/current');
  }

  async getCurrentOrder(): Promise<{ success: boolean; data: { order: any } }> {
    return this.request('/api/sessions/current-order');
  }

  async createNewSession(restaurantId: number): Promise<{ success: boolean; data: { session_id: string } }> {
    return this.request('/api/sessions/new-car', {
      method: 'POST',
      data: { restaurant_id: restaurantId },
    });
  }

  async clearCurrentSession(): Promise<{ success: boolean; message: string }> {
    return this.request('/api/sessions/next-car', {
      method: 'POST',
    });
  }

  // AI endpoints
  async processAudio(audioFile: File, sessionId: string, restaurantId: number, language: string = 'en'): Promise<{
    success: boolean;
    session_id: string;
    audio_url: string;
    response_text: string;
    order_state_changed: boolean;
    metadata: {
      processing_time: number;
      cached: boolean;
      errors: string[] | null;
    };
  }> {
    const formData = new FormData();
    formData.append('audio_file', audioFile);
    formData.append('session_id', sessionId);
    formData.append('restaurant_id', restaurantId.toString());
    formData.append('language', language);

    return this.request('/api/ai/process-audio', {
      method: 'POST',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  // Admin endpoints
  async uploadImage(file: File, restaurantId: number): Promise<{
    success: boolean;
    message: string;
    data: {
      file_id: string;
      image_url: string;
      original_name: string;
      size: number;
      content_type: string;
    };
  }> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('restaurant_id', restaurantId.toString());

    return this.request('/api/admin/upload/image', {
      method: 'POST',
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  }

  async getMenuItems(restaurantId: number, categoryId?: number, availableOnly: boolean = true): Promise<{
    id: number;
    name: string;
    description: string | null;
    price: number;
    image_url: string | null;
    category_id: number;
    restaurant_id: number;
    is_available: boolean;
    is_upsell: boolean;
    is_special: boolean;
    prep_time_minutes: number;
    display_order: number;
    created_at: string;
    updated_at: string | null;
  }[]> {
    const params = new URLSearchParams();
    params.append('restaurant_id', restaurantId.toString());
    if (categoryId) params.append('category_id', categoryId.toString());
    if (availableOnly !== undefined) params.append('available_only', availableOnly.toString());
    
    return this.request(`/api/admin/menu-items?${params}`);
  }

  async createMenuItem(menuItem: {
    name: string;
    description?: string;
    price: number;
    category_id: number;
    restaurant_id: number;
    image_url?: string;
    is_available?: boolean;
    is_upsell?: boolean;
    is_special?: boolean;
    prep_time_minutes?: number;
    display_order?: number;
  }): Promise<{
    id: number;
    name: string;
    description: string | null;
    price: number;
    image_url: string | null;
    category_id: number;
    restaurant_id: number;
    is_available: boolean;
    is_upsell: boolean;
    is_special: boolean;
    prep_time_minutes: number;
    display_order: number;
    created_at: string;
    updated_at: string | null;
  }> {
    return this.request('/api/admin/menu-items', {
      method: 'POST',
      data: menuItem,
    });
  }

  async updateMenuItem(menuItemId: number, updates: {
    name?: string;
    description?: string;
    price?: number;
    category_id?: number;
    image_url?: string;
    is_available?: boolean;
    is_upsell?: boolean;
    is_special?: boolean;
    prep_time_minutes?: number;
    display_order?: number;
  }): Promise<{
    id: number;
    name: string;
    description: string | null;
    price: number;
    image_url: string | null;
    category_id: number;
    restaurant_id: number;
    is_available: boolean;
    is_upsell: boolean;
    is_special: boolean;
    prep_time_minutes: number;
    display_order: number;
    created_at: string;
    updated_at: string | null;
  }> {
    return this.request(`/api/admin/menu-items/${menuItemId}`, {
      method: 'PUT',
      data: updates,
    });
  }

  async deleteMenuItem(menuItemId: number): Promise<{ success: boolean; message: string }> {
    return this.request(`/api/admin/menu-items/${menuItemId}`, {
      method: 'DELETE',
    });
  }

  async getIngredients(restaurantId: number, search?: string, allergenOnly?: boolean): Promise<{
    id: number;
    name: string;
    description: string | null;
    restaurant_id: number;
    is_allergen: boolean;
    allergen_type: string | null;
    unit_cost: number;
    created_at: string;
    updated_at: string | null;
  }[]> {
    const params = new URLSearchParams();
    params.append('restaurant_id', restaurantId.toString());
    if (search) params.append('search', search);
    if (allergenOnly !== undefined) params.append('allergen_only', allergenOnly.toString());
    
    return this.request(`/api/admin/ingredients?${params}`);
  }

  async createIngredient(ingredient: {
    name: string;
    description?: string;
    restaurant_id: number;
    is_allergen?: boolean;
    allergen_type?: string;
    unit_cost: number;
  }): Promise<{
    id: number;
    name: string;
    description: string | null;
    restaurant_id: number;
    is_allergen: boolean;
    allergen_type: string | null;
    unit_cost: number;
    created_at: string;
    updated_at: string | null;
  }> {
    return this.request('/api/admin/ingredients', {
      method: 'POST',
      data: ingredient,
    });
  }

  async updateIngredient(ingredientId: number, updates: {
    name?: string;
    description?: string;
    is_allergen?: boolean;
    allergen_type?: string;
    unit_cost?: number;
  }): Promise<{
    id: number;
    name: string;
    description: string | null;
    restaurant_id: number;
    is_allergen: boolean;
    allergen_type: string | null;
    unit_cost: number;
    created_at: string;
    updated_at: string | null;
  }> {
    return this.request(`/api/admin/ingredients/${ingredientId}`, {
      method: 'PUT',
      data: updates,
    });
  }

  async deleteIngredient(ingredientId: number): Promise<{ success: boolean; message: string }> {
    return this.request(`/api/admin/ingredients/${ingredientId}`, {
      method: 'DELETE',
    });
  }

  async getMenuItemIngredients(menuItemId: number): Promise<{
    id: number;
    menu_item_id: number;
    ingredient_id: number;
    quantity: number;
    unit: string;
    is_optional: boolean;
    additional_cost: number;
    ingredient: {
      id: number;
      name: string;
      description: string | null;
      restaurant_id: number;
      is_allergen: boolean;
      allergen_type: string | null;
      unit_cost: number;
      created_at: string;
      updated_at: string | null;
    };
  }[]> {
    return this.request(`/api/admin/menu-items/${menuItemId}/ingredients`);
  }

  async addIngredientToMenuItem(menuItemId: number, ingredientData: {
    ingredient_id: number;
    quantity: number;
    unit?: string;
    is_optional?: boolean;
    additional_cost?: number;
  }): Promise<{
    id: number;
    menu_item_id: number;
    ingredient_id: number;
    quantity: number;
    unit: string;
    is_optional: boolean;
    additional_cost: number;
    ingredient: {
      id: number;
      name: string;
      description: string | null;
      restaurant_id: number;
      is_allergen: boolean;
      allergen_type: string | null;
      unit_cost: number;
      created_at: string;
      updated_at: string | null;
    };
  }> {
    return this.request(`/api/admin/menu-items/${menuItemId}/ingredients`, {
      method: 'POST',
      data: ingredientData,
    });
  }

  async removeIngredientFromMenuItem(menuItemId: number, ingredientId: number): Promise<{ success: boolean; message: string }> {
    return this.request(`/api/admin/menu-items/${menuItemId}/ingredients/${ingredientId}`, {
      method: 'DELETE',
    });
  }

  // Health checks
  async checkRestaurantHealth(): Promise<{ status: string; message: string }> {
    return this.request('/api/restaurants/health');
  }

  async checkAiHealth(): Promise<{ status: string; services: Record<string, string>; message: string }> {
    return this.request('/api/ai/health');
  }

  async checkAdminHealth(): Promise<{ status: string; service: string; message: string; endpoints: Record<string, string> }> {
    return this.request('/api/admin/health');
  }

  // Category endpoints
  async getCategories(restaurantId: number): Promise<{
    id: number;
    name: string;
    description: string | null;
    restaurant_id: number;
    display_order: number;
    is_active: boolean;
    created_at: string;
  }[]> {
    return this.request(`/api/admin/categories?restaurant_id=${restaurantId}`);
  }

  async createCategory(category: {
    name: string;
    description?: string;
    restaurant_id: number;
    display_order?: number;
    is_active?: boolean;
  }): Promise<{
    id: number;
    name: string;
    description: string | null;
    restaurant_id: number;
    display_order: number;
    is_active: boolean;
    created_at: string;
  }> {
    return this.request('/api/admin/categories', {
      method: 'POST',
      data: category,
    });
  }

  async updateCategory(categoryId: number, updates: {
    name?: string;
    description?: string;
    display_order?: number;
    is_active?: boolean;
  }): Promise<{
    id: number;
    name: string;
    description: string | null;
    restaurant_id: number;
    display_order: number;
    is_active: boolean;
    created_at: string;
  }> {
    return this.request(`/api/admin/categories/${categoryId}`, {
      method: 'PUT',
      data: updates,
    });
  }

  async deleteCategory(categoryId: number): Promise<{ success: boolean; message: string }> {
    return this.request(`/api/admin/categories/${categoryId}`, {
      method: 'DELETE',
    });
  }

  // Restaurant endpoints
  async getRestaurants(): Promise<{
    id: number;
    name: string;
    description: string | null;
    address: string | null;
    phone: string | null;
    hours: string | null;
    logo_url: string | null;
    primary_color: string;
    secondary_color: string;
    is_active: boolean;
    created_at: string;
    updated_at: string | null;
  }[]> {
    return this.request('/api/admin/restaurants/');
  }

  async createRestaurant(restaurant: {
    name: string;
    description?: string;
    address?: string;
    phone?: string;
    hours?: string;
    primary_color?: string;
    secondary_color?: string;
    is_active?: boolean;
  }): Promise<{
    id: number;
    name: string;
    description: string | null;
    address: string | null;
    phone: string | null;
    hours: string | null;
    logo_url: string | null;
    primary_color: string;
    secondary_color: string;
    is_active: boolean;
    created_at: string;
    updated_at: string | null;
  }> {
    return this.request('/api/admin/restaurants/', {
      method: 'POST',
      data: restaurant,
    });
  }
}

// Create singleton instance
export const apiClient = new ApiClient(process.env.NEXT_PUBLIC_API_BASE_URL || '');

// Export types for convenience
export type { Restaurant, MenuCategory, RestaurantMenuResponse };
