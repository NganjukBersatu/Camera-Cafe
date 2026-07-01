<script lang="ts">
	import { page } from '$app/state';
	import { api } from '$lib/api/client';
	import type { Customer, Visit, CustomerFace, MenuItem } from '$lib/types';

	const customerId = $derived(page.params['id'] as string);

	let customer = $state<Customer | null>(null);
	let visits = $state<Visit[]>([]);
	let faces = $state<CustomerFace[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Modal order — menu grid
	let showOrderModal = $state(false);
	let selectedVisit = $state<Visit | null>(null);
	let savingOrder = $state(false);
	let menuItems = $state<MenuItem[]>([]);
	let menuLoading = $state(false);
	let selectedCategory = $state<string | null>(null);
	let cart = $state<Record<string, number>>({});

	// Modal tambah wajah
	let showFaceModal = $state(false);
	let faceFile = $state<File | null>(null);
	let facePreview = $state<string | null>(null);
	let savingFace = $state(false);
	let faceError = $state<string | null>(null);

	// Konfirmasi hapus wajah
	let deletingFaceId = $state<string | null>(null);
	let confirmDeleteFaceId = $state<string | null>(null);

	async function load(): Promise<void> {
		loading = true;
		error = null;
		try {
			const [c, v, f] = await Promise.all([
				api.customers.get(customerId),
				api.customers.visits(customerId),
				api.customers.faces(customerId)
			]);
			customer = c;
			visits = v.items;
			faces = f;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Gagal memuat data';
		} finally {
			loading = false;
		}
	}

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

	$effect(() => {
		void load();
	});

	async function deleteFace(faceId: string): Promise<void> {
		deletingFaceId = faceId;
		try {
			await api.customers.deleteFace(customerId, faceId);
			faces = faces.filter((f) => f.id !== faceId);
			confirmDeleteFaceId = null;
		} catch (e) {
			alert(e instanceof Error ? e.message : 'Gagal menghapus data wajah');
		} finally {
			deletingFaceId = null;
		}
	}

	const lastOrder = $derived(customer?.preferences ?? null);

	let categories = $derived([...new Set(menuItems.map(m => m.category).filter(Boolean))] as string[]);
	let filteredMenu = $derived(
		selectedCategory ? menuItems.filter(m => m.category === selectedCategory) : menuItems
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

	function openOrderModal(visit: Visit): void {
		selectedVisit = visit;
		cart = {};
		selectedCategory = null;
		showOrderModal = true;
		void loadMenu();
	}

	function openNewOrderModal(): void {
		const latest = visits[0] ?? null;
		selectedVisit = latest;
		cart = {};
		selectedCategory = null;
		showOrderModal = true;
		void loadMenu();
	}

	async function saveOrder(): Promise<void> {
		if (!cartSummary) return;
		savingOrder = true;
		try {
			let visitId: string;
			if (selectedVisit) {
				visitId = selectedVisit.id;
			} else {
				const newVisit = await api.visits.create({ customer_id: customerId, source: 'manual' });
				visitId = newVisit.id;
			}
			await api.visits.updateOrder(visitId, cartSummary);
			if (customer) customer = { ...customer, preferences: cartSummary };
			showOrderModal = false;
			cart = {};
			await load();
		} catch (e) {
			alert('Gagal menyimpan pesanan');
		} finally {
			savingOrder = false;
		}
	}

	function formatPrice(price: number): string {
		return new Intl.NumberFormat('id-ID', {
			style: 'currency', currency: 'IDR', minimumFractionDigits: 0
		}).format(price);
	}

	function handleFaceFile(e: Event): void {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;
		faceFile = file;
		facePreview = URL.createObjectURL(file);
	}

	async function saveFace(): Promise<void> {
		if (!faceFile) return;
		savingFace = true;
		faceError = null;
		try {
			await api.enrollment.enroll(customerId, faceFile);
			await load();
			showFaceModal = false;
			faceFile = null;
			facePreview = null;
		} catch (e) {
			faceError = e instanceof Error ? e.message : 'Gagal menyimpan wajah';
		} finally {
			savingFace = false;
		}
	}
</script>

<svelte:head><title>{customer?.name ?? 'Pelanggan'} — Camera Cafe CRM</title></svelte:head>

{#if loading}
	<div class="flex items-center justify-center gap-2 py-20 text-surface-400">
		<i class="ti ti-loader-2 animate-spin" aria-hidden="true"></i>
		<p>Memuat data...</p>
	</div>

{:else if error}
	<div class="rounded-xl border border-error-800 bg-error-900/20 p-6 text-center">
		<p class="font-semibold text-error-400">Gagal memuat data</p>
		<p class="mt-1 text-sm text-surface-400">{error}</p>
		<button onclick={load} class="mt-4 rounded-md bg-surface-700 px-4 py-2 text-sm text-surface-200">Coba lagi</button>
	</div>

{:else if customer}
	<div class="flex flex-col gap-6">
		<div class="flex items-start justify-between">
			<div>
				<a href="/customers" class="text-sm text-surface-500 hover:text-surface-300">← Kembali</a>
				<h1 class="mt-1 text-2xl font-bold text-surface-50">{customer.name}</h1>
				<span class="mt-1 inline-block rounded-full px-2 py-0.5 text-xs font-medium
					{customer.status === 'active' ? 'bg-success-500/20 text-success-400' : 'bg-surface-600 text-surface-400'}">
					{customer.status === 'active' ? 'Aktif' : 'Nonaktif'}
				</span>
			</div>
			<div class="flex gap-2">
				<button
					onclick={openNewOrderModal}
					class="rounded-md bg-success-600 px-4 py-2 text-sm font-semibold text-white hover:bg-success-500">
					+ Catat Pesanan
				</button>
				<button
					onclick={() => { showFaceModal = true; faceFile = null; facePreview = null; faceError = null; }}
					class="rounded-md bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-400">
					+ Tambah Wajah
				</button>
			</div>
		</div>

		<div class="grid gap-4 lg:grid-cols-2">
			<!-- Info dasar -->
			<div class="rounded-xl border border-surface-700 bg-surface-900 p-5">
				<h2 class="mb-4 font-semibold text-surface-200">Informasi</h2>
				<dl class="flex flex-col gap-3 text-sm">
					<div class="flex justify-between">
						<dt class="text-surface-400">Kontak</dt>
						<dd class="text-surface-100">{customer.contact ?? '—'}</dd>
					</div>
					<div class="flex flex-col gap-1.5">
						<dt class="text-surface-400">Preferensi</dt>
						{#if customer.preferences}
							<dd class="flex flex-wrap gap-1.5">
								{#each customer.preferences.split(',').map(p => p.trim()).filter(Boolean) as pref}
									{@const match = pref.match(/^(.*?)\s*x(\d+)$/i)}
									<span class="inline-flex items-center gap-1 rounded-md bg-surface-800 px-2 py-1 text-xs text-surface-200">
										{match ? match[1] : pref}
										{#if match}
											<span class="font-medium text-primary-400">x{match[2]}</span>
										{/if}
									</span>
								{/each}
							</dd>
						{:else}
							<dd class="text-surface-500 italic">Belum ada preferensi</dd>
						{/if}
					</div>
					<div class="flex justify-between">
						<dt class="text-surface-400">Catatan</dt>
						<dd class="text-surface-100">{customer.notes ?? '—'}</dd>
					</div>
					<div class="flex justify-between">
						<dt class="text-surface-400">Terdaftar</dt>
						<dd class="text-surface-100">{new Date(customer.created_at).toLocaleDateString('id-ID')}</dd>
					</div>
				</dl>
			</div>

			<!-- Data wajah -->
			<div class="rounded-xl border border-surface-700 bg-surface-900 p-5">
				<h2 class="mb-4 font-semibold text-surface-200">Data Wajah ({faces.length})</h2>
				{#if faces.length === 0}
					<div class="flex flex-col items-center justify-center gap-2 py-8 text-center">
						<i class="ti ti-face-id text-surface-600" style="font-size:32px" aria-hidden="true"></i>
						<p class="text-sm text-surface-500">Belum ada data wajah tersimpan.</p>
					</div>
				{:else}
					<div class="flex max-h-40 flex-col divide-y divide-surface-800 overflow-y-auto pr-1">
						{#each faces as face, i (face.id)}
							<div class="group relative flex items-center gap-3 py-2.5 first:pt-0 last:pb-0">
								<!-- Avatar bulat, bukan kotak -->
								<div class="flex size-10 shrink-0 items-center justify-center overflow-hidden rounded-full border border-surface-700 bg-surface-800">
									<i class="ti ti-face-id text-surface-500" style="font-size:18px" aria-hidden="true"></i>
								</div>

								<div class="min-w-0 flex-1">
									<p class="text-sm font-medium text-surface-100">Wajah #{i + 1}</p>
									<p class="text-xs text-surface-500">{new Date(face.created_at).toLocaleDateString('id-ID')}</p>
								</div>

								{#if confirmDeleteFaceId === face.id}
									<div class="flex items-center gap-1.5">
										<button onclick={() => (confirmDeleteFaceId = null)} class="rounded px-2 py-1 text-xs text-surface-300 hover:bg-surface-700">Batal</button>
										<button
											onclick={() => deleteFace(face.id)}
											disabled={deletingFaceId === face.id}
											class="rounded bg-error-700 px-2 py-1 text-xs text-white hover:bg-error-600 disabled:opacity-50"
										>
											{deletingFaceId === face.id ? '...' : 'Hapus'}
										</button>
									</div>
								{:else}
									<button
										onclick={() => (confirmDeleteFaceId = face.id)}
										class="rounded p-1.5 text-surface-500 opacity-0 hover:text-error-400 group-hover:opacity-100"
										aria-label="Hapus foto wajah #{i + 1}"
									>
										<i class="ti ti-trash" style="font-size:15px" aria-hidden="true"></i>
									</button>
								{/if}
							</div>
						{/each}
					</div>
				{/if}
			</div>
		</div>

		<!-- Riwayat kunjungan -->
		<div class="rounded-xl border border-surface-700 bg-surface-900 p-5">
			<h2 class="mb-4 font-semibold text-surface-200">Riwayat Kunjungan ({visits.length})</h2>
			{#if visits.length === 0}
				<p class="text-sm text-surface-500">Belum ada riwayat kunjungan.</p>
			{:else}
				<div class="overflow-hidden rounded-lg border border-surface-700">
					<table class="w-full text-sm">
						<thead class="bg-surface-800 text-left">
							<tr>
								<th class="px-4 py-2 font-medium text-surface-400">Waktu</th>
								<th class="px-4 py-2 font-medium text-surface-400">Pesanan</th>
								<th class="px-4 py-2 font-medium text-surface-400">Sumber</th>
								<th class="px-4 py-2 font-medium text-surface-400"></th>
							</tr>
						</thead>
						<tbody class="divide-y divide-surface-700">
							{#each visits as visit (visit.id)}
								<tr>
									<td class="px-4 py-2 text-surface-200">{new Date(visit.visited_at).toLocaleString('id-ID')}</td>
									<td class="px-4 py-3 align-top">
										{#if visit.order_note}
											<div class="flex flex-wrap gap-1.5">
												{#each visit.order_note.split(',').map(s => s.trim()).filter(Boolean) as item}
													{@const match = item.match(/^(.*?)\s*x(\d+)$/i)}
													<span class="inline-flex items-center gap-1 rounded-md bg-surface-800 px-2 py-1 text-xs text-surface-200">
														{match ? match[1] : item}
														{#if match}<span class="font-medium text-primary-400">×{match[2]}</span>{/if}
													</span>
												{/each}
											</div>
										{:else}
											<span class="text-surface-500">—</span>
										{/if}
									</td>
									<td class="px-4 py-2 text-surface-400">
										{#if visit.source === 'auto_recognition'}
											<div class="flex items-center gap-2">
												<i class="ti ti-camera text-primary-500 text-lg" aria-hidden="true"></i>
												<span>Auto</span>
											</div>
										{:else}
											<div class="flex items-center gap-2">
												<i class="ti ti-hand-click text-warning-500 text-lg" aria-hidden="true"></i>
												<span>Manual</span>
											</div>
										{/if}
									</td>
									<td class="px-4 py-2">
										<button onclick={() => openOrderModal(visit)} class="text-xs text-primary-400 hover:text-primary-300">
											{visit.order_note ? 'Edit' : 'Catat'}
										</button>
									</td>
								</tr>
							{/each}
						</tbody>
					</table>
				</div>
			{/if}
		</div>
	</div>
{/if}

<!-- Modal Tambah Wajah -->
{#if showFaceModal}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
		role="presentation"
		onclick={() => { if (!savingFace) showFaceModal = false; }}
		onkeydown={() => { if (!savingFace) showFaceModal = false; }}
	>
		<div
			class="w-full max-w-sm rounded-xl border border-surface-700 bg-surface-900 p-6 shadow-xl"
			role="dialog" aria-modal="true" aria-label="Tambah wajah" tabindex="-1"
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => e.stopPropagation()}
		>
			<h2 class="mb-1 text-lg font-semibold text-surface-50">Tambah Wajah</h2>
			<p class="mb-4 text-xs text-surface-400">Foto dari sudut berbeda meningkatkan akurasi deteksi</p>

			{#if !facePreview}
				<label class="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-surface-600 py-6 hover:border-primary-500">
					<i class="ti ti-camera-plus text-surface-500" style="font-size:32px" aria-hidden="true"></i>
					<span class="text-sm text-surface-400">Pilih foto wajah</span>
					<span class="text-xs text-surface-500">Depan, kiri 45°, kanan 45°</span>
					<input type="file" accept="image/*" onchange={handleFaceFile} class="hidden" />
				</label>
			{:else}
				<div class="overflow-hidden rounded-lg border border-surface-700">
					<img src={facePreview} alt="Preview" class="h-48 w-full object-cover" />
				</div>
				<button onclick={() => { faceFile = null; facePreview = null; }} class="mt-2 text-xs text-surface-400 hover:text-surface-200">
					Ganti foto
				</button>
			{/if}

			{#if faceError}
				<p class="mt-2 text-xs text-error-400">{faceError}</p>
			{/if}

			<div class="mt-4 flex gap-2">
				<button onclick={() => { showFaceModal = false; }} disabled={savingFace}
					class="flex-1 rounded-md border border-surface-600 px-4 py-2 text-sm text-surface-300 hover:bg-surface-800 disabled:opacity-50">
					Batal
				</button>
				<button onclick={saveFace} disabled={savingFace || !faceFile}
					class="flex-1 rounded-md bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-400 disabled:opacity-50">
					{savingFace ? 'Menyimpan...' : 'Simpan Wajah'}
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Modal Catat Pesanan — Menu Grid -->
{#if showOrderModal}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm"
		role="presentation"
		onclick={() => { if (!savingOrder) showOrderModal = false; }}
		onkeydown={() => { if (!savingOrder) showOrderModal = false; }}
	>
		<div
			class="flex h-[85vh] w-full max-w-2xl flex-col rounded-xl border border-surface-700 bg-surface-900 shadow-2xl"
			role="dialog" aria-modal="true" aria-label="Catat pesanan" tabindex="-1"
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => e.stopPropagation()}
		>
			<!-- Header -->
			<div class="flex items-center justify-between border-b border-surface-700 px-5 py-4">
				<div class="flex items-center gap-3">
					<div class="flex size-9 items-center justify-center rounded-full bg-primary-500/20 font-bold text-primary-300">
						{customer?.name.charAt(0).toUpperCase()}
					</div>
					<div>
						<p class="font-semibold text-surface-50">{customer?.name}</p>
						<p class="text-xs text-surface-500">Pilih menu pesanan</p>
					</div>
				</div>
				<button onclick={() => { showOrderModal = false; }} class="rounded p-1 text-surface-400 hover:text-surface-200" aria-label="Tutup">
					<i class="ti ti-x" style="font-size:18px" aria-hidden="true"></i>
				</button>
			</div>

			<!-- Saran dari preferensi -->
			{#if lastOrder}
				<div class="mx-5 mt-4 flex items-center gap-3 rounded-xl border border-success-600/30 bg-success-500/10 px-4 py-3">
					<div class="flex size-9 shrink-0 items-center justify-center rounded-full bg-success-500/20">
						<i class="ti ti-sparkles text-success-400" style="font-size:18px" aria-hidden="true"></i>
					</div>
					<div class="min-w-0 flex-1">
						<p class="text-[11px] font-medium uppercase tracking-wide text-success-500/80">Biasanya pesan</p>
						<p class="truncate text-sm font-semibold text-success-200">{lastOrder}</p>
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

								<div class="p-2.5">
									<p class="text-xs font-semibold text-surface-100 line-clamp-2 leading-tight">{item.name}</p>
									<p class="mt-1 text-xs font-bold text-primary-400">{formatPrice(item.price)}</p>

									<div class="mt-2 flex items-center justify-between">
										{#if qty === 0}
											<button onclick={() => addToCart(item.id)}
												class="w-full rounded-lg bg-primary-500 py-1.5 text-xs font-semibold text-white hover:bg-primary-400">
												+ Tambah
											</button>
										{:else}
											<div class="flex w-full items-center justify-between gap-1">
												<button onclick={() => removeFromCart(item.id)}
													class="flex size-7 items-center justify-center rounded-lg bg-surface-700 text-surface-200 hover:bg-surface-600"
													aria-label="Kurangi jumlah {item.name}">
													<i class="ti ti-minus" style="font-size:12px" aria-hidden="true"></i>
												</button>
												<span class="text-sm font-bold text-surface-50">{qty}</span>
												<button onclick={() => addToCart(item.id)}
													class="flex size-7 items-center justify-center rounded-lg bg-primary-500 text-white hover:bg-primary-400"
													aria-label="Tambah jumlah {item.name}">
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

			<!-- Footer -->
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
						<button onclick={saveOrder} disabled={savingOrder}
							class="rounded-lg bg-success-600 px-6 py-2.5 text-sm font-semibold text-white hover:bg-success-500 disabled:opacity-50">
							{savingOrder ? 'Menyimpan...' : 'Simpan Pesanan'}
						</button>
					</div>
				{:else}
					<p class="text-center text-xs text-surface-500">Pilih menu di atas untuk mencatat pesanan</p>
				{/if}
			</div>
		</div>
	</div>
{/if}