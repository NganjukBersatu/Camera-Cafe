import type { WsPayload } from '$lib/types';
import { notifications, unknownNotifications } from '$lib/stores/notifications';
import { systemHealth, wsConnected } from '$lib/stores/systemHealth';

const WS_URL = import.meta.env.VITE_WS_URL ?? 'ws://localhost:8000/ws';
const RECONNECT_DELAY_MS = 3000;
const MAX_RECONNECT_ATTEMPTS = 10;

function isWsPayload(data: unknown): data is WsPayload {
	return (
		typeof data === 'object' &&
		data !== null &&
		'event_type' in data &&
		typeof (data as Record<string, unknown>)['event_type'] === 'string'
	);
}

function handlePayload(payload: WsPayload): void {
	if (payload.event_type === 'customer_detected') {
		notifications.add(payload);
	} else if (payload.event_type === 'unknown_detected') {
		unknownNotifications.add();
	} else if (payload.event_type === 'system_health') {
		systemHealth.setAll(payload.health);
	}
}

export function createWsClient(): { destroy: () => void } {
	let socket: WebSocket | null = null;
	let attempts = 0;
	let destroyed = false;
	let reconnectTimer: ReturnType<typeof setTimeout> | null = null;

	function connect(): void {
		if (destroyed) return;

		socket = new WebSocket(WS_URL);

		socket.onopen = () => {
			attempts = 0;
			wsConnected.set(true);
		};

		socket.onmessage = (event: MessageEvent<string>) => {
			let parsed: unknown;
			try {
				parsed = JSON.parse(event.data);
			} catch {
				return;
			}
			if (isWsPayload(parsed)) {
				handlePayload(parsed);
			}
		};

		socket.onclose = () => {
			wsConnected.set(false);
			socket = null;
			if (!destroyed && attempts < MAX_RECONNECT_ATTEMPTS) {
				attempts++;
				reconnectTimer = setTimeout(connect, RECONNECT_DELAY_MS);
			}
		};

		socket.onerror = () => {
			socket?.close();
		};
	}

	connect();

	return {
		destroy() {
			destroyed = true;
			if (reconnectTimer !== null) clearTimeout(reconnectTimer);
			socket?.close();
			wsConnected.set(false);
		}
	};
}