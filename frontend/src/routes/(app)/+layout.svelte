<script lang="ts">
	import { page } from '$app/state';
	import NotificationQueue from '$lib/components/NotificationQueue.svelte';
	import StatusStrip from '$lib/components/StatusStrip.svelte';

	let { children } = $props();

	const navItems = [
		{ href: '/dashboard', label: 'Dashboard', icon: 'ti-layout-dashboard' },
		{ href: '/customers', label: 'Pelanggan', icon: 'ti-user' },
		{ href: '/enrollment', label: 'Enrollment', icon: 'ti-user-plus' },
		{ href: '/visits', label: 'Kunjungan', icon: 'ti-calendar-stats' }
	] as const;
</script>

<div class="flex h-screen overflow-hidden bg-surface-950 text-surface-50">
	<!-- Sidebar -->
	<aside class="flex w-56 flex-col border-r border-surface-700 bg-surface-900">
		<div class="border-b border-surface-700 px-4 py-5">
			<div class="flex items-center gap-2.5">
				<div class="flex size-8 items-center justify-center rounded-lg bg-primary-500/20">
					<i class="ti ti-camera text-primary-400" style="font-size:18px" aria-hidden="true"></i>
				</div>
				<div>
					<p class="text-sm font-bold text-surface-50 leading-none">Camera Cafe</p>
					<p class="text-xs text-primary-400 font-semibold tracking-wider mt-0.5">CRM</p>
				</div>
			</div>
		</div>

		<nav class="flex flex-col gap-1 p-2">
			{#each navItems as item}
				<a
					href={item.href}
					class="flex items-center gap-3 rounded-md px-3 py-2 text-sm transition-colors
						{page.url.pathname.startsWith(item.href)
						? 'bg-primary-500/20 font-semibold text-primary-300'
						: 'text-surface-300 hover:bg-surface-700 hover:text-surface-50'}"
				>
					<span>
						<i class="ti {item.icon}" aria-hidden="true"></i>
					</span>
					<span>{item.label}</span>
				</a>
			{/each}
		</nav>

		<div class="mt-auto p-2">
			<StatusStrip />
		</div>
	</aside>

	<!-- Main content -->
	<main class="flex flex-1 flex-col overflow-hidden">
		<div class="flex-1 overflow-y-auto p-6">
			{@render children()}
		</div>
	</main>
</div>
