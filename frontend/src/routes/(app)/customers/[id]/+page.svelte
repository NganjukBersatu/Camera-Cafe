<script lang="ts">
	import { page } from '$app/state';
	import { api } from '$lib/api/client';
	import type { Customer, Visit, CustomerFace } from '$lib/types';

	const customerId = $derived(page.params['id'] as string);

	let customer = $state<Customer | null>(null);
	let visits = $state<Visit[]>([]);
	let faces = $state<CustomerFace[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Modal state
	let showOrderModal = $state(false);
	let selectedVisit = $state<Visit | null>(null);
	let orderInput = $state('');
	let savingOrder = $state(false);

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

	$effect(() => {
		void load();
	});

	async function deleteFace(faceId: string): Promise<void> {
		if (!confirm('Hapus data wajah ini? Tindakan tidak dapat dibatalkan.')) return;
		try {
			await api.customers.deleteFace(customerId, faceId);
			faces = faces.filter((f) => f.id !== faceId);
		} catch (e) {
			alert(e instanceof Error ? e.message : 'Gagal menghapus data wajah');
		}
	}

	// Ambil pesanan terakhir dari riwayat kunjungan
	const lastOrder = $derived(customer?.preferences ?? null);

	function openOrderModal(visit: Visit): void {
		selectedVisit = visit;
		orderInput = visit.order_note ?? '';
		showOrderModal = true;
	}

	function openNewOrderModal(): void {
		// Pakai kunjungan terbaru
		const latest = visits[0] ?? null;
		selectedVisit = latest;
		orderInput = lastOrder ?? '';
		showOrderModal = true;
	}

	async function saveOrder(): Promise<void> {
		if (!selectedVisit || !orderInput.trim()) return;
		savingOrder = true;
		try {
			await api.visits.updateOrder(selectedVisit.id, orderInput.trim());
			visits = visits.map((v) =>
				v.id === selectedVisit!.id ? { ...v, order_note: orderInput.trim() } : v
			);
			if (customer) customer = { ...customer, preferences: orderInput.trim() };
			showOrderModal = false;
		} catch (e) {
			alert('Gagal menyimpan pesanan');
		} finally {
			savingOrder = false;
		}
	}
</script>

<svelte:head><title>{customer?.name ?? 'Pelanggan'} — Camera Cafe CRM</title></svelte:head>

{#if loading}
	<div class="flex items-center justify-center py-20 text-surface-400">Memuat...</div>

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
				<span class="rounded-full px-2 py-0.5 text-xs font-medium
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
				<a href="/enrollment?customer_id={customer.id}" class="rounded-md bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-400">
					+ Tambah Wajah
				</a>
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
					<div class="flex justify-between">
						<dt class="text-surface-400">Preferensi</dt>
						<dd class="text-surface-100">{customer.preferences ?? '—'}</dd>
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
					<p class="text-sm text-surface-500">Belum ada data wajah tersimpan.</p>
				{:else}
					<div class="flex flex-col gap-2">
						{#each faces as face (face.id)}
							<div class="flex items-center justify-between rounded-md bg-surface-800 px-3 py-2 text-sm">
								<span class="text-surface-300">{new Date(face.created_at).toLocaleDateString('id-ID')}</span>
								<button onclick={() => deleteFace(face.id)} class="text-error-400 hover:text-error-300">Hapus</button>
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
									<td class="px-4 py-2 text-surface-200">
										{new Date(visit.visited_at).toLocaleString('id-ID')}
									</td>
									<td class="px-4 py-2 text-surface-100">
										{visit.order_note ?? '—'}
									</td>
									<td class="px-4 py-2 text-surface-400">
										{visit.source === 'auto_recognition' ? '🎥 Auto' : '✋ Manual'}
									</td>
									<td class="px-4 py-2">
										<button
											onclick={() => openOrderModal(visit)}
											class="text-xs text-primary-400 hover:text-primary-300">
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

<!-- Modal Catat Pesanan -->
{#if showOrderModal}
	<div class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm">
		<div class="w-full max-w-sm rounded-xl border border-surface-700 bg-surface-900 p-6 shadow-xl">
			<h2 class="mb-4 text-lg font-semibold text-surface-50">Catat Pesanan — {customer?.name}</h2>

			{#if lastOrder}
				<button
					onclick={() => { orderInput = lastOrder; }}
					class="mb-4 w-full rounded-lg bg-success-600/20 border border-success-600/40 px-4 py-3 text-left text-sm font-medium text-success-300 hover:bg-success-600/30">
					✓ Pesan seperti biasanya: {lastOrder}
				</button>
			{/if}

			<label class="mb-1 block text-xs text-surface-400">Atau ketik pesanan:</label>
			<input
				type="text"
				bind:value={orderInput}
				placeholder="contoh: Kopi Susu, Es Teh..."
				class="w-full rounded-md border border-surface-600 bg-surface-800 px-3 py-2 text-sm text-surface-100 placeholder-surface-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
			/>

			<div class="mt-4 flex gap-2">
				<button
					onclick={() => { showOrderModal = false; }}
					class="flex-1 rounded-md border border-surface-600 px-4 py-2 text-sm text-surface-300 hover:bg-surface-800">
					Batal
				</button>
				<button
					onclick={saveOrder}
					disabled={savingOrder || !orderInput.trim()}
					class="flex-1 rounded-md bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-400 disabled:opacity-50">
					{savingOrder ? 'Menyimpan...' : 'Simpan'}
				</button>
			</div>
		</div>
	</div>
{/if}