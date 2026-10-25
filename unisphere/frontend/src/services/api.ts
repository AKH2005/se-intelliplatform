const API_BASE_URL = 'http://localhost:8002/api';

export class ApiError extends Error {
  status: number;
  data: any;

  constructor(status: number, message: string, data?: any) {
    super(message);
    this.status = status;
    this.data = data;
    this.name = 'ApiError';
  }
}

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const token = localStorage.getItem('unisphere_token');

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> || {}),
  };

  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const url = `${API_BASE_URL}${endpoint}`;
  const response = await fetch(url, {
    ...options,
    headers,
  });

  if (response.status === 204) {
    return {} as T;
  }

  const data = await response.json().catch(() => null);

  if (!response.ok) {
    const detail = data?.detail || `HTTP Error ${response.status}`;
    const message = typeof detail === 'string' ? detail : JSON.stringify(detail);
    throw new ApiError(response.status, message, data);
  }

  return data as T;
}

export const api = {
  // Authentication
  auth: {
    login: (credentials: { email: string; password: string }) =>
      request<{ access_token: string; token_type: string; user: any }>('/auth/login', {
        method: 'POST',
        body: JSON.stringify(credentials),
      }),
    register: (payload: any) =>
      request<{ access_token: string; token_type: string; user: any }>('/auth/register', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    me: () => request<any>('/auth/me'),
    forgotPassword: (email: string) =>
      request<{ message: string; reset_token?: string }>('/auth/forgot-password', {
        method: 'POST',
        body: JSON.stringify({ email }),
      }),
    resetPassword: (payload: { reset_token: string; new_password: string }) =>
      request<{ status: string; message: string }>('/auth/reset-password', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    changePassword: (payload: { current_password: string; new_password: string }) =>
      request<{ status: string; message: string }>('/auth/change-password', {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    updateProfile: (payload: any) =>
      request<any>('/auth/profile', {
        method: 'PUT',
        body: JSON.stringify(payload),
      }),
  },

  // Courses
  courses: {
    list: (params?: { search?: string; department_id?: number; semester?: string; faculty_id?: number }) => {
      const q = new URLSearchParams();
      if (params?.search) q.append('search', params.search);
      if (params?.department_id) q.append('department_id', String(params.department_id));
      if (params?.semester) q.append('semester', params.semester);
      if (params?.faculty_id) q.append('faculty_id', String(params.faculty_id));
      const qs = q.toString() ? `?${q.toString()}` : '';
      return request<any[]>(`/courses${qs}`);
    },
    get: (id: number) => request<any>(`/courses/${id}`),
    create: (payload: any) =>
      request<any>('/courses', { method: 'POST', body: JSON.stringify(payload) }),
    update: (id: number, payload: any) =>
      request<any>(`/courses/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
    delete: (id: number) =>
      request<void>(`/courses/${id}`, { method: 'DELETE' }),
    enroll: (courseId: number, studentId?: number) =>
      request<{ status: string; message: string }>(`/courses/${courseId}/enroll`, {
        method: 'POST',
        body: JSON.stringify({ student_id: studentId }),
      }),
    drop: (courseId: number, studentId: number) =>
      request<void>(`/courses/${courseId}/enroll/${studentId}`, { method: 'DELETE' }),
  },

  // Students
  students: {
    list: (params?: { search?: string; department_id?: number; year?: number; sort_by?: string; order?: string }) => {
      const q = new URLSearchParams();
      if (params?.search) q.append('search', params.search);
      if (params?.department_id) q.append('department_id', String(params.department_id));
      if (params?.year) q.append('year', String(params.year));
      if (params?.sort_by) q.append('sort_by', params.sort_by);
      if (params?.order) q.append('order', params.order);
      const qs = q.toString() ? `?${q.toString()}` : '';
      return request<any[]>(`/students${qs}`);
    },
    get: (id: number) => request<any>(`/students/${id}`),
    create: (payload: any) =>
      request<any>('/students', { method: 'POST', body: JSON.stringify(payload) }),
    update: (id: number, payload: any) =>
      request<any>(`/students/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
    delete: (id: number) =>
      request<void>(`/students/${id}`, { method: 'DELETE' }),
  },

  // Faculty
  faculty: {
    list: (params?: { search?: string; department_id?: number; designation?: string }) => {
      const q = new URLSearchParams();
      if (params?.search) q.append('search', params.search);
      if (params?.department_id) q.append('department_id', String(params.department_id));
      if (params?.designation) q.append('designation', params.designation);
      const qs = q.toString() ? `?${q.toString()}` : '';
      return request<any[]>(`/faculty${qs}`);
    },
    get: (id: number) => request<any>(`/faculty/${id}`),
    create: (payload: any) =>
      request<any>('/faculty', { method: 'POST', body: JSON.stringify(payload) }),
    update: (id: number, payload: any) =>
      request<any>(`/faculty/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
    delete: (id: number) =>
      request<void>(`/faculty/${id}`, { method: 'DELETE' }),
  },

  // Departments
  departments: {
    list: () => request<any[]>('/departments'),
    get: (id: number) => request<any>(`/departments/${id}`),
    create: (payload: any) =>
      request<any>('/departments', { method: 'POST', body: JSON.stringify(payload) }),
  },

  // Attendance
  attendance: {
    getCourseSheet: (courseId: number, dateVal?: string) => {
      const qs = dateVal ? `?date_val=${dateVal}` : '';
      return request<any>(`/attendance/course/${courseId}${qs}`);
    },
    saveBatch: (payload: { course_id: number; date: string; records: any[] }) =>
      request<any>('/attendance/batch', { method: 'POST', body: JSON.stringify(payload) }),
    getStudentSummary: (studentId: number, courseId?: number) => {
      const qs = courseId ? `?course_id=${courseId}` : '';
      return request<any>(`/attendance/student/${studentId}${qs}`);
    },
  },

  // Assignments
  assignments: {
    list: (courseId?: number) => {
      const qs = courseId ? `?course_id=${courseId}` : '';
      return request<any[]>(`/assignments${qs}`);
    },
    get: (id: number) => request<any>(`/assignments/${id}`),
    create: (payload: any) =>
      request<any>('/assignments', { method: 'POST', body: JSON.stringify(payload) }),
    submit: (assignmentId: number, payload: { content: string; file_name?: string }) =>
      request<any>(`/assignments/${assignmentId}/submit`, {
        method: 'POST',
        body: JSON.stringify(payload),
      }),
    grade: (submissionId: number, payload: { marks_obtained: number; feedback?: string }) =>
      request<any>(`/assignments/submissions/${submissionId}/grade`, {
        method: 'PUT',
        body: JSON.stringify(payload),
      }),
  },

  // Examinations
  examinations: {
    list: (params?: { course_id?: number; upcoming_only?: boolean }) => {
      const q = new URLSearchParams();
      if (params?.course_id) q.append('course_id', String(params.course_id));
      if (params?.upcoming_only) q.append('upcoming_only', 'true');
      const qs = q.toString() ? `?${q.toString()}` : '';
      return request<any[]>(`/examinations${qs}`);
    },
    get: (id: number) => request<any>(`/examinations/${id}`),
    create: (payload: any) =>
      request<any>('/examinations', { method: 'POST', body: JSON.stringify(payload) }),
    enterBatchMarks: (examId: number, results: any[]) =>
      request<any>(`/examinations/${examId}/results/batch`, {
        method: 'POST',
        body: JSON.stringify({ examination_id: examId, results }),
      }),
    getStudentResults: (studentId: number) =>
      request<any[]>(`/examinations/results/student/${studentId}`),
  },

  // Announcements
  announcements: {
    list: (params?: { search?: string; category?: string }) => {
      const q = new URLSearchParams();
      if (params?.search) q.append('search', params.search);
      if (params?.category) q.append('category', params.category);
      const qs = q.toString() ? `?${q.toString()}` : '';
      return request<any[]>(`/announcements${qs}`);
    },
    get: (id: number) => request<any>(`/announcements/${id}`),
    create: (payload: any) =>
      request<any>('/announcements', { method: 'POST', body: JSON.stringify(payload) }),
    update: (id: number, payload: any) =>
      request<any>(`/announcements/${id}`, { method: 'PUT', body: JSON.stringify(payload) }),
    delete: (id: number) =>
      request<void>(`/announcements/${id}`, { method: 'DELETE' }),
  },

  // Dashboards
  dashboard: {
    student: () => request<any>('/dashboard/student'),
    faculty: () => request<any>('/dashboard/faculty'),
    admin: () => request<any>('/dashboard/admin'),
  },

  // Contact
  contact: {
    submit: (payload: { name: string; email: string; subject: string; message: string }) =>
      request<any>('/contact', { method: 'POST', body: JSON.stringify(payload) }),
  },
};
