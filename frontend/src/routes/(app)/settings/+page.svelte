<script lang="ts">
	import { api } from '$lib/api/client';
	import type { MenuItem } from '$lib/types';

	let menuItems = $state<MenuItem[]>([]);
	let loading = $state(true);
	let error = $state<string | null>(null);

	// Modal tambah/edit
	let showModal = $state(false);
	let editTarget = $state<MenuItem | null>(null);
	let saving = $state(false);
	let formError = $state<string | null>(null);

	// Form fields
	let formName = $state('');
	let formPrice = $state('');
	let formCategory = $state('');
	let formDescription = $state('');
	let formAvailable = $state(true);

	// Upload gambar
	let imageFile = $state<File | null>(null);
	let imagePreview = $state<string | null>(null);
	let uploadingImage = $state(false);

	// Konfirmasi hapus
	let deleteTarget = $state<MenuItem | null>(null);
	let deleting = $state(false);

	// Kategori unik
	let categories = $derived([...new Set(menuItems.map(m => m.category).filter(Boolean))]);

	async function load(): Promise<void> {
		loading = true;
		error = null;
		try {
			const res = await api.menu.list();
			menuItems = res.items;
		} catch (e) {
			error = e instanceof Error ? e.message : 'Gagal memuat menu';
		} finally {
			loading = false;
		}
	}

	function openAddModal(): void {
		editTarget = null;
		formName = '';
		formPrice = '';
		formCategory = '';
		formDescription = '';
		formAvailable = true;
		imageFile = null;
		imagePreview = null;
		formError = null;
		showModal = true;
	}

	function openEditModal(item: MenuItem): void {
		editTarget = item;
		formName = item.name;
		formPrice = String(item.price);
		formCategory = item.category ?? '';
		formDescription = item.description ?? '';
		formAvailable = item.is_available;
		imageFile = null;
		imagePreview = item.image_url;
		formError = null;
		showModal = true;
	}

	function handleImageSelect(e: Event): void {
		const input = e.target as HTMLInputElement;
		const file = input.files?.[0];
		if (!file) return;
		imageFile = file;
		imagePreview = URL.createObjectURL(file);
	}

	async function save(): Promise<void> {
		if (!formName.trim() || !formPrice) return;
		saving = true;
		formError = null;
		try {
			const body = {
				name: formName.trim(),
				price: parseFloat(formPrice),
				category: formCategory.trim() || null,
				description: formDescription.trim() || null,
				is_available: formAvailable,
			};

			let saved: MenuItem;
			if (editTarget) {
				saved = await api.menu.update(editTarget.id, body);
			} else {
				saved = await api.menu.create(body);
			}

			// Upload gambar jika ada
			if (imageFile) {
				uploadingImage = true;
				saved = await api.menu.uploadImage(saved.id, imageFile);
				uploadingImage = false;
			}

			showModal = false;
			await load();
		} catch (e) {
			formError = e instanceof Error ? e.message : 'Gagal menyimpan menu';
		} finally {
			saving = false;
			uploadingImage = false;
		}
	}

	async function deleteItem(): Promise<void> {
		if (!deleteTarget) return;
		deleting = true;
		try {
			await api.menu.delete(deleteTarget.id);
			deleteTarget = null;
			await load();
		} catch (e) {
			alert('Gagal menghapus menu');
		} finally {
			deleting = false;
		}
	}

	$effect(() => {
		void load();
	});

	function formatPrice(price: number): string {
		return new Intl.NumberFormat('id-ID', { style: 'currency', currency: 'IDR', minimumFractionDigits: 0 }).format(price);
	}
</script>

<svelte:head><title>Settings — Camera Cafe CRM</title></svelte:head>

<div class="flex flex-col gap-6">
	<div class="flex items-center justify-between">
		<div>
			<h1 class="text-2xl font-bold text-surface-50">Settings</h1>
			<p class="text-sm text-surface-400">Kelola daftar menu kafe</p>
		</div>
		<button
			onclick={openAddModal}
			class="rounded-md bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-400"
		>
			+ Tambah Menu
		</button>
	</div>

	{#if loading}
		<div class="flex items-center justify-center gap-2 py-20 text-surface-400">
			<i class="ti ti-loader-2 animate-spin" aria-hidden="true"></i>
			<p>Memuat menu...</p>
		</div>

	{:else if error}
		<div class="rounded-xl border border-error-800 bg-error-900/20 p-6 text-center">
			<p class="font-semibold text-error-400">Gagal memuat data</p>
			<p class="mt-1 text-sm text-surface-400">{error}</p>
			<button onclick={load} class="mt-4 rounded-md bg-surface-700 px-4 py-2 text-sm text-surface-200">Coba lagi</button>
		</div>

	{:else if menuItems.length === 0}
		<div class="flex flex-col items-center justify-center gap-3 rounded-xl border border-dashed border-surface-700 py-20 text-center">
			<i class="ti ti-tools-kitchen-2 text-surface-500" style="font-size:32px" aria-hidden="true"></i>
			<p class="font-semibold text-surface-300">Belum ada menu</p>
			<p class="text-sm text-surface-500">Tambah menu untuk mempermudah kasir saat mencatat pesanan.</p>
			<button onclick={openAddModal} class="rounded-md bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-400">
				+ Tambah Menu Pertama
			</button>
		</div>

	{:else}
		<!-- Group by category -->
		{#each [...new Set(['', ...categories])] as cat}
			{@const items = menuItems.filter(m => cat === '' ? !m.category : m.category === cat)}
			{#if items.length > 0}
				<div>
					<h2 class="mb-3 text-xs font-semibold uppercase tracking-wider text-surface-500">
						{cat || 'Tanpa Kategori'}
					</h2>
					<div class="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5">
						{#each items as item (item.id)}
							<div class="group relative overflow-hidden rounded-xl border border-surface-700 bg-surface-900">
								<!-- Foto -->
								<div class="relative h-36 bg-surface-800">
									{#if item.image_url}
										<img src={item.image_url} alt={item.name} class="h-full w-full object-cover" />
									{:else}
										<div class="flex h-full items-center justify-center">
											<i class="ti ti-photo text-surface-600" style="font-size:32px" aria-hidden="true"></i>
										</div>
									{/if}
									{#if !item.is_available}
										<div class="absolute inset-0 flex items-center justify-center bg-black/60">
											<span class="rounded-full bg-surface-700 px-2 py-0.5 text-xs font-medium text-surface-400">Tidak Tersedia</span>
										</div>
									{/if}
								</div>

								<!-- Info -->
								<div class="p-3">
									<p class="text-sm font-semibold text-surface-100 line-clamp-1">{item.name}</p>
									<p class="mt-0.5 text-sm font-bold text-primary-400">{formatPrice(item.price)}</p>
									{#if item.description}
										<p class="mt-1 text-xs text-surface-500 line-clamp-2">{item.description}</p>
									{/if}
								</div>

								<!-- Aksi -->
								<div class="flex border-t border-surface-700">
									<button
										onclick={() => openEditModal(item)}
										class="flex-1 py-2 text-xs text-surface-400 hover:bg-surface-800 hover:text-surface-200"
									>
										<i class="ti ti-pencil" aria-hidden="true"></i> Edit
									</button>
									<div class="w-px bg-surface-700"></div>
									<button
										onclick={() => (deleteTarget = item)}
										class="flex-1 py-2 text-xs text-error-400 hover:bg-error-900/20 hover:text-error-300"
									>
										<i class="ti ti-trash" aria-hidden="true"></i> Hapus
									</button>
								</div>
							</div>
						{/each}
					</div>
				</div>
			{/if}
		{/each}
		<p class="text-xs text-surface-500">{menuItems.length} menu terdaftar</p>
	{/if}
</div>

<!-- Modal Tambah/Edit Menu -->
{#if showModal}
	<div
		class="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
		role="presentation"
		onclick={() => { if (!saving) showModal = false; }}
		onkeydown={() => { if (!saving) showModal = false; }}
	>
		<div
			class="w-full max-w-md rounded-xl border border-surface-700 bg-surface-900 p-6 shadow-xl"
			role="dialog"
			aria-modal="true"
			aria-label={editTarget ? 'Edit menu' : 'Tambah menu'}
			tabindex="-1"
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => e.stopPropagation()}
		>
			<h2 class="mb-4 text-lg font-semibold text-surface-50">
				{editTarget ? 'Edit Menu' : 'Tambah Menu'}
			</h2>

			<!-- Upload foto -->
			<div class="mb-4">
				{#if imagePreview}
					<div class="relative overflow-hidden rounded-lg border border-surface-700">
						<img src={imagePreview} alt="Preview" class="h-40 w-full object-cover" />
						<label class="absolute bottom-2 right-2 cursor-pointer rounded-md bg-black/60 px-2 py-1 text-xs text-white hover:bg-black/80">
							<i class="ti ti-camera" aria-hidden="true"></i> Ganti
							<input type="file" accept="image/*" onchange={handleImageSelect} class="hidden" />
						</label>
					</div>
				{:else}
					<label class="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-surface-600 py-6 hover:border-primary-500">
						<i class="ti ti-photo text-surface-500" style="font-size:28px" aria-hidden="true"></i>
						<span class="text-sm text-surface-400">Upload foto menu</span>
						<input type="file" accept="image/*" onchange={handleImageSelect} class="hidden" />
					</label>
				{/if}
			</div>

			<div class="flex flex-col gap-3">
				<div class="flex flex-col gap-1">
					<label for="menu-name" class="text-xs text-surface-400">Nama Menu <span class="text-error-400">*</span></label>
					<input
						id="menu-name"
						type="text"
						bind:value={formName}
						placeholder="contoh: Kopi Susu"
						class="rounded-md border border-surface-600 bg-surface-800 px-3 py-2 text-sm text-surface-50 placeholder:text-surface-500 focus:border-primary-500 focus:outline-none"
					/>
				</div>

				<div class="flex gap-3">
					<div class="flex flex-1 flex-col gap-1">
						<label for="menu-price" class="text-xs text-surface-400">Harga <span class="text-error-400">*</span></label>
						<input
							id="menu-price"
							type="number"
							bind:value={formPrice}
							placeholder="15000"
							min="0"
							class="rounded-md border border-surface-600 bg-surface-800 px-3 py-2 text-sm text-surface-50 placeholder:text-surface-500 focus:border-primary-500 focus:outline-none"
						/>
					</div>
					<div class="flex flex-1 flex-col gap-1">
						<label for="menu-category" class="text-xs text-surface-400">Kategori</label>
						<input
							id="menu-category"
							type="text"
							bind:value={formCategory}
							placeholder="contoh: Minuman"
							list="category-list"
							class="rounded-md border border-surface-600 bg-surface-800 px-3 py-2 text-sm text-surface-50 placeholder:text-surface-500 focus:border-primary-500 focus:outline-none"
						/>
						<datalist id="category-list">
							{#each categories as cat}
								<option value={cat}></option>
							{/each}
						</datalist>
					</div>
				</div>

				<div class="flex flex-col gap-1">
					<label for="menu-desc" class="text-xs text-surface-400">Deskripsi</label>
					<input
						id="menu-desc"
						type="text"
						bind:value={formDescription}
						placeholder="Deskripsi singkat menu"
						class="rounded-md border border-surface-600 bg-surface-800 px-3 py-2 text-sm text-surface-50 placeholder:text-surface-500 focus:border-primary-500 focus:outline-none"
					/>
				</div>

				<label class="flex items-center gap-2 cursor-pointer">
					<input type="checkbox" bind:checked={formAvailable} class="rounded" />
					<span class="text-sm text-surface-300">Tersedia</span>
				</label>
			</div>

			{#if formError}
				<p class="mt-3 text-xs text-error-400">{formError}</p>
			{/if}

			<div class="mt-4 flex gap-2">
				<button
					onclick={() => (showModal = false)}
					disabled={saving}
					class="flex-1 rounded-md border border-surface-600 py-2 text-sm text-surface-300 hover:bg-surface-800 disabled:opacity-50"
				>
					Batal
				</button>
				<button
					onclick={save}
					disabled={saving || !formName.trim() || !formPrice}
					class="flex-1 rounded-md bg-primary-500 py-2 text-sm font-semibold text-white hover:bg-primary-400 disabled:opacity-50"
				>
					{#if saving}
						{uploadingImage ? 'Upload foto...' : 'Menyimpan...'}
					{:else}
						{editTarget ? 'Simpan Perubahan' : 'Tambah Menu'}
					{/if}
				</button>
			</div>
		</div>
	</div>
{/if}

<!-- Modal Konfirmasi Hapus -->
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
			aria-label="Konfirmasi hapus menu"
			tabindex="-1"
			onclick={(e) => e.stopPropagation()}
			onkeydown={(e) => e.stopPropagation()}
		>
			<p class="font-semibold text-surface-50">Hapus menu?</p>
			<p class="mt-1 text-sm text-surface-400">
				<span class="font-medium text-surface-200">{deleteTarget.name}</span>
				akan dihapus permanen.
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
					onclick={deleteItem}
					disabled={deleting}
					class="flex items-center gap-2 rounded-md bg-error-700 px-3 py-1.5 text-sm text-white hover:bg-error-600 disabled:opacity-50"
				>
					{#if deleting}
						<span class="inline-block h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
					{:else}
						<i class="ti ti-trash" aria-hidden="true"></i>
					{/if}
					Hapus
				</button>
			</div>
		</div>
	</div>
{/if}