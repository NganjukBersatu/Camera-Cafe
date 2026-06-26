<script lang="ts">
	import { api } from '$lib/api/client';
	import type { Visit } from '$lib/types';
	import { onMount } from 'svelte';

	let visits = $state<Visit[]>([]);
	let total = $state(0);
	let loading = $state(true);
	let error = $state<string | null>(null);
	let dateFrom = $state('');
	let dateTo = $state('');
	let page = $state(1);
	const size = 20;

	let totalPages = $derived(Math.ceil(total / size));

	async function load(): Promise<void> {
		loading = true;
		error = null;
		try {
			const res = await api.visits.list({
				date_from: dateFrom || undefined,
				date_to: dateTo || undefined,
				page
			});
			visits = res.items;
			total = res.total;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Gagal memuat data';
		} finally {
			loading = false;
		}
	}

	function applyFilter(): void {
		page = 1;
		void load();
	}

	function goToPage(p: number): void {
		if (p < 1 || p > totalPages) return;
		page = p;
		void load();
	}

	// Buat array halaman yang ditampilkan (maks 5 halaman di sekitar halaman aktif)
	function getPageNumbers(): (number | '...')[] {
		if (totalPages <= 7) return Array.from({ length: totalPages }, (_, i) => i + 1);
		const pages: (number | '...')[] = [1];
		if (page > 3) pages.push('...');
		for (let i = Math.max(2, page - 1); i <= Math.min(totalPages - 1, page + 1); i++) {
			pages.push(i);
		}
		if (page < totalPages - 2) pages.push('...');
		pages.push(totalPages);
		return pages;
	}

	onMount(() => {
		void load();
	});
</script>

<svelte:head><title>Kunjungan — Camera Cafe CRM</title></svelte:head>

<div class="flex flex-col gap-6">
	<h1 class="text-2xl font-bold text-surface-50">Riwayat Kunjungan</h1>

	<!-- Filter tanggal -->
	<div class="flex gap-3">
		<div class="flex flex-col gap-1">
			<label for="date-from" class="text-xs text-surface-400">Dari tanggal</label>
			<input
				id="date-from"
				type="date"
				bind:value={dateFrom}
				class="rounded-md border border-surface-600 bg-surface-800 px-3 py-2 text-sm text-surface-50 focus:border-primary-500 focus:outline-none"
			/>
		</div>
		<div class="flex flex-col gap-1">
			<label for="date-to" class="text-xs text-surface-400">Sampai tanggal</label>
			<input
				id="date-to"
				type="date"
				bind:value={dateTo}
				class="rounded-md border border-surface-600 bg-surface-800 px-3 py-2 text-sm text-surface-50 focus:border-primary-500 focus:outline-none"
			/>
		</div>
		<div class="flex items-end">
			<button onclick={applyFilter} class="rounded-md bg-surface-700 px-4 py-2 text-sm text-surface-200 hover:bg-surface-600">
				Filter
			</button>
		</div>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-20 text-surface-400">
			<i class="ti ti-loader-2 animate-spin mr-2" aria-hidden="true"></i>
			Memuat...
		</div>

	{:else if error}
		<div class="rounded-xl border border-error-800 bg-error-900/20 p-6 text-center">
			<p class="font-semibold text-error-400">Gagal memuat data</p>
			<p class="mt-1 text-sm text-surface-400">{error}</p>
			<button onclick={load} class="mt-4 rounded-md bg-surface-700 px-4 py-2 text-sm text-surface-200">Coba lagi</button>
		</div>

	{:else if visits.length === 0}
		<div class="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-surface-700 py-20 text-center">
			<i class="ti ti-history-off text-surface-500" style="font-size: 32px" aria-hidden="true"></i>
			<p class="font-semibold text-surface-300">Belum ada kunjungan</p>
			<p class="text-sm text-surface-500">Kunjungan dicatat otomatis saat pelanggan terdeteksi kamera.</p>
		</div>

	{:else}
		<div class="overflow-hidden rounded-xl border border-surface-700">
			<table class="w-full text-sm">
				<thead class="bg-surface-800 text-left">
					<tr>
						<th class="px-4 py-3 font-semibold text-surface-300">Waktu</th>
						<th class="px-4 py-3 font-semibold text-surface-300">Pelanggan</th>
						<th class="px-4 py-3 font-semibold text-surface-300">Sumber</th>
					</tr>
				</thead>
				<tbody class="divide-y divide-surface-700">
					{#each visits as visit (visit.id)}
						<tr class="bg-surface-900 hover:bg-surface-800">
							<td class="px-4 py-3 text-surface-300">
								{new Date(visit.visited_at).toLocaleString('id-ID')}
							</td>
							<td class="px-4 py-3">
								<a href="/customers/{visit.customer_id}" class="font-medium text-primary-400 hover:underline">
									{visit.customer_name ?? 'Pelanggan'}
								</a>
							</td>
							<td class="px-4 py-3 text-surface-400">
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
						</tr>
					{/each}
				</tbody>
			</table>
		</div>

		<!-- Footer: info + pagination -->
		<div class="flex items-center justify-between">
			<p class="text-xs text-surface-500">
				Menampilkan {(page - 1) * size + 1}–{Math.min(page * size, total)} dari {total} kunjungan
			</p>

			{#if totalPages > 1}
				<div class="flex items-center gap-1">
					<!-- Prev -->
					<button
						onclick={() => goToPage(page - 1)}
						disabled={page === 1}
						class="flex size-8 items-center justify-center rounded-md text-surface-400 hover:bg-surface-700 hover:text-surface-100 disabled:cursor-not-allowed disabled:opacity-30"
						aria-label="Halaman sebelumnya"
					>
						<i class="ti ti-chevron-left" aria-hidden="true"></i>
					</button>

					<!-- Nomor halaman -->
					{#each getPageNumbers() as p}
						{#if p === '...'}
							<span class="flex size-8 items-center justify-center text-xs text-surface-500">…</span>
						{:else}
							<button
								onclick={() => goToPage(p)}
								class="flex size-8 items-center justify-center rounded-md text-xs font-medium transition-colors
									{page === p
										? 'bg-primary-500 text-white'
										: 'text-surface-400 hover:bg-surface-700 hover:text-surface-100'}"
							>
								{p}
							</button>
						{/if}
					{/each}

					<!-- Next -->
					<button
						onclick={() => goToPage(page + 1)}
						disabled={page === totalPages}
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