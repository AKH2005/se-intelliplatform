import { HttpClient } from './apiClient';
import { LoginCredentials, RegisterCredentials, TokenResponse, User } from '../types/auth';

const client = new HttpClient();

export const authApi = {
  async register(data: RegisterCredentials): Promise<TokenResponse> {
    return client.post<TokenResponse>('/auth/register', data, { timeoutMs: 60000 });
  },

  async login(data: LoginCredentials): Promise<TokenResponse> {
    return client.post<TokenResponse>('/auth/login', data, { timeoutMs: 60000 });
  },

  async getMe(): Promise<User> {
    return client.get<User>('/auth/me', { timeoutMs: 60000 });
  },

  async logout(): Promise<{ status: string; message: string }> {
    return client.post<{ status: string; message: string }>('/auth/logout');
  },
};
