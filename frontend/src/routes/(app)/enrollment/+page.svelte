<script lang="ts">
    import { api } from '$lib/api/client';

    type Step = 'form' | 'done';

    let step = $state<Step>('form');
    let submitting = $state(false);
    let error = $state<string | null>(null);
    let enrolledCustomerId = $state<string | null>(null);
    let enrolledName = $state<string | null>(null);

    let name = $state('');
    let contact = $state('');
    let preferences = $state('');
    let notes = $state('');
    let selectedFile = $state<File | null>(null);
    let previewUrl = $state<string | null>(null);

    function handleFileSelect(e: Event): void {
        const input = e.target as HTMLInputElement;
        const file = input.files?.[0];
        if (!file) return;
        selectedFile = file;
        previewUrl = URL.createObjectURL(file);
    }

    async function submit(): Promise<void> {
        if (!name.trim() || !selectedFile) return;

        submitting = true;
        error = null;

        try {
            // Step 1 — Buat customer baru
            const customer = await api.customers.create({
                name: name.trim(),
                contact: contact || null,
                preferences: preferences || null,
                notes: notes || null,
                status: 'active',
            });

            // Step 2 — Enroll wajah
            await api.enrollment.enroll(customer.id, selectedFile);

            enrolledCustomerId = customer.id;
            enrolledName = customer.name;
            step = 'done';
        } catch (e) {
            error = e instanceof Error ? e.message : 'Enrollment gagal';
        } finally {
            submitting = false;
        }
    }

    function reset(): void {
        step = 'form';
        name = '';
        contact = '';
        preferences = '';
        notes = '';
        selectedFile = null;
        previewUrl = null;
        enrolledCustomerId = null;
        enrolledName = null;
        error = null;
    }
</script>

<svelte:head><title>Enrollment Pelanggan — Camera Cafe CRM</title></svelte:head>

<div class="mx-auto max-w-xl">
    <div class="mb-6">
        <a href="/customers" class="text-sm text-surface-500 hover:text-surface-300">← Kembali</a>
        <h1 class="mt-1 text-2xl font-bold text-surface-50">Enrollment Pelanggan</h1>
    </div>

    {#if step === 'done' && enrolledCustomerId}
        <div class="rounded-xl border border-success-700 bg-success-900/20 p-8 text-center">
            <p class="text-4xl">✅</p>
            <p class="mt-3 text-lg font-semibold text-success-300">Enrollment berhasil!</p>
            <p class="mt-1 text-sm text-surface-400">{enrolledName} telah terdaftar dan siap dikenali kamera.</p>
            <div class="mt-6 flex gap-3 justify-center">
                <a href="/customers/{enrolledCustomerId}" class="rounded-md bg-primary-500 px-4 py-2 text-sm font-semibold text-white hover:bg-primary-400">
                    Lihat Profil
                </a>
                <button
                    onclick={reset}
                    class="rounded-md bg-surface-700 px-4 py-2 text-sm text-surface-200 hover:bg-surface-600"
                >
                    Enrollment Baru
                </button>
            </div>
        </div>

    {:else}
        <form
            onsubmit={(e) => { e.preventDefault(); void submit(); }}
            class="flex flex-col gap-5 rounded-xl border border-surface-700 bg-surface-900 p-6"
        >
            <fieldset class="flex flex-col gap-4">
                <legend class="font-semibold text-surface-200">Data Pelanggan</legend>

                <div class="flex flex-col gap-1">
                    <label for="name" class="text-sm text-surface-400">Nama <span class="text-error-400">*</span></label>
                    <input
                        id="name"
                        type="text"
                        bind:value={name}
                        required
                        class="rounded-md border border-surface-600 bg-surface-800 px-3 py-2 text-sm text-surface-50 placeholder:text-surface-500 focus:border-primary-500 focus:outline-none"
                        placeholder="Nama lengkap pelanggan"
                    />
                </div>

                <div class="flex flex-col gap-1">
                    <label for="contact" class="text-sm text-surface-400">Kontak (opsional)</label>
                    <input
                        id="contact"
                        type="text"
                        bind:value={contact}
                        class="rounded-md border border-surface-600 bg-surface-800 px-3 py-2 text-sm text-surface-50 placeholder:text-surface-500 focus:border-primary-500 focus:outline-none"
                        placeholder="Nomor HP atau email"
                    />
                </div>

                <div class="flex flex-col gap-1">
                    <label for="preferences" class="text-sm text-surface-400">Preferensi pesanan (opsional)</label>
                    <input
                        id="preferences"
                        type="text"
                        bind:value={preferences}
                        class="rounded-md border border-surface-600 bg-surface-800 px-3 py-2 text-sm text-surface-50 placeholder:text-surface-500 focus:border-primary-500 focus:outline-none"
                        placeholder="Contoh: Kopi susu less sugar"
                    />
                </div>

                <div class="flex flex-col gap-1">
                    <label for="notes" class="text-sm text-surface-400">Catatan (opsional)</label>
                    <textarea
                        id="notes"
                        bind:value={notes}
                        rows="2"
                        class="rounded-md border border-surface-600 bg-surface-800 px-3 py-2 text-sm text-surface-50 placeholder:text-surface-500 focus:border-primary-500 focus:outline-none"
                        placeholder="Catatan tambahan kasir"
                    ></textarea>
                </div>
            </fieldset>

            <fieldset class="flex flex-col gap-3">
                <legend class="font-semibold text-surface-200">Foto Wajah <span class="text-error-400">*</span></legend>

                <label class="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-surface-600 py-8 hover:border-primary-500">
                    <span class="text-3xl">📷</span>
                    <span class="text-sm text-surface-400">Pilih foto wajah pelanggan</span>
                    <span class="text-xs text-surface-500">JPG, PNG, maks 5MB</span>
                    <input type="file" accept="image/*" onchange={handleFileSelect} class="hidden" />
                </label>

                {#if previewUrl}
                    <div class="overflow-hidden rounded-lg border border-surface-700">
                        <img src={previewUrl} alt="Preview wajah" class="h-48 w-full object-cover" />
                    </div>
                {/if}
            </fieldset>

            {#if error}
                <div class="rounded-md border border-error-700 bg-error-900/20 p-3">
                    <p class="text-sm text-error-400">{error}</p>
                </div>
            {/if}

            <button
                type="submit"
                disabled={submitting || !name.trim() || !selectedFile}
                class="rounded-md bg-primary-500 py-2.5 text-sm font-semibold text-white hover:bg-primary-400 disabled:cursor-not-allowed disabled:opacity-50"
            >
                {submitting ? 'Menyimpan...' : 'Daftarkan Pelanggan'}
            </button>
        </form>
    {/if}
</div>