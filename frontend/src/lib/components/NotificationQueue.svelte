<script lang="ts">
	import { activeNotifications, notifications } from '$lib/stores/notifications';
	import type { Notification } from '$lib/types';

	function timeAgo(ts: number): string {
		const diff = Math.floor((Date.now() - ts) / 1000);
		if (diff < 60) return 'Baru saja';
		const minutes = Math.floor(diff / 60);
		if (minutes < 60) {
			return `${minutes} menit lalu`;
		}
		const hours = Math.floor(minutes / 60);
		if (hours < 24) {
			return `${hours} jam lalu`;
		}
		return `${Math.floor(hours / 24)} hari lalu`;
	}

	function confidence(similarity: number): string {
		if (similarity >= 0.8) return 'text-success-400';
		if (similarity >= 0.6) return 'text-warning-400';
		return 'text-error-400';
	}
</script>

<div class="pointer-events-none fixed right-4 top-4 z-50 flex w-80 flex-col gap-2">
	{#each $activeNotifications.slice(0, 5) as notif (notif.id)}
		<div
			class="pointer-events-auto rounded-lg border border-surface-700 bg-surface-900 p-4 shadow-xl"
		>
			<div class="flex items-start justify-between gap-2">
				<div class="min-w-0 flex-1">
					<p class="truncate font-semibold text-surface-50">{notif.payload.customer_name}</p>
					{#if notif.payload.preferences}
						<p class="mt-0.5 truncate text-xs text-surface-400">
							{notif.payload.preferences}
						</p>
					{/if}
					<div class="mt-1.5 flex items-center gap-2">
						<span class="text-xs {confidence(notif.payload.similarity)}">
							{Math.round(notif.payload.similarity * 100)}% 
						</span>
						<span class="text-xs text-surface-500">{timeAgo(notif.received_at)}</span>
					</div>
				</div>
				<button
					onclick={() => notifications.dismiss(notif.id)}
					class="shrink-0 text-surface-400 hover:text-surface-200"
					aria-label="Tutup notifikasi"
				>
					✕
				</button>
			</div>

			<div class="mt-3 flex gap-2">
				<a
					href="/customers/{notif.payload.customer_id}"
					onclick={() => notifications.dismiss(notif.id)}
					class="flex-1 rounded bg-primary-500/20 py-1.5 text-center text-xs font-medium text-primary-300 hover:bg-primary-500/30"
				>
					Lihat Profil
				</a>
				<button
					onclick={() => notifications.dismiss(notif.id)}
					class="flex-1 rounded bg-surface-700 py-1.5 text-xs font-medium text-surface-300 hover:bg-surface-600"
				>
					Abaikan
				</button>
			</div>
		</div>
	{/each}
</div>
