<script lang="ts">
	import { api } from '$lib/api/client';
	import type { Customer, CustomerStatus } from '$lib/types';

	let search = $state('');
	let statusFilter = $state<CustomerStatus | 'all'>('all');
	let customers = $state<Customer[]>([]);
	let total = $state(0);
	let loading = $state(true);
	let error = $state<string | null>(null);

	let deleteTarget = $state<Customer | null>(null);
	let openMenuId = $state<string | null>(null);
	let deleting = $state(false);
	let deleteSuccess = $state<string | null>(null);

	let currentPage = $state(1);
	const size = 20;

	let totalPages = $derived(Math.ceil(total / size));

	let timer: ReturnType<typeof setTimeout>;
	let initialized = false;

	async function load(): Promise<void> {
		loading = true;
		error = null;

		try {
			const res = await api.customers.list({
				search: search || undefined,
				status: statusFilter !== 'all' ? statusFilter : undefined,
				page: currentPage
			});

			customers = res.items;
			total = res.total;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Gagal memuat data';
		} finally {
			loading = false;
		}
	}

	function goToPage(p: number): void {
		if (p < 1 || p > totalPages) return;
		currentPage = p;
		void load();
	}

	function getPageNumbers(): (number | '...')[] {
		if (totalPages <= 7) return Array.from({ length: totalPages }, (_, i) => i + 1);
		const pages: (number | '...')[] = [1];
		if (currentPage > 3) pages.push('...');
		for (let i = Math.max(2, currentPage - 1); i <= Math.min(totalPages - 1, currentPage + 1); i++) {
			pages.push(i);
		}
		if (currentPage < totalPages - 2) pages.push('...');
		pages.push(totalPages);
		return pages;
	}

	function toggleMenu(id: string) {
		openMenuId = openMenuId === id ? null : id;
	}

	async function deleteCustomer() {
		if (!deleteTarget) return;
		deleting = true;

		try {
			await api.customers.delete(deleteTarget.id);
			const name = deleteTarget.name;
			deleteTarget = null;
			await load();
			deleteSuccess = `${name} berhasil dihapus`;
			setTimeout(() => (deleteSuccess = null), 3000);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Gagal menghapus pelanggan';
			deleteTarget = null;
		} finally {
			deleting = false;
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
			currentPage = 1;
			void load();
		}, 300);

		return () => clearTimeout(timer);
	});
</script>

<svelte:head><title>Pelanggan — Camera Cafe CRM</title></svelte:head>

<svelte:window onclick={() => (openMenuId = null)} />

<div class="flex flex-col gap-6">
	<div class="flex items-center justify-between">
		<h1 class="text-2xl font-bold text-surface-50">Pelanggan</h1>
		<a href="/enrollment" class="rounded-md bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-400">
			+ Enrollment Baru
		</a>
	</div>

	<!-- Toast sukses hapus -->
	{#if deleteSuccess}
		<div class="flex items-center gap-2 rounded-lg border border-success-700 bg-success-900/30 px-4 py-3 text-sm text-success-400">
			<i class="ti ti-circle-check" aria-hidden="true"></i>
			<span>{deleteSuccess}</span>
		</div>
	{/if}

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
		<div class="flex items-center justify-center gap-2 py-20 text-surface-400">
			<i class="ti ti-loader-2 animate-spin" aria-hidden="true"></i>
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
			<i class="ti ti-users-off text-surface-500" style="font-size:32px" aria-hidden="true"></i>
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
						<th class="px-4 py-3 font-semibold text-surface-300">Aksi</th>
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
							<td class="relative px-4 py-3">
								<button
									onclick={(e) => { e.stopPropagation(); toggleMenu(customer.id); }}
									class="rounded p-1 text-surface-400 hover:bg-surface-700 hover:text-surface-100"
									aria-label="Aksi"
								>
									<i class="ti ti-dots-vertical" aria-hidden="true"></i>
								</button>

								{#if openMenuId === customer.id}
									<div class="absolute right-4 top-10 z-10 w-36 rounded-lg border border-surface-600 bg-surface-800 py-1 shadow-lg">
										<a
											href="/customers/{customer.id}"
											class="flex items-center gap-2 px-3 py-2 text-sm text-surface-200 hover:bg-surface-700"
										>
											<i class="ti ti-eye" aria-hidden="true"></i> Lihat detail
										</a>
										<hr class="border-surface-700" />
										<button
											onclick={() => { deleteTarget = customer; openMenuId = null; }}
											class="flex w-full items-center gap-2 px-3 py-2 text-sm text-error-400 hover:bg-error-900/30"
										>
											<i class="ti ti-trash" aria-hidden="true"></i> Hapus
										</button>
									</div>
								{/if}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>

		<!-- Footer: info + pagination -->
		<div class="flex items-center justify-between">
			<p class="text-xs text-surface-500">
				Menampilkan {(currentPage - 1) * size + 1}–{Math.min(currentPage * size, total)} dari {total} pelanggan
			</p>

			{#if totalPages > 1}
				<div class="flex items-center gap-1">
					<button
						onclick={() => goToPage(currentPage - 1)}
						disabled={currentPage === 1}
						class="flex size-8 items-center justify-center rounded-md text-surface-400 hover:bg-surface-700 hover:text-surface-100 disabled:cursor-not-allowed disabled:opacity-30"
						aria-label="Halaman sebelumnya"
					>
						<i class="ti ti-chevron-left" aria-hidden="true"></i>
					</button>

					{#each getPageNumbers() as p}
						{#if p === '...'}
							<span class="flex size-8 items-center justify-center text-xs text-surface-500">…</span>
						{:else}
							<button
								onclick={() => goToPage(p)}
								class="flex size-8 items-center justify-center rounded-md text-xs font-medium transition-colors
									{currentPage === p
										? 'bg-primary-500 text-white'
										: 'text-surface-400 hover:bg-surface-700 hover:text-surface-100'}"
							>
								{p}
							</button>
						{/if}
					{/each}

					<button
						onclick={() => goToPage(currentPage + 1)}
						disabled={currentPage === totalPages}
						class="flex size-8 items-center justify-center rounded-md text-surface-400 hover:bg-surface-700 hover:text-surface-100 disabled:cursor-not-allowed disabled:opacity-30"
						aria-label="Halaman berikutnya"
					>
						<i class="ti ti-chevron-right" aria-hidden="true"></i>
					</button>
				</div>
			{/if}
		</div>
	{/if}
</div>

<!-- Modal konfirmasi hapus -->
{#if deleteTarget}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/60"
		role="presentation"
		onclick={() => { if (!deleting) deleteTarget = null; }}
		onkeydown={() => { if (!deleting) deleteTarget = null; }}
	>
		<div
			class="w-80 rounded-xl border border-surface-700 bg-surface-900 p-6"
			role="dialog"
			aria-modal="true"
			aria-label="Konfirmasi hapus"
			tabindex="-1"
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => e.stopPropagation()}
		>
			<p class="font-semibold text-surface-50">Hapus pelanggan?</p>
			<p class="mt-1 text-sm text-surface-400">
				<span class="font-medium text-surface-200">{deleteTarget.name}</span>
				akan dihapus permanen beserta seluruh data wajah dan riwayat kunjungannya.
			</p>
			<div class="mt-5 flex justify-end gap-2">
				<button
					onclick={() => (deleteTarget = null)}
					disabled={deleting}
					class="rounded-md border border-surface-600 px-3 py-1.5 text-sm text-surface-300 hover:bg-surface-700 disabled:opacity-50"
				>
					Batal
				</button>
				<button
					onclick={deleteCustomer}
					disabled={deleting}
					class="flex items-center gap-2 rounded-md bg-error-700 px-3 py-1.5 text-sm text-white hover:bg-error-600 disabled:opacity-50"
				>
					{#if deleting}
						<span class="inline-block h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
						Menghapus...
					{:else}
						<i class="ti ti-trash" aria-hidden="true"></i> Hapus
					{/if}
				</button>
			</div>
		</div>
	</div>
{/if}