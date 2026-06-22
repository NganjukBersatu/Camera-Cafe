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

	async function load(): Promise<void> {
		loading = true;
		error = null;
		try {
			const res = await api.visits.list({
				date_from: dateFrom || undefined,
				date_to: dateTo || undefined
			});
			visits = res.items;
			total = res.total;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Gagal memuat data';
		} finally {
			loading = false;
		}
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
			<button onclick={load} class="rounded-md bg-surface-700 px-4 py-2 text-sm text-surface-200 hover:bg-surface-600">
				Filter
			</button>
		</div>
	</div>

	{#if loading}
		<div class="flex items-center justify-center py-20 text-surface-400">Memuat...</div>

	{:else if error}
		<div class="rounded-xl border border-error-800 bg-error-900/20 p-6 text-center">
			<p class="font-semibold text-error-400">Gagal memuat data</p>
			<p class="mt-1 text-sm text-surface-400">{error}</p>
			<button onclick={load} class="mt-4 rounded-md bg-surface-700 px-4 py-2 text-sm text-surface-200">Coba lagi</button>
		</div>

	{:else if visits.length === 0}
		<div class="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-surface-700 py-20 text-center">
			<p class="text-4xl">📋</p>
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
								{visit.source === 'auto_recognition' ? '🎥 Auto' : '✋ Manual'}
							</td>
						</tr>
					{/each}
				</tbody>
			</table>
		</div>
		<p class="text-xs text-surface-500">{total} kunjungan ditemukan</p>
	{/if}
</div>
