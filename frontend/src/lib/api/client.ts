import type { Customer, Visit, RecognitionEvent, CameraSource, SystemHealth, PaginatedResponse, CustomerFace } from '$lib/types';

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
        update: (id: string, body: Partial<Pick<Customer, 'name' | 'contact' | 'notes' | 'preferences'>>): Promise<Customer> =>
            request(`/customers/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
        faces: (id: string): Promise<CustomerFace[]> => request(`/customers/${id}/faces`),
        deleteFace: (customerId: string, faceId: string): Promise<void> =>
            request(`/customers/${customerId}/faces/${faceId}`, { method: 'DELETE' }),
        visits: (id: string, params?: { page?: number }): Promise<PaginatedResponse<Visit>> => {
            const query = new URLSearchParams();
            if (params?.page) query.set('page', String(params.page));
            return request(`/customers/${id}/visits?${query}`);
        },
    },

    visits: {
    list: (params?: { customer_id?: string; date_from?: string; date_to?: string; page?: number }): Promise<PaginatedResponse<Visit>> => {
        const query = new URLSearchParams();
        if (params?.customer_id) query.set('customer_id', params.customer_id);
        if (params?.date_from) query.set('date_from', params.date_from);
        if (params?.date_to) query.set('date_to', params.date_to);
        if (params?.page) query.set('page', String(params.page));
        return request(`/visits?${query}`);
    },
    create: (body: { customer_id: string; source: string }): Promise<Visit> =>
        request('/visits', { method: 'POST', body: JSON.stringify(body) }),
    updateOrder: (visitId: string, orderNote: string): Promise<{ status: string }> =>
        request(`/visits/${visitId}/order?order_note=${encodeURIComponent(orderNote)}`, { method: 'PATCH' })  // ← tambah ini
    },

    cameras: {
        list: (params?: { page?: number }): Promise<PaginatedResponse<CameraSource>> => {
            const query = new URLSearchParams();
            if (params?.page) query.set('page', String(params.page));
            return request(`/cameras?${query}`);
        },
        get: (id: string): Promise<CameraSource> => request(`/cameras/${id}`),
        create: (body: Omit<CameraSource, 'id' | 'last_frame_at' | 'created_at'>): Promise<CameraSource> =>
            request('/cameras', { method: 'POST', body: JSON.stringify(body) }),
        update: (id: string, body: Partial<CameraSource>): Promise<CameraSource> =>
            request(`/cameras/${id}`, { method: 'PATCH', body: JSON.stringify(body) }),
        delete: (id: string): Promise<void> =>
            request(`/cameras/${id}`, { method: 'DELETE' })
    },

    recognition: {
        list: (params?: { camera_id?: string; customer_id?: string; matched?: boolean; page?: number }): Promise<PaginatedResponse<RecognitionEvent>> => {
            const query = new URLSearchParams();
            if (params?.camera_id) query.set('camera_id', params.camera_id);
            if (params?.customer_id) query.set('customer_id', params.customer_id);
            if (params?.matched !== undefined) query.set('matched', String(params.matched));
            if (params?.page) query.set('page', String(params.page));
            return request(`/recognition?${query}`);
        },
        get: (id: string): Promise<RecognitionEvent> => request(`/recognition/${id}`)
    },

    enrollment: {
        enroll: (customerId: string, file: File): Promise<{ face_id: string; customer_id: string; det_score: number }> => {
            const formData = new FormData();
            formData.append('file', file);
            return fetch(`${BASE_URL}/enrollment/${customerId}/enroll`, {
                method: 'POST',
                body: formData
            }).then((r) => {
                if (!r.ok) throw new ApiError(r.status, 'Enrollment failed');
                return r.json();
            });
        },
        recognize: (file: File): Promise<{ recognized: boolean; customer_name?: string; confidence?: number }> => {
            const formData = new FormData();
            formData.append('file', file);
            return fetch(`${BASE_URL}/enrollment/recognize`, {
                method: 'POST',
                body: formData
            }).then((r) => {
                if (!r.ok) throw new ApiError(r.status, 'Recognize failed');
                return r.json();
            });
        }
    }
};