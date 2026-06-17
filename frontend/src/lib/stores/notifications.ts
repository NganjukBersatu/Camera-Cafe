import { writable, derived } from 'svelte/store';
import type { Notification, WsCustomerDetectedPayload } from '$lib/types';

function createNotificationStore() {
	const { subscribe, update } = writable<Notification[]>([]);

	function add(payload: WsCustomerDetectedPayload): void {
		const notification: Notification = {
			id: crypto.randomUUID(),
			payload,
			received_at: Date.now(),
			dismissed: false
		};
		update((list) => [notification, ...list].slice(0, 50));
	}

	function dismiss(id: string): void {
		update((list) =>
			list.map((n) => (n.id === id ? { ...n, dismissed: true } : n))
		);
	}

	function clear(): void {
		update(() => []);
	}

	return { subscribe, add, dismiss, clear };
}

export const notifications = createNotificationStore();

export const activeNotifications = derived(notifications, ($list) =>
	$list.filter((n) => !n.dismissed)
);
