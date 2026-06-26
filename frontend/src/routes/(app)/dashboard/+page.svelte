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

	function confidenceColor(similarity: number): string {
		if (similarity >= 0.8) return 'text-success-400';
		if (similarity >= 0.6) return 'text-warning-400';
		return 'text-error-400';
	}

	function confidenceBg(similarity: number): string {
		if (similarity >= 0.8) return 'bg-success-500/10 border-success-700/50';
		if (similarity >= 0.6) return 'bg-warning-500/10 border-warning-700/50';
		return 'bg-error-500/10 border-error-700/50';
	}

	function confidenceLabel(similarity: number): string {
		if (similarity >= 0.8) return 'Tinggi';
		if (similarity >= 0.6) return 'Sedang';
		return 'Rendah';
	}

	function timeAgo(ts: number): string {
		const diff = Math.floor((Date.now() - ts) / 1000);
		if (diff < 60) return 'Baru saja';
		const minutes = Math.floor(diff / 60);
		if (minutes < 60) return `${minutes} mnt lalu`;
		const hours = Math.floor(minutes / 60);
		if (hours < 24) return `${hours} jam lalu`;
		return `${Math.floor(hours / 24)} hari lalu`;
	}

	function formatDate(date: string | null): string {
		if (!date) return '-';
		return new Date(date).toLocaleString('id-ID', {
			day: '2-digit', month: 'short', year: 'numeric',
			hour: '2-digit', minute: '2-digit'
		});
	}

	let totalDetected = $derived($activeNotifications.length + $activeUnknownNotifications.length);
</script>

<svelte:head>
	<title>Dashboard — Camera Cafe CRM</title>
</svelte:head>

<div class="flex h-full flex-col gap-4">

	<!-- Header -->
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold text-surface-50">Dashboard Kasir</h1>
			<p class="text-sm text-surface-400">Deteksi wajah pelanggan secara real-time</p>
		</div>
		<div class="flex items-center gap-3">
			{#if $activeNotifications.length > 0}
				<span class="rounded-full bg-warning-500/15 px-3 py-1 text-xs font-semibold text-warning-400 border border-warning-700/40">
					{$activeNotifications.length} terdeteksi
				</span>
			{/if}
			<div class="flex items-center gap-2 rounded-full border px-3 py-1.5 text-xs font-medium
				{$wsConnected ? 'border-success-700/50 bg-success-500/10 text-success-400' : 'border-error-700/50 bg-error-500/10 text-error-400'}">
				<span class="size-1.5 rounded-full {$wsConnected ? 'bg-success-400' : 'bg-error-400'}"></span>
				{$wsConnected ? 'Terhubung' : 'Terputus'}
			</div>
		</div>
	</div>

	<!-- Layout 2 kolom -->
	<div class="grid flex-1 grid-cols-[1fr_360px] gap-4 min-h-0">

		<!-- Kolom kiri — Video -->
		<div class="flex flex-col overflow-hidden rounded-xl border border-surface-700 bg-surface-900">
			<div class="flex items-center justify-between border-b border-surface-700 px-4 py-2.5">
				<div class="flex items-center gap-2">
					<span class="size-2 rounded-full bg-error-500 animate-pulse"></span>
					<p class="text-sm font-semibold text-surface-200">Kamera Kasir</p>
				</div>
				<span class="text-xs text-surface-500">
					{totalDetected > 0 ? `${totalDetected} wajah terdeteksi` : 'Menunggu pelanggan...'}
				</span>
			</div>
			<div class="relative flex-1 bg-black">
				<img
					src={STREAM_URL}
					alt="Live stream kamera"
					class="h-full w-full object-contain"
				/>
				{#if $activeNotifications.length > 0}
					<div class="absolute bottom-0 left-0 right-0 flex flex-wrap gap-2 bg-linier-to-t from-black/80 to-transparent p-4">
						{#each $activeNotifications as notif (notif.id)}
							<span class="rounded-full bg-black/60 px-3 py-1 text-xs font-semibold backdrop-blur-sm {confidenceColor(notif.payload.similarity)}">
								{notif.payload.customer_name} · {Math.round(notif.payload.similarity * 100)}%
							</span>
						{/each}
					</div>
				{/if}
			</div>
		</div>

		<!-- Kolom kanan — Notifikasi -->
		<div class="flex flex-col gap-2.5 overflow-y-auto pr-0.5">

			{#if $activeNotifications.length === 0 && $activeUnknownNotifications.length === 0}
				<div class="flex h-full flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-surface-700 p-8 text-center">
					<i class="ti ti-radar-2 text-surface-500" style="font-size: 32px" aria-hidden="true"></i>
					<p class="font-semibold text-surface-300">Menunggu pelanggan</p>
					<p class="text-xs text-surface-500 leading-relaxed">Notifikasi muncul otomatis saat kamera mendeteksi wajah pelanggan</p>
				</div>

			{:else}

				<!-- Wajah tidak dikenal — compact -->
				{#each $activeUnknownNotifications as notif (notif.id)}
					<div class="rounded-xl border border-warning-700/50 bg-warning-900/15 p-3.5">
						<div class="flex items-center justify-between">
							<div class="flex items-center gap-2.5">
								<div class="flex size-8 items-center justify-center rounded-full bg-warning-500/20 text-sm">
									<i class="ti ti-user" style="font-size:16px" aria-hidden="true"></i>
								</div>
								<div>
									<p class="text-sm font-semibold text-warning-300">Wajah Tidak Dikenal</p>
									<p class="text-xs text-surface-500">{timeAgo(notif.received_at)}</p>
								</div>
							</div>
							<button
								onclick={() => unknownNotifications.dismiss(notif.id)}
								class="rounded p-1 text-surface-500 hover:text-surface-300"
								aria-label="Tutup"
							>
								✕
							</button>
						</div>
						<a
							href="/enrollment"
							onclick={() => unknownNotifications.dismiss(notif.id)}
							class="mt-2.5 flex w-full items-center justify-center gap-1.5 rounded-lg bg-warning-600 py-1.5 text-xs font-semibold text-white hover:bg-warning-500"
						>
							+ Daftarkan Pelanggan
						</a>
					</div>
				{/each}

				<!-- Pelanggan dikenal -->
				{#each $activeNotifications as notif (notif.id)}
					<div class="rounded-xl border border-surface-700 bg-surface-900 p-4">

						<!-- Header -->
						<div class="flex items-start justify-between gap-2">
							<div class="flex items-center gap-3">
								<div class="flex size-9 items-center justify-center rounded-full bg-primary-500/20 text-sm font-bold text-primary-300">
									{notif.payload.customer_name.charAt(0).toUpperCase()}
								</div>
								<div>
									<p class="font-semibold text-surface-50">{notif.payload.customer_name}</p>
									<p class="text-xs text-surface-500">{timeAgo(notif.received_at)}</p>
								</div>
							</div>
							<div class="flex items-center gap-2">
								<span class="rounded-full border px-2 py-0.5 text-xs font-semibold {confidenceBg(notif.payload.similarity)} {confidenceColor(notif.payload.similarity)}">
									{Math.round(notif.payload.similarity * 100)}% · {confidenceLabel(notif.payload.similarity)}
								</span>
								<button
									onclick={() => notifications.dismiss(notif.id)}
									class="rounded p-1 text-surface-500 hover:text-surface-300"
									aria-label="Tutup"
								>
									✕
								</button>
							</div>
						</div>

						<!-- Preferensi -->
						{#if notif.payload.preferences}
							<div class="mt-3 rounded-lg bg-surface-800 px-3 py-2">
								<p class="text-xs text-surface-500">Biasanya pesan</p>
								<p class="mt-0.5 text-sm font-medium text-surface-100">{notif.payload.preferences}</p>
							</div>
						{/if}

						<!-- Kunjungan terakhir -->
						{#if notif.payload.last_visit}
							<p class="mt-2 text-xs text-surface-500">
								Terakhir: {formatDate(notif.payload.last_visit)}
							</p>
						{/if}

						<!-- Aksi -->
						<div class="mt-3 flex gap-2">
							<button
								onclick={() => openOrderModal(notif)}
								class="flex-1 rounded-lg bg-success-600 py-2 text-xs font-semibold text-white hover:bg-success-500"
							>
								Catat Pesanan
							</button>
							<a
								href="/customers/{notif.payload.customer_id}"
								class="flex-1 rounded-lg bg-surface-700 py-2 text-center text-xs font-semibold text-surface-200 hover:bg-surface-600"
							>
								Lihat Profil
							</a>
						</div>
					</div>
				{/each}
			{/if}
		</div>
	</div>
</div>

<!-- Modal Catat Pesanan -->
{#if showModal && modalNotif}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
		role="presentation"
		onclick={() => { if (!saving) showModal = false; }}
		onkeydown={() => { if (!saving) showModal = false; }}
	>
		<div
			class="w-full max-w-sm rounded-xl border border-surface-700 bg-surface-900 p-6 shadow-2xl"
			role="dialog"
			aria-modal="true"
			aria-label="Catat pesanan"
			tabindex="-1"
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => e.stopPropagation()}
		>
			<!-- Header modal -->
			<div class="mb-4 flex items-center gap-3">
				<div class="flex size-10 items-center justify-center rounded-full bg-primary-500/20 text-base font-bold text-primary-300">
					{modalNotif.payload.customer_name.charAt(0).toUpperCase()}
				</div>
				<div>
					<h2 class="font-semibold text-surface-50">{modalNotif.payload.customer_name}</h2>
					<p class="text-xs text-surface-500">Catat pesanan kunjungan ini</p>
				</div>
			</div>

			<!-- Saran dari preferensi -->
			{#if modalNotif.payload.preferences}
				<button
					onclick={() => { orderInput = modalNotif!.payload.preferences ?? ''; }}
					class="mb-3 w-full rounded-lg border border-success-600/30 bg-success-600/10 px-4 py-3 text-left hover:bg-success-600/20"
				>
					<p class="text-xs text-success-500">Pesanan biasanya</p>
					<p class="mt-0.5 text-sm font-medium text-success-300">{modalNotif.payload.preferences}</p>
				</button>
			{/if}

			<!-- Input pesanan -->
			<label for="orderInput" class="mb-1.5 block text-xs text-surface-400">Pesanan</label>
			<input
				id="orderInput"
				type="text"
				bind:value={orderInput}
				placeholder="contoh: Kopi Susu, Es Teh..."
				class="w-full rounded-lg border border-surface-600 bg-surface-800 px-3 py-2.5 text-sm text-surface-100 placeholder-surface-500 focus:border-primary-500 focus:outline-none"
			/>

			<!-- Aksi -->
			<div class="mt-4 flex gap-2">
				<button
					onclick={() => { showModal = false; }}
					disabled={saving}
					class="flex-1 rounded-lg border border-surface-600 py-2 text-sm text-surface-300 hover:bg-surface-800 disabled:opacity-50"
				>
					Batal
				</button>
				<button
					onclick={saveOrder}
					disabled={saving || !orderInput.trim()}
					class="flex-1 rounded-lg bg-primary-500 py-2 text-sm font-semibold text-white hover:bg-primary-400 disabled:opacity-50"
				>
					{saving ? 'Menyimpan...' : 'Simpan Pesanan'}
				</button>
			</div>
		</div>
	</div>
{/if}