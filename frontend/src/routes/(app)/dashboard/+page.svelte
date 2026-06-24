<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { activeNotifications, notifications, activeUnknownNotifications, unknownNotifications } from '$lib/stores/notifications';
	import { wsConnected } from '$lib/stores/systemHealth';
	import { createWsClient } from '$lib/ws/client';
	import { api } from '$lib/api/client';

	const STREAM_URL = 'http://localhost:8000/cameras/stream/live';

	let wsClient: { destroy: () => void } | null = null;

	onMount(() => {
		wsClient = createWsClient();
	});

	onDestroy(() => {
		wsClient?.destroy();
	});

	// Modal state
	let showModal = $state(false);
	let modalNotif = $state<typeof $activeNotifications[0] | null>(null);
	let orderInput = $state('');
	let saving = $state(false);

	function openOrderModal(notif: typeof $activeNotifications[0]): void {
		modalNotif = notif;
		orderInput = notif.payload.preferences ?? '';
		showModal = true;
	}

	async function saveOrder(): Promise<void> {
		if (!modalNotif || !orderInput.trim()) return;
		saving = true;
		try {
			const visit = await api.visits.create({
				customer_id: modalNotif.payload.customer_id,
				source: 'manual'
			});
			await api.visits.updateOrder(visit.id, orderInput.trim());
			notifications.dismiss(modalNotif.id);
			showModal = false;
		} catch (e) {
			alert('Gagal menyimpan pesanan');
		} finally {
			saving = false;
		}
	}

	function confidence(similarity: number): string {
		if (similarity >= 0.8) return 'text-success-400';
		if (similarity >= 0.6) return 'text-warning-400';
		return 'text-error-400';
	}

	function timeAgo(ts: number): string {
		const diff = Math.floor((Date.now() - ts) / 1000);
		if (diff < 60) return 'Baru saja';
		const minutes = Math.floor(diff / 60);
		if (minutes < 60) return `${minutes} menit lalu`;
		const hours = Math.floor(minutes / 60);
		if (hours < 24) return `${hours} jam lalu`;
		return `${Math.floor(hours / 24)} hari lalu`;
	}

	function formatDate(date: string | null): string {
		if (!date) return '-';
		return new Date(date).toLocaleString('id-ID', {
			day: '2-digit', month: 'long', year: 'numeric',
			hour: '2-digit', minute: '2-digit'
		});
	}
</script>

<svelte:head>
	<title>Dashboard — Camera Cafe CRM</title>
</svelte:head>

<div class="flex h-full flex-col gap-4">
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

	<!-- Layout 2 kolom -->
	<div class="grid grid-cols-[1fr_380px] gap-4 flex-1">

		<!-- Kolom kiri — Video -->
		<div class="rounded-xl border border-surface-700 bg-surface-900 overflow-hidden flex flex-col">
			<div class="flex items-center justify-between px-4 py-2 border-b border-surface-700">
				<p class="text-sm font-semibold text-surface-300">Kamera Kasir</p>
				{#if $activeNotifications.length > 0}
					<span class="text-xs font-medium text-warning-400">
						{$activeNotifications.length} pelanggan terdeteksi
					</span>
				{:else}
					<span class="text-xs text-surface-500">Menunggu pelanggan...</span>
				{/if}
			</div>
			<div class="relative flex-1">
				<img
					src={STREAM_URL}
					alt="Live stream kamera"
					class="w-full h-full object-contain bg-black"
				/>
				{#if $activeNotifications.length > 0}
					<div class="absolute bottom-0 left-0 right-0 flex flex-wrap gap-2 p-3">
						{#each $activeNotifications as notif (notif.id)}
							<span class="rounded-full bg-black/70 px-3 py-1 text-sm font-semibold {confidence(notif.payload.similarity)}">
								{notif.payload.customer_name} — {Math.round(notif.payload.similarity * 100)}%
							</span>
						{/each}
					</div>
				{/if}
			</div>
		</div>

		<!-- Kolom kanan — Notifikasi -->
		<div class="flex flex-col gap-3 overflow-y-auto">
			{#if $activeNotifications.length === 0 && $activeUnknownNotifications.length === 0}
				<div class="flex flex-1 flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-surface-700 text-center p-6 h-full">
					<p class="text-4xl">📡</p>
					<p class="font-semibold text-surface-300">Menunggu pelanggan</p>
					<p class="text-sm text-surface-500">Notifikasi muncul otomatis saat kamera mendeteksi pelanggan</p>
				</div>
			{:else}
				<!-- Card Unknown -->
				{#each $activeUnknownNotifications as notif (notif.id)}
					<div class="rounded-xl border border-warning-700 bg-warning-900/20 p-4 shadow-lg">
						<div class="flex items-start justify-between">
							<div>
								<p class="font-bold text-lg text-warning-300">Wajah Tidak Dikenal</p>
								<p class="mt-1 text-xs text-surface-500">{timeAgo(notif.received_at)}</p>
							</div>
							<button
								onclick={() => unknownNotifications.dismiss(notif.id)}
								class="text-surface-400 hover:text-surface-200">
								✕
							</button>
						</div>
						<p class="mt-2 text-xs text-surface-400">Pelanggan belum terdaftar di sistem</p>
						<div class="mt-3">
							<a
								href="/enrollment"
								onclick={() => unknownNotifications.dismiss(notif.id)}
								class="block w-full rounded-md bg-warning-600 py-2 text-center text-sm font-semibold text-white hover:bg-warning-500">
								+ Daftarkan Pelanggan
							</a>
						</div>
					</div>
				{/each}

				<!-- Card Pelanggan Dikenal -->
				{#each $activeNotifications as notif (notif.id)}
					<div class="rounded-xl border border-surface-700 bg-surface-900 p-4 shadow-lg">
						<div class="flex items-start justify-between">
							<div>
								<p class="font-bold text-lg text-surface-50">{notif.payload.customer_name}</p>
								<p class="mt-1 text-xs text-surface-500">{timeAgo(notif.received_at)}</p>
							</div>
							<span class="text-md font-bold {confidence(notif.payload.similarity)}">
								{Math.round(notif.payload.similarity * 100)}%
							</span>
						</div>

						{#if notif.payload.preferences}
							<div class="mt-2 rounded-lg bg-surface-800 p-3">
								<p class="text-xs uppercase tracking-wider text-surface-500">Preferensi</p>
								<p class="mt-2 text-sm text-surface-100">{notif.payload.preferences}</p>
							</div>
						{/if}

						{#if notif.payload.last_visit}
							<p class="mt-2 text-xs text-surface-400">
								Kunjungan terakhir: {formatDate(notif.payload.last_visit)}
							</p>
						{/if}

						<div class="mt-3 flex gap-2">
							<button
								onclick={() => openOrderModal(notif)}
								class="flex-1 rounded-md bg-success-600 py-2 text-center text-sm font-semibold text-white hover:bg-success-500">
								Catat Pesanan
							</button>
							<a
								href="/customers/{notif.payload.customer_id}"
								class="flex-1 rounded-md bg-primary-500 py-2 text-center text-sm font-semibold text-white hover:bg-primary-400">
								Lihat Profil
							</a>
							<button
								onclick={() => notifications.dismiss(notif.id)}
								class="rounded-md bg-surface-700 px-3 py-2 text-sm font-semibold text-surface-300 hover:bg-surface-600">
								✕
							</button>
						</div>
					</div>
				{/each}
			{/if}
		</div>
	</div>
</div>

<!-- Modal Catat Pesanan -->
{#if showModal && modalNotif}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
		<div class="w-full max-w-sm rounded-xl border border-surface-700 bg-surface-900 p-6 shadow-xl">
			<h2 class="mb-4 text-lg font-semibold text-surface-50">
				Catat Pesanan — {modalNotif.payload.customer_name}
			</h2>

			{#if modalNotif.payload.preferences}
				<button
					onclick={() => { orderInput = modalNotif!.payload.preferences ?? ''; }}
					class="mb-4 w-full rounded-lg border border-success-600/40 bg-success-600/20 px-4 py-3 text-left text-sm font-medium text-success-300 hover:bg-success-600/30">
					✓ Pesan seperti biasanya: {modalNotif.payload.preferences}
				</button>
			{/if}

			<label for="orderInput" class="mb-1 block text-xs text-surface-400">Atau ketik pesanan:</label>
			<input
				id="orderInput"
				type="text"
				bind:value={orderInput}
				placeholder="contoh: Kopi Susu, Es Teh..."
				class="w-full rounded-md border border-surface-600 bg-surface-800 px-3 py-2 text-sm text-surface-100 placeholder-surface-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
			/>

			<div class="mt-4 flex gap-2">
				<button
					onclick={() => { showModal = false; }}
					class="flex-1 rounded-md border border-surface-600 px-4 py-2 text-sm text-surface-300 hover:bg-surface-800">
					Batal
				</button>
				<button
					onclick={saveOrder}
					disabled={saving || !orderInput.trim()}
					class="flex-1 rounded-md bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-400 disabled:opacity-50">
					{saving ? 'Menyimpan...' : 'Simpan'}
				</button>
			</div>
		</div>
	</div>
{/if}