<script lang="ts">
  import '../app.css';

    import { Toaster } from "$lib/components/ui/sonner";
  import Footer from '$lib/components/Footer.svelte';
</script>


<div class="flex flex-col min-h-screen bg-black text-green-400 font-mono">
  <main class="flex-1 px-4 pt-8 max-w-4xl mx-auto w-full">
<Toaster />
    <slot />
  </main>
  <!-- Footer sits at the bottom when content is short -->
  <Footer />
</div>