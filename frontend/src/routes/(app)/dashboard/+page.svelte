<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { activeNotifications, notifications } from '$lib/stores/notifications';
	import { wsConnected } from '$lib/stores/systemHealth';
	import { createWsClient } from '$lib/ws/client';
	import type { Notification } from '$lib/types';

	let wsClient: { destroy: () => void } | null = null;

	onMount(() => {
		wsClient = createWsClient();
	});

	onDestroy(() => {
		wsClient?.destroy();
	});

	function confidence(similarity: number): string {
		if (similarity >= 0.85) return 'text-success-400';
		if (similarity >= 0.7) return 'text-warning-400';
		return 'text-error-400';
	}

	function timeAgo(ts: number): string {
		const secs = Math.floor((Date.now() - ts) / 1000);
		if (secs < 60) return `${secs}d lalu`;
		return `${Math.floor(secs / 60)}m lalu`;
	}
</script>

<svelte:head><title>Dashboard — Camera Cafe CRM</title></svelte:head>

<div class="flex h-full flex-col gap-6">
	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold text-surface-50">Dashboard Kasir</h1>
			<p class="text-sm text-surface-400">Notifikasi pelanggan real-time</p>
		</div>
		<div class="flex items-center gap-2 text-sm">
			<span class="size-2 rounded-full {$wsConnected ? 'bg-success-500' : 'bg-error-500'}"></span>
			<span class="text-surface-400">{$wsConnected ? 'Terhubung' : 'Terputus'}</span>
		</div>
	</div>

	<!-- Queue aktif -->
	{#if $activeNotifications.length === 0}
		<div class="flex flex-1 flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-surface-700 text-center">
			<p class="text-4xl">📡</p>
			<p class="font-semibold text-surface-300">Menunggu pelanggan</p>
			<p class="text-sm text-surface-500">Notifikasi muncul otomatis saat kamera mendeteksi pelanggan</p>
		</div>
	{:else}
		<div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
			{#each $activeNotifications as notif (notif.id)}
				<div class="rounded-xl border border-surface-700 bg-surface-900 p-5">
					<div class="flex items-start justify-between">
						<div>
							<p class="font-bold text-surface-50">{notif.payload.customer_name}</p>
							<p class="mt-0.5 text-xs text-surface-500">{timeAgo(notif.received_at)}</p>
						</div>
						<span class="text-sm font-semibold {confidence(notif.payload.similarity)}">
							{Math.round(notif.payload.similarity * 100)}%
						</span>
					</div>

					{#if notif.payload.preferences}
						<div class="mt-3 rounded-md bg-surface-800 p-3">
							<p class="text-xs font-semibold uppercase tracking-wider text-surface-400">Preferensi</p>
							<p class="mt-1 text-sm text-surface-200">{notif.payload.preferences}</p>
						</div>
					{/if}

					{#if notif.payload.last_visit}
						<p class="mt-2 text-xs text-surface-500">Kunjungan terakhir: {notif.payload.last_visit}</p>
					{/if}

					<div class="mt-4 flex gap-2">
						<a
							href="/customers/{notif.payload.customer_id}"
							class="flex-1 rounded-md bg-primary-500 py-2 text-center text-xs font-semibold text-white hover:bg-primary-400"
						>
							Lihat Profil
						</a>
						<button
							onclick={() => notifications.dismiss(notif.id)}
							class="flex-1 rounded-md bg-surface-700 py-2 text-xs font-semibold text-surface-300 hover:bg-surface-600"
						>
							Abaikan
						</button>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>
