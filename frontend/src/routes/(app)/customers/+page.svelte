<script lang="ts">
	import { api } from '$lib/api/client';
	import type { Customer, CustomerStatus } from '$lib/types';

	let search = $state('');
	let statusFilter = $state<CustomerStatus | 'all'>('all');
	let customers = $state<Customer[]>([]);
	let total = $state(0);
	let loading = $state(true);
	let error = $state<string | null>(null);

	let timer: ReturnType<typeof setTimeout>;
	let initialized = false;

	async function load(): Promise<void> {
		loading = true;
		error = null;

		try {
			const res = await api.customers.list({
				search: search || undefined,
				status: statusFilter !== 'all' ? statusFilter : undefined
			});

			customers = res.items;
			total = res.total;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Gagal memuat data';
		} finally {
			loading = false;
		}
	}

	$effect(() => {
		search;
		statusFilter;

		if (!initialized) {
			initialized = true;
			void load();
			return;
		}

		clearTimeout(timer);

		timer = setTimeout(() => {
			void load();
		}, 300);

		return () => clearTimeout(timer);
	});
</script>

<svelte:head><title>Pelanggan — Camera Cafe CRM</title></svelte:head>

<div class="flex flex-col gap-6">
	<div class="flex items-center justify-between">
		<h1 class="text-2xl font-bold text-surface-50">Pelanggan</h1>
		<a href="/enrollment" class="rounded-md bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-400">
			+ Enrollment Baru
		</a>
	</div>

	<!-- Filter -->
	<div class="flex gap-3">
		<input
			type="search"
			placeholder="Cari nama atau kontak..."
			bind:value={search}
			class="flex-1 rounded-md border border-surface-600 bg-surface-800 px-3 py-2 text-sm text-surface-50 placeholder:text-surface-500 focus:border-primary-500 focus:outline-none"
		/>
		<select
			bind:value={statusFilter}
			class="rounded-md border border-surface-600 bg-surface-800 px-3 py-2 text-sm text-surface-50 focus:border-primary-500 focus:outline-none"
		>
			<option value="all">Semua status</option>
			<option value="active">Aktif</option>
			<option value="inactive">Nonaktif</option>
		</select>
	</div>

	<!-- State: loading -->
	{#if loading}
		<div class="flex items-center justify-center py-20 text-surface-400">
			<p>Memuat data...</p>
		</div>

	<!-- State: error -->
	{:else if error}
		<div class="rounded-xl border border-error-800 bg-error-900/20 p-6 text-center">
			<p class="font-semibold text-error-400">Gagal memuat data</p>
			<p class="mt-1 text-sm text-surface-400">{error}</p>
			<button onclick={load} class="mt-4 rounded-md bg-surface-700 px-4 py-2 text-sm text-surface-200 hover:bg-surface-600">
				Coba lagi
			</button>
		</div>

	<!-- State: empty -->
	{:else if customers.length === 0}
		<div class="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-surface-700 py-20 text-center">
			<p class="text-4xl">👤</p>
			<p class="font-semibold text-surface-300">Belum ada pelanggan</p>
			<a href="/enrollment" class="text-sm text-primary-400 hover:underline">Daftarkan pelanggan pertama →</a>
		</div>

	<!-- State: data -->
	{:else}
		<div class="overflow-hidden rounded-xl border border-surface-700">
			<table class="w-full text-sm">
				<thead class="bg-surface-800 text-left">
					<tr>
						<th class="px-4 py-3 font-semibold text-surface-300">Nama</th>
						<th class="px-4 py-3 font-semibold text-surface-300">Kontak</th>
						<th class="px-4 py-3 font-semibold text-surface-300">Wajah</th>
						<th class="px-4 py-3 font-semibold text-surface-300">Status</th>
						<th class="px-4 py-3"></th>
					</tr>
				</thead>
				<tbody class="divide-y divide-surface-700">
					{#each customers as customer (customer.id)}
						<tr class="bg-surface-900 hover:bg-surface-800">
							<td class="px-4 py-3 font-medium text-surface-100">{customer.name}</td>
							<td class="px-4 py-3 text-surface-400">{customer.contact ?? '—'}</td>
							<td class="px-4 py-3 text-surface-400">{customer.face_count}</td>
							<td class="px-4 py-3">
								<span class="rounded-full px-2 py-0.5 text-xs font-medium
									{customer.status === 'active' ? 'bg-success-500/20 text-success-400' : 'bg-surface-600 text-surface-400'}">
									{customer.status === 'active' ? 'Aktif' : 'Nonaktif'}
								</span>
							</td>
							<td class="px-4 py-3">
								<a href="/customers/{customer.id}" class="text-primary-400 hover:underline">Detail →</a>
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		<p class="text-xs text-surface-500">{total} pelanggan ditemukan</p>
	{/if}
</div>
