import type { Customer, Visit, RecognitionEvent, CameraSource, SystemHealth, PaginatedResponse } from '$lib/types';

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000';

class ApiError extends Error {
	constructor(
		public status: number,
		message: string
	) {
		super(message);
		this.name = 'ApiError';
	}
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
	const response = await fetch(`${BASE_URL}${path}`, {
		headers: { 'Content-Type': 'application/json', ...init?.headers },
		...init
	});

	if (!response.ok) {
		throw new ApiError(response.status, `API error ${response.status}: ${path}`);
	}

	return response.json() as Promise<T>;
}

export const api = {
	health: {
		get: (): Promise<{ status: string }> => request('/health'),
		dependencies: (): Promise<SystemHealth> => request('/health/dependencies')
	},

	customers: {
		list: (params?: { search?: string; status?: string; page?: number }): Promise<PaginatedResponse<Customer>> => {
			const query = new URLSearchParams();
			if (params?.search) query.set('search', params.search);
			if (params?.status) query.set('status', params.status);
			if (params?.page) query.set('page', String(params.page));
			return request(`/customers?${query}`);
		},
		get: (id: string): Promise<Customer> => request(`/customers/${id}`),
		create: (body: Omit<Customer, 'id' | 'face_count' | 'created_at' | 'updated_at'>): Promise<Customer> =>
			request('/customers', { method: 'POST', body: JSON.stringify(body) }),
		update: (id: string, body: Partial<Pick<Customer, 'name' | 'contact' | 'notes' | 'preferences' | 'status'>>): Promise<Customer> =>
			request(`/customers/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
		faces: (id: string): Promise<import('$lib/types').CustomerFace[]> => request(`/customers/${id}/faces`),
		deleteFace: (customerId: string, faceId: string): Promise<void> =>
			request(`/customers/${customerId}/faces/${faceId}`, { method: 'DELETE' }),
		visits: (id: string): Promise<PaginatedResponse<Visit>> => request(`/customers/${id}/visits`),
		recognitionEvents: (id: string): Promise<PaginatedResponse<RecognitionEvent>> =>
			request(`/customers/${id}/recognition-events`)
	},

	visits: {
		list: (params?: { customer_id?: string; date_from?: string; date_to?: string }): Promise<PaginatedResponse<Visit>> => {
			const query = new URLSearchParams();
			if (params?.customer_id) query.set('customer_id', params.customer_id);
			if (params?.date_from) query.set('date_from', params.date_from);
			if (params?.date_to) query.set('date_to', params.date_to);
			return request(`/visits?${query}`);
		},
		create: (body: { customer_id: string; source: 'manual' }): Promise<Visit> =>
			request('/visits', { method: 'POST', body: JSON.stringify(body) })
	},

	cameras: {
		list: (): Promise<CameraSource[]> => request('/camera-sources'),
		test: (id: string): Promise<{ ok: boolean }> =>
			request(`/camera-sources/${id}/test`, { method: 'POST' })
	},

	enrollment: {
		submit: (formData: FormData): Promise<{ customer_id: string; face_id: string }> =>
			fetch(`${BASE_URL}/enrollments`, { method: 'POST', body: formData }).then((r) => {
				if (!r.ok) throw new ApiError(r.status, 'Enrollment failed');
				return r.json() as Promise<{ customer_id: string; face_id: string }>;
			})
	}
};
