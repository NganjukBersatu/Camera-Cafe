// Dummy types — akan diganti auto-generate dari FastAPI OpenAPI schema (openapi-typescript)
// saat backend Phase 1 selesai. Tidak ada any, tidak ada undefined tanpa union eksplisit.

export type CustomerStatus = 'active' | 'inactive';
export type CameraRole = 'entrance' | 'cashier';
export type CameraStatus = 'online' | 'offline' | 'unknown';
export type VisitSource = 'auto_recognition' | 'manual';
export type ServiceStatus = 'ok' | 'error' | 'unknown';

export interface Customer {
	id: string;
	name: string;
	contact: string | null;
	notes: string | null;
	preferences: string | null;
	status: CustomerStatus;
	face_count: number;
	created_at: string;
	updated_at: string;
}

export interface CustomerFace {
	id: string;
	customer_id: string;
	preview_url: string | null;
	created_at: string;
}

export interface Visit {
	id: string;
	customer_id: string;
	customer_name: string;
	source: VisitSource;
	recognition_event_id: string | null;
	visited_at: string;
	order_note: string | null;
}

export interface RecognitionEvent {
	id: string;
	camera_id: string;
	customer_id: string | null;
	similarity: number;
	matched: boolean;
	frame_url: string | null;
	detected_at: string;
}

export interface CameraSource {
	id: string;
	name: string;
	role: CameraRole;
	rtsp_url: string;
	status: CameraStatus;
	last_frame_at: string | null;
}

export interface SystemHealth {
	api: ServiceStatus;
	database: ServiceStatus;
	redis: ServiceStatus;
	qdrant: ServiceStatus;
	mosquitto: ServiceStatus;
	celery: ServiceStatus;
}

// WebSocket payload dari FastAPI recognition event
export interface WsCustomerDetectedPayload {
	event_type: 'customer_detected';
	camera_id: string;
	customer_id: string;
	customer_name: string;
	similarity: number;
	preferences: string | null;
	notes: string | null;
	total_visits: number;
	last_visit: string | null;
	detected_at: string;
}

export interface WsNoMatchPayload {
	event_type: 'no_match';
	camera_id: string;
	detected_at: string;
}

export interface WsSystemHealthPayload {
	event_type: 'system_health';
	health: SystemHealth;
}

export type WsPayload = WsCustomerDetectedPayload | WsNoMatchPayload | WsSystemHealthPayload | WsUnknownDetectedPayload;

// Notifikasi di queue dashboard kasir
export interface Notification {
	id: string;
	payload: WsCustomerDetectedPayload;
	received_at: number;
	dismissed: boolean;
}

export interface WsUnknownDetectedPayload {
	event_type: 'unknown_detected';
	camera_id: string;
	detected_at: string;
}

export interface UnknownNotification {
	id: string;
	received_at: number;
	dismissed: boolean;
}

// Response API wrapper
export interface PaginatedResponse<T> {
	items: T[];
	total: number;
	page: number;
	size: number;
}
export interface MenuItem {
	id: string;
	name: string;
	description: string | null;
	price: number;
	category: string | null;
	image_path: string | null;
	image_url: string | null;
	is_available: boolean;
	created_at: string;
	updated_at: string;
}