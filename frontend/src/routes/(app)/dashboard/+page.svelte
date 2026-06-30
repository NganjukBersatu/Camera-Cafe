<script lang="ts">
	import { onMount, onDestroy } from 'svelte';
	import { activeNotifications, notifications, activeUnknownNotifications, unknownNotifications } from '$lib/stores/notifications';
	import { wsConnected } from '$lib/stores/systemHealth';
	import { createWsClient } from '$lib/ws/client';
	import { api } from '$lib/api/client';
	import type { MenuItem } from '$lib/types';

	const STREAM_URL = 'http://localhost:8000/cameras/stream/live';

	let wsClient: { destroy: () => void } | null = null;

	onMount(() => {
		wsClient = createWsClient();
		void loadMenu();
	});

	onDestroy(() => {
		wsClient?.destroy();
	});

	// Menu state
	let menuItems = $state<MenuItem[]>([]);
	let menuLoading = $state(false);
	let selectedCategory = $state<string | null>(null);
	let cart = $state<Record<string, number>>({});

	async function loadMenu(): Promise<void> {
		menuLoading = true;
		try {
			const res = await api.menu.list({ available_only: true });
			menuItems = res.items;
		} catch (e) {
			console.error('Gagal memuat menu', e);
		} finally {
			menuLoading = false;
		}
	}

	let categories = $derived([...new Set(menuItems.map(m => m.category).filter(Boolean))] as string[]);
	let filteredMenu = $derived(
		selectedCategory
			? menuItems.filter(m => m.category === selectedCategory)
			: menuItems
	);

	function addToCart(id: string): void {
		cart = { ...cart, [id]: (cart[id] ?? 0) + 1 };
	}

	function removeFromCart(id: string): void {
		const qty = cart[id] ?? 0;
		if (qty <= 1) {
			const { [id]: _, ...rest } = cart;
			cart = rest;
		} else {
			cart = { ...cart, [id]: qty - 1 };
		}
	}

	let cartTotal = $derived(
		Object.entries(cart).reduce((sum, [id, qty]) => {
			const item = menuItems.find(m => m.id === id);
			return sum + (item ? item.price * qty : 0);
		}, 0)
	);

	let cartSummary = $derived(
		Object.entries(cart)
			.map(([id, qty]) => {
				const item = menuItems.find(m => m.id === id);
				return item ? `${item.name} x${qty}` : '';
			})
			.filter(Boolean)
			.join(', ')
	);

	// Modal state
	let showModal = $state(false);
	let modalNotif = $state<typeof $activeNotifications[0] | null>(null);
	let saving = $state(false);

	function openOrderModal(notif: typeof $activeNotifications[0]): void {
		modalNotif = notif;
		cart = {};
		selectedCategory = null;
		showModal = true;
	}

	async function saveOrder(): Promise<void> {
		if (!modalNotif || !cartSummary) return;
		saving = true;
		try {
			const visit = await api.visits.create({
				customer_id: modalNotif.payload.customer_id,
				source: 'manual'
			});
			await api.visits.updateOrder(visit.id, cartSummary);
			notifications.dismiss(modalNotif.id);
			showModal = false;
			cart = {};
		} catch (e) {
			alert('Gagal menyimpan pesanan');
		} finally {
			saving = false;
		}
	}

	function formatPrice(price: number): string {
		return new Intl.NumberFormat('id-ID', {
			style: 'currency', currency: 'IDR', minimumFractionDigits: 0
		}).format(price);
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
				<img src={STREAM_URL} alt="Live stream kamera" class="h-full w-full object-contain" />
				{#if $activeNotifications.length > 0}
					<div class="absolute bottom-0 left-0 right-0 flex flex-wrap gap-2 bg-linear-to-t from-black/80 to-transparent p-4">
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
				<!-- Wajah tidak dikenal -->
				{#each $activeUnknownNotifications as notif (notif.id)}
					<div class="rounded-xl border border-warning-700/50 bg-warning-900/15 p-3.5">
						<div class="flex items-center justify-between">
							<div class="flex items-center gap-2.5">
								<div class="flex size-8 items-center justify-center rounded-full bg-warning-500/20">
									<i class="ti ti-user text-warning-400" style="font-size:16px" aria-hidden="true"></i>
								</div>
								<div>
									<p class="text-sm font-semibold text-warning-300">Wajah Tidak Dikenal</p>
									<p class="text-xs text-surface-500">{timeAgo(notif.received_at)}</p>
								</div>
							</div>
							<button onclick={() => unknownNotifications.dismiss(notif.id)} class="rounded p-1 text-surface-500 hover:text-surface-300" aria-label="Tutup">✕</button>
						</div>
						<a href="/enrollment" onclick={() => unknownNotifications.dismiss(notif.id)}
							class="mt-2.5 flex w-full items-center justify-center gap-1.5 rounded-lg bg-warning-600 py-1.5 text-xs font-semibold text-white hover:bg-warning-500">
							+ Daftarkan Pelanggan
						</a>
					</div>
				{/each}

				<!-- Pelanggan dikenal -->
				{#each $activeNotifications as notif (notif.id)}
					<div class="rounded-xl border border-surface-700 bg-surface-900 p-4">
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
								<button onclick={() => notifications.dismiss(notif.id)} class="rounded p-1 text-surface-500 hover:text-surface-300" aria-label="Tutup">✕</button>
							</div>
						</div>

						{#if notif.payload.preferences}
							<div class="mt-3 rounded-lg bg-surface-800 px-3 py-2">
								<p class="text-xs text-surface-500">Biasanya pesan</p>
								<p class="mt-0.5 text-sm font-medium text-surface-100">{notif.payload.preferences}</p>
							</div>
						{/if}

						{#if notif.payload.last_visit}
							<p class="mt-2 text-xs text-surface-500">Terakhir: {formatDate(notif.payload.last_visit)}</p>
						{/if}

						<div class="mt-3 flex gap-2">
							<button onclick={() => openOrderModal(notif)}
								class="flex-1 rounded-lg bg-success-600 py-2 text-xs font-semibold text-white hover:bg-success-500">
								Catat Pesanan
							</button>
							<a href="/customers/{notif.payload.customer_id}"
								class="flex-1 rounded-lg bg-surface-700 py-2 text-center text-xs font-semibold text-surface-200 hover:bg-surface-600">
								Lihat Profil
							</a>
						</div>
					</div>
				{/each}
			{/if}
		</div>
	</div>
</div>

<!-- Modal Catat Pesanan — Menu Grid -->
{#if showModal && modalNotif}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
		role="presentation"
		onclick={() => { if (!saving) showModal = false; }}
		onkeydown={() => { if (!saving) showModal = false; }}
	>
		<div
			class="flex h-[85vh] w-full max-w-2xl flex-col rounded-xl border border-surface-700 bg-surface-900 shadow-2xl"
			role="dialog"
			aria-modal="true"
			aria-label="Catat pesanan"
			tabindex="-1"
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => e.stopPropagation()}
		>
			<!-- Header modal -->
			<div class="flex items-center justify-between border-b border-surface-700 px-5 py-4">
				<div class="flex items-center gap-3">
					<div class="flex size-9 items-center justify-center rounded-full bg-primary-500/20 font-bold text-primary-300">
						{modalNotif.payload.customer_name.charAt(0).toUpperCase()}
					</div>
					<div>
						<p class="font-semibold text-surface-50">{modalNotif.payload.customer_name}</p>
						<p class="text-xs text-surface-500">Pilih menu pesanan</p>
					</div>
				</div>
				<button onclick={() => { showModal = false; }} class="rounded p-1 text-surface-400 hover:text-surface-200" aria-label="Tutup">
					<i class="ti ti-x" style="font-size:18px" aria-hidden="true"></i>
				</button>
			</div>

			<!-- Saran pesanan biasanya — menonjol -->
			{#if modalNotif.payload.preferences}
				<div class="mx-5 mt-4 flex items-center gap-3 rounded-xl border border-success-600/30 bg-gradient-to-r from-success-500/15 to-success-500/5 px-4 py-3">
					<div class="flex size-9 shrink-0 items-center justify-center rounded-full bg-success-500/20">
						<i class="ti ti-sparkles text-success-400" style="font-size:18px" aria-hidden="true"></i>
					</div>
					<div class="min-w-0 flex-1">
						<p class="text-[11px] font-medium uppercase tracking-wide text-success-500/80">Biasanya pesan</p>
						<p class="truncate text-sm font-semibold text-success-200">{modalNotif.payload.preferences}</p>
					</div>
				</div>
			{/if}

			<!-- Filter kategori -->
			{#if categories.length > 0}
				<div class="flex gap-2 overflow-x-auto border-b border-surface-700 px-5 py-3">
					<button
						onclick={() => (selectedCategory = null)}
						class="shrink-0 rounded-full px-3 py-1 text-xs font-medium transition-colors
							{selectedCategory === null ? 'bg-primary-500 text-white' : 'bg-surface-800 text-surface-400 hover:bg-surface-700'}"
					>
						Semua
					</button>
					{#each categories as cat}
						<button
							onclick={() => (selectedCategory = cat)}
							class="shrink-0 rounded-full px-3 py-1 text-xs font-medium transition-colors
								{selectedCategory === cat ? 'bg-primary-500 text-white' : 'bg-surface-800 text-surface-400 hover:bg-surface-700'}"
						>
							{cat}
						</button>
					{/each}
				</div>
			{/if}

			<!-- Grid menu -->
			<div class="flex-1 overflow-y-auto p-5">
				{#if menuLoading}
					<div class="flex items-center justify-center gap-2 py-12 text-surface-400">
						<i class="ti ti-loader-2 animate-spin" aria-hidden="true"></i>
						<span class="text-sm">Memuat menu...</span>
					</div>
				{:else if filteredMenu.length === 0}
					<div class="flex flex-col items-center justify-center gap-2 py-12 text-center">
						<i class="ti ti-tools-kitchen-2 text-surface-600" style="font-size:32px" aria-hidden="true"></i>
						<p class="text-sm text-surface-400">Belum ada menu tersedia</p>
						<a href="/settings" class="text-xs text-primary-400 hover:underline">Tambah menu di Settings →</a>
					</div>
				{:else}
					<div class="grid grid-cols-3 gap-3">
						{#each filteredMenu as item (item.id)}
							{@const qty = cart[item.id] ?? 0}
							<div class="overflow-hidden rounded-xl border border-surface-700 bg-surface-800 transition-all
								{qty > 0 ? 'border-primary-500/50 ring-1 ring-primary-500/30' : ''}">
								<!-- Foto -->
								<div class="relative h-28 bg-surface-700">
									{#if item.image_url}
										<img src={item.image_url} alt={item.name} class="h-full w-full object-cover" />
									{:else}
										<div class="flex h-full items-center justify-center">
											<i class="ti ti-tools-kitchen-2 text-surface-500" style="font-size:28px" aria-hidden="true"></i>
										</div>
									{/if}
									{#if qty > 0}
										<div class="absolute right-1.5 top-1.5 flex size-5 items-center justify-center rounded-full bg-primary-500 text-xs font-bold text-white">
											{qty}
										</div>
									{/if}
								</div>

								<!-- Info -->
								<div class="p-2.5">
									<p class="text-xs font-semibold text-surface-100 line-clamp-2 leading-tight">{item.name}</p>
									<p class="mt-1 text-xs font-bold text-primary-400">{formatPrice(item.price)}</p>

									<!-- Tombol +/- -->
									<div class="mt-2 flex items-center justify-between">
										{#if qty === 0}
											<button
												onclick={() => addToCart(item.id)}
												class="w-full rounded-lg bg-primary-500 py-1.5 text-xs font-semibold text-white hover:bg-primary-400"
											>
												+ Tambah
											</button>
										{:else}
											<div class="flex w-full items-center justify-between gap-1">
												<button
													onclick={() => removeFromCart(item.id)}
													class="flex size-7 items-center justify-center rounded-lg bg-surface-700 text-surface-200 hover:bg-surface-600"
												>
													<i class="ti ti-minus" style="font-size:12px" aria-hidden="true"></i>
												</button>
												<span class="text-sm font-bold text-surface-50">{qty}</span>
												<button
													onclick={() => addToCart(item.id)}
													class="flex size-7 items-center justify-center rounded-lg bg-primary-500 text-white hover:bg-primary-400"
												>
													<i class="ti ti-plus" style="font-size:12px" aria-hidden="true"></i>
												</button>
											</div>
										{/if}
									</div>
								</div>
							</div>
						{/each}
					</div>
				{/if}
			</div>

			<!-- Footer — ringkasan & simpan -->
			<div class="border-t border-surface-700 px-5 py-4">
				{#if cartSummary}
					<p class="mb-3 text-xs text-surface-400 line-clamp-2">
						<span class="font-medium text-surface-200">Pesanan:</span> {cartSummary}
					</p>
					<div class="flex items-center justify-between">
						<div>
							<p class="text-xs text-surface-500">Total</p>
							<p class="text-lg font-bold text-primary-400">{formatPrice(cartTotal)}</p>
						</div>
						<button
							onclick={saveOrder}
							disabled={saving}
							class="rounded-lg bg-success-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-success-500 disabled:opacity-50"
						>
							{saving ? 'Menyimpan...' : 'Simpan Pesanan'}
						</button>
					</div>
				{:else}
					<p class="text-center text-xs text-surface-500">Pilih menu di atas untuk mencatat pesanan</p>
				{/if}
			</div>
		</div>
	</div>
{/if}