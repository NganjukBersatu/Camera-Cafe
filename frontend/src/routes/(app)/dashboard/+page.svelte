<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { activeNotifications, notifications } from '$lib/stores/notifications';
	import { wsConnected } from '$lib/stores/systemHealth';
	import { createWsClient } from '$lib/ws/client';

	let wsClient: { destroy: () => void } | null = null;

	onMount(() => {
		wsClient = createWsClient();
	});

	onDestroy(() => {
		wsClient?.destroy();
	});

	function confidence(similarity: number): string {
		if (similarity >= 0.8) return 'text-success-400';
		if (similarity >= 0.6) return 'text-warning-400';
		return 'text-error-400';
	}

	function timeAgo(ts: number): string {
		const diff = Math.floor((Date.now() - ts) / 1000);

		if (diff < 60) return 'Baru saja';

		const minutes = Math.floor(diff / 60);

		if (minutes < 60) {
			return `${minutes} menit lalu`;
		}

		const hours = Math.floor(minutes / 60);

		if (hours < 24) {
			return `${hours} jam lalu`;
		}

		return `${Math.floor(hours / 24)} hari lalu`;
	}

	function formatDate(date: string | null): string {
		if (!date) return '-';

		return new Date(date).toLocaleString('id-ID', {
			day: '2-digit',
			month: 'long',
			year: 'numeric',
			hour: '2-digit',
			minute: '2-digit'
		});
	}
</script>

<svelte:head>
	<title>Dashboard — Camera Cafe CRM</title>
</svelte:head>

<div class="flex h-full flex-col gap-6">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold text-surface-50">Dashboard Kasir</h1>
			<p class="text-sm text-surface-400">Notifikasi pelanggan real-time</p>
		</div>

		<div class="flex items-center gap-2 text-sm">
			<span class="size-2 rounded-full {$wsConnected ? 'bg-success-500' : 'bg-error-500'}"></span>

			<span class="text-surface-400">
				{$wsConnected ? 'Terhubung' : 'Terputus'}
			</span>
		</div>
	</div>

	{#if $activeNotifications.length === 0}
		<div class="flex flex-1 flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-surface-700 text-center">
			<p class="text-4xl">📡</p>

			<p class="font-semibold text-surface-300">
				Menunggu pelanggan
			</p>

			<p class="text-sm text-surface-500">
				Notifikasi muncul otomatis saat kamera mendeteksi pelanggan
			</p>
		</div>

	{:else}

		<div class="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
			{#each $activeNotifications as notif (notif.id)}
				<div class="rounded-xl border border-surface-700 bg-surface-900 p-5 shadow-lg">
					<div class="flex items-start justify-between">
						<div>
							<p class="font-bold text-lg text-surface-50">
								{notif.payload.customer_name}
							</p>
							<p class="mt-1 text-xs text-surface-500">
								{timeAgo(notif.received_at)}
							</p>
						</div>
						<span class="text-md font-bold {confidence(notif.payload.similarity)}">
							{Math.round(notif.payload.similarity * 100)}%
						</span>
					</div>

					{#if notif.payload.preferences}
						<div class="mt-2 rounded-lg bg-surface-800 p-3">
							<p class="text-xs uppercase tracking-wider text-surface-500">
								Preferensi
							</p>
							<p class="mt-2 text-md text-surface-100">
								{notif.payload.preferences}
							</p>
						</div>
					{/if}

					{#if notif.payload.last_visit}
						<p class="mt-2 text-xs text-surface-400">
							Kunjungan terakhir:
							{formatDate(notif.payload.last_visit)}
						</p>
					{/if}
					<div class="mt-3 flex gap-2">
						<a
							href="/customers/{notif.payload.customer_id}"
							class="flex-1 rounded-md bg-primary-500 py-2 text-center text-sm font-semibold text-white hover:bg-primary-400">
							Lihat Profil
						</a>
						<button
							onclick={() => notifications.dismiss(notif.id)}
							class="flex-1 rounded-md bg-surface-700 py-2 text-sm font-semibold text-surface-300 hover:bg-surface-600"
						>
							Abaikan
						</button>
					</div>
				</div>
			{/each}
		</div>
	{/if}
</div>