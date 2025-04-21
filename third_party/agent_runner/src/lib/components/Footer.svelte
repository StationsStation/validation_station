<script lang="ts">
  import * as Dialog from "$lib/components/ui/dialog";
  import * as Card from "$lib/components/ui/card";
  import { Separator } from "$lib/components/ui/separator";
  import * as Button from "$lib/components/ui/button";
  import * as ToggleGroup from "$lib/components/ui/toggle-group";
  import { sendNotification } from '@tauri-apps/plugin-notification';
  import { open } from '@tauri-apps/plugin-shell';

</script>

<footer class="grid grid-cols-3 gap-4 items-center justify-items-center py-4 border-t border-green-500 bg-black z-10">
  <a href="https://github.com/StationsStation/capitalisation_station" target="_blank" class="block">
    <img src="/derolas.png" alt="Derolas Logo" class="h-20 w-auto" />
  </a>
  <a href="https://olas.network"  target="_blank" class="block">
    <img src="/olas.png" alt="Olas Logo" class="h-16 w-auto" />
  </a>
  <a href="https://derive.xyz" target="_blank" class="block">
    <img src="/derive.png" alt="Derive Logo" class="h-12 w-auto" />
  </a>
</footer>
