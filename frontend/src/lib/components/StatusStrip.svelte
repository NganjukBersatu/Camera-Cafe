<script lang="ts">
	import { systemHealth, wsConnected } from '$lib/stores/systemHealth';
	import type { ServiceStatus } from '$lib/types';

	function dot(status: ServiceStatus): string {
		if (status === 'ok') return 'bg-success-500';
		if (status === 'error') return 'bg-error-500';
		return 'bg-surface-500';
	}
</script>

<div class="rounded-md border border-surface-700 bg-surface-800 p-3">
	<p class="mb-2 text-xs font-semibold uppercase tracking-widest text-surface-400">Status</p>

	<div class="flex flex-col gap-1.5">
		<div class="flex items-center justify-between text-xs">
			<span class="text-surface-300">WebSocket</span>
			<span class="size-2 rounded-full {$wsConnected ? 'bg-success-500' : 'bg-error-500'}"></span>
		</div>
		{#each Object.entries($systemHealth) as [service, status]}
			<div class="flex items-center justify-between text-xs">
				<span class="text-surface-300 capitalize">{service}</span>
				<span class="size-2 rounded-full {dot(status)}"></span>
			</div>
		{/each}
	</div>
</div>
