<script lang="ts">
    import { api } from '$lib/api/client';
    import { onDestroy } from 'svelte';

    type Step = 'form' | 'done';
    type PhotoMode = 'upload' | 'camera';

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

    // Kamera state
    let photoMode = $state<PhotoMode>('upload');
    let videoEl = $state<HTMLVideoElement | null>(null);
    let canvasEl = $state<HTMLCanvasElement | null>(null);
    let stream = $state<MediaStream | null>(null);
    let cameraError = $state<string | null>(null);

    async function startCamera(): Promise<void> {
        cameraError = null;
        try {
            stream = await navigator.mediaDevices.getUserMedia({ video: true });
            if (videoEl) videoEl.srcObject = stream;
        } catch (e) {
            cameraError = 'Tidak bisa akses kamera. Pastikan browser punya izin kamera.';
        }
    }

    function stopCamera(): void {
        stream?.getTracks().forEach((t) => t.stop());
        stream = null;
    }

    function switchMode(mode: PhotoMode): void {
        photoMode = mode;
        selectedFile = null;
        previewUrl = null;
        if (mode === 'camera') {
            setTimeout(() => startCamera(), 100);
        } else {
            stopCamera();
        }
    }

    function capturePhoto(): void {
        if (!videoEl || !canvasEl) return;
        canvasEl.width = videoEl.videoWidth;
        canvasEl.height = videoEl.videoHeight;
        canvasEl.getContext('2d')?.drawImage(videoEl, 0, 0);
        canvasEl.toBlob((blob) => {
            if (!blob) return;
            selectedFile = new File([blob], 'capture.jpg', { type: 'image/jpeg' });
            previewUrl = URL.createObjectURL(blob);
            stopCamera();
        }, 'image/jpeg', 0.9);
    }

    function retakePhoto(): void {
        selectedFile = null;
        previewUrl = null;
        startCamera();
    }

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
            const customer = await api.customers.create({
                name: name.trim(),
                contact: contact || null,
                preferences: preferences || null,
                notes: notes || null,
                status: 'active',
            });
            await api.enrollment.enroll(customer.id, selectedFile);
            enrolledCustomerId = customer.id;
            enrolledName = customer.name;
            step = 'done';
            stopCamera();
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
        photoMode = 'upload';
        stopCamera();
    }

    onDestroy(() => stopCamera());
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
                <button onclick={reset} class="rounded-md bg-surface-700 px-4 py-2 text-sm text-surface-200 hover:bg-surface-600">
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
                    <input id="name" type="text" bind:value={name} required
                        class="rounded-md border border-surface-600 bg-surface-800 px-3 py-2 text-sm text-surface-50 placeholder:text-surface-500 focus:border-primary-500 focus:outline-none"
                        placeholder="Nama lengkap pelanggan" />
                </div>

                <div class="flex flex-col gap-1">
                    <label for="contact" class="text-sm text-surface-400">Kontak (opsional)</label>
                    <input id="contact" type="text" bind:value={contact}
                        class="rounded-md border border-surface-600 bg-surface-800 px-3 py-2 text-sm text-surface-50 placeholder:text-surface-500 focus:border-primary-500 focus:outline-none"
                        placeholder="Nomor HP atau email" />
                </div>

                <div class="flex flex-col gap-1">
                    <label for="preferences" class="text-sm text-surface-400">Preferensi pesanan (opsional)</label>
                    <input id="preferences" type="text" bind:value={preferences}
                        class="rounded-md border border-surface-600 bg-surface-800 px-3 py-2 text-sm text-surface-50 placeholder:text-surface-500 focus:border-primary-500 focus:outline-none"
                        placeholder="Contoh: Kopi susu less sugar" />
                </div>

                <div class="flex flex-col gap-1">
                    <label for="notes" class="text-sm text-surface-400">Catatan (opsional)</label>
                    <textarea id="notes" bind:value={notes} rows="2"
                        class="rounded-md border border-surface-600 bg-surface-800 px-3 py-2 text-sm text-surface-50 placeholder:text-surface-500 focus:border-primary-500 focus:outline-none"
                        placeholder="Catatan tambahan kasir"></textarea>
                </div>
            </fieldset>

            <!-- Foto Wajah -->
            <fieldset class="flex flex-col gap-3">
                <legend class="font-semibold text-surface-200">Foto Wajah <span class="text-error-400">*</span></legend>

                <!-- Toggle Upload / Kamera -->
                <div class="flex rounded-lg border border-surface-600 overflow-hidden">
                    <button
                        type="button"
                        onclick={() => switchMode('upload')}
                        class="flex-1 py-2 text-sm font-medium transition-colors
                            {photoMode === 'upload' ? 'bg-primary-500 text-white' : 'bg-surface-800 text-surface-400 hover:bg-surface-700'}">
                        Upload Foto
                    </button>
                    <button
                        type="button"
                        onclick={() => switchMode('camera')}
                        class="flex-1 py-2 text-sm font-medium transition-colors
                            {photoMode === 'camera' ? 'bg-primary-500 text-white' : 'bg-surface-800 text-surface-400 hover:bg-surface-700'}">
                        Ambil dari Kamera
                    </button>
                </div>

                <!-- Mode Upload -->
                {#if photoMode === 'upload'}
                    {#if !previewUrl}
                        <label class="flex cursor-pointer flex-col items-center justify-center gap-2 rounded-lg border-2 border-dashed border-surface-600 py-8 hover:border-primary-500">
                            <span class="text-3xl">📷</span>
                            <span class="text-sm text-surface-400">Pilih foto wajah pelanggan</span>
                            <span class="text-xs text-surface-500">JPG, PNG, maks 5MB</span>
                            <input type="file" accept="image/*" onchange={handleFileSelect} class="hidden" />
                        </label>
                    {:else}
                        <div class="overflow-hidden rounded-lg border border-surface-700">
                            <img src={previewUrl} alt="Preview wajah" class="h-72 w-full object-cover" />
                        </div>
                        <button type="button"
                            onclick={() => { selectedFile = null; previewUrl = null; }}
                            class="text-sm text-surface-400 hover:text-surface-200">
                            Ganti foto
                        </button>
                    {/if}
                {/if}

                <!-- Mode Kamera -->
                {#if photoMode === 'camera'}
                    {#if cameraError}
                        <p class="text-sm text-error-400">{cameraError}</p>
                    {:else if !previewUrl}
                        <div class="relative overflow-hidden rounded-lg border border-surface-700 bg-black">
                            <video
                                bind:this={videoEl}
                                autoplay
                                playsinline
                                class="w-full h-72 object-cover">
                            </video>
                            <button
                                type="button"
                                onclick={capturePhoto}
                                class="absolute bottom-3 left-1/2 -translate-x-1/2 rounded-full bg-white px-6 py-2 text-sm font-bold text-black hover:bg-surface-200">
                                Ambil Foto
                            </button>
                        </div>
                        <canvas bind:this={canvasEl} class="hidden"></canvas>
                    {:else}
                        <div class="overflow-hidden rounded-lg border border-surface-700">
                            <img src={previewUrl} alt="Preview wajah" class="h-72 w-full object-cover" />
                        </div>
                        <button type="button" onclick={retakePhoto}
                            class="text-sm text-surface-400 hover:text-surface-200">
                            Ulangi foto
                        </button>
                    {/if}
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
                class="rounded-md bg-primary-500 py-2.5 text-sm font-semibold text-white hover:bg-primary-400 disabled:cursor-not-allowed disabled:opacity-50">
                {submitting ? 'Menyimpan...' : 'Daftarkan Pelanggan'}
            </button>
        </form>
    {/if}
</div>