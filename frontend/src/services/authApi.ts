import { HttpClient } from './apiClient';
import { LoginCredentials, RegisterCredentials, TokenResponse, User } from '../types/auth';

const client = new HttpClient();

export const authApi = {
  async register(data: RegisterCredentials): Promise<TokenResponse> {
    return client.post<TokenResponse>('/auth/register', data);
  },

  async login(data: LoginCredentials): Promise<TokenResponse> {
    return client.post<TokenResponse>('/auth/login', data);
  },

  async getMe(): Promise<User> {
    return client.get<User>('/auth/me');
  },

  async logout(): Promise<{ status: string; message: string }> {
    return client.post<{ status: string; message: string }>('/auth/logout');
  },
};
