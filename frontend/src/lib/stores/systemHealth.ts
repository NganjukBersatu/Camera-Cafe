import { writable } from 'svelte/store';
import type { SystemHealth, ServiceStatus } from '$lib/types';

const defaultHealth: SystemHealth = {
	api: 'unknown',
	database: 'unknown',
	redis: 'unknown',
	qdrant: 'unknown',
	mosquitto: 'unknown',
	celery: 'unknown'
};

function createHealthStore() {
	const { subscribe, set, update } = writable<SystemHealth>(defaultHealth);

	function setService(service: keyof SystemHealth, status: ServiceStatus): void {
		update((h) => ({ ...h, [service]: status }));
	}

	function setAll(health: SystemHealth): void {
		set(health);
	}

	return { subscribe, setService, setAll };
}

export const systemHealth = createHealthStore();
export const wsConnected = writable<boolean>(false);
