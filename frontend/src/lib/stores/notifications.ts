import { writable, derived } from 'svelte/store';
import type { Notification, WsCustomerDetectedPayload, UnknownNotification } from '$lib/types';

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

function createUnknownStore() {
	const { subscribe, update } = writable<UnknownNotification[]>([]);

	function add(): void {
		const notif: UnknownNotification = {
			id: crypto.randomUUID(),
			received_at: Date.now(),
			dismissed: false
		};
		update((list) => [notif, ...list].slice(0, 5));
	}

	function dismiss(id: string): void {
		update((list) =>
			list.map((n) => (n.id === id ? { ...n, dismissed: true } : n))
		);
	}

	return { subscribe, add, dismiss };
}

export const notifications = createNotificationStore();
export const unknownNotifications = createUnknownStore();

export const activeNotifications = derived(notifications, ($list) =>
	$list.filter((n) => !n.dismissed)
);

export const activeUnknownNotifications = derived(unknownNotifications, ($list) =>
	$list.filter((n) => !n.dismissed)
);