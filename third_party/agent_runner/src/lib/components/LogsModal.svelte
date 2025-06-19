<script lang="ts">
  export let agentId: string = "";

  import * as Button from "$lib/components/ui/button";
  import * as Dialog from "$lib/components/ui/dialog";
  import * as Card from "$lib/components/ui/card";
  import type { StateResponse } from '$lib/api';
  import { invoke } from '@tauri-apps/api/core';
  import { onMount } from "svelte";
  import { AgentStatus} from '$lib/components/types/src_tauri';
  import type { Agent } from '$lib/components/types/src_tauri';
  import { 
    FileText,
    Download,
  } from 'lucide-svelte';
  import { toast } from "svelte-sonner";
  import { save } from "@tauri-apps/plugin-dialog";

  let agentsList : Agent[] = [];

  let selectedAgentId: string | null = null;
  let isLogsModalOpen = false;
  let isFollowingLogs = true;
  let logContainer: HTMLPreElement;
  let logs: string = "";


  async function fetchAgents() {
    agentsList = await invoke<Agent[]>("list_agents");
  }

  onMount(() => {
    fetchAgents();
  });

  setInterval(fetchAgents, 500);

  async function openLogsModal(agentId: string) {
    console.log("Opening logs modal for agent:", agentId);
    selectedAgentId = agentId;
    isLogsModalOpen = true;
    await fetchLogs(agentId); // no param
  }

  async function fetchLogs(id: string) {
    logs = await invoke("get_container_logs", { id: id});
    // If following is enabled, scroll to bottom after fetching new logs
    if (isFollowingLogs && logContainer) {
      // Use setTimeout to ensure this happens after the DOM updates
      setTimeout(() => {
        logContainer.scrollTop = logContainer.scrollHeight;
      }, 100);
      // we recursively call this function every 3 seconds
      setTimeout(() => {
        fetchLogs(id);
      }, 1000);
    }
  }


  async function saveLogs(id: string) {
    const logs = await invoke("get_container_logs", { id: id});
    const filePath = await save({
      defaultPath: `logs_${id}.txt`,
      filters: [{ name: 'Text Files', extensions: ['txt'] }],
    });
    if (filePath) {
      // Save the logs to the selected file
      await invoke("save_logs_to_file", { filePath, logs });
    }
  }
  async function closeLogsModal() {
    console.log("Closing logs modal");
    isLogsModalOpen = false;
  }
  
</script>
<Dialog.Root >
  <Dialog.Trigger onclick={() => openLogsModal(agentId)} onclose={() => closeLogsModal()}>
    <Button.Root variant="outline" size="icon">
      <FileText size={16} />
    </Button.Root>
  </Dialog.Trigger>
  <Dialog.Content class="w-full max-w-screen-2xl">
    <Dialog.Title>Logs for {agentId}</Dialog.Title>
    <Dialog.Description>
      <pre bind:this={logContainer} class="overflow-auto max-h-96"> </pre>
      <!-- We add in a follow logs button -->

    </Dialog.Description>
    <!-- We now render the logs card -->
    <Card.Root>
      <Card.Content>
        <div class="flex items-center gap-2">
          <h5 class="text-sm font-semibold">Logs</h5>
        </div>
        <!-- Now a nice container for the logs -->
        <div class="overflow-auto max-h-96">
          <pre bind:this={logContainer} class="overflow-auto max-h-96">{logs}</pre>
        </div>
      </Card.Content>
        <div class="flex justify-center gap-4 mt-6">
        <!-- Follow/Unfollow Logs Button -->
        <Button.Root
          variant="outline"
          on:click={() => {
            isFollowingLogs = !isFollowingLogs;
            if (isFollowingLogs) {
              fetchLogs(agentId); // Start fetching
            }
          }}
          class="flex items-center gap-2 px-4 py-2"
        >
          <FileText
            size={16}
            class={isFollowingLogs ? "text-green-500" : "text-gray-500"}
          />
          {isFollowingLogs ? "Unfollow Logs" : "Follow Logs"}
        </Button.Root>
        <!-- Save Logs Button -->
        <Button.Root
          variant="outline"
          on:click={() => {
            saveLogs(agentId);
          }}
          class="flex items-center gap-2 px-4 py-2"
        >
          <Download size={16} />
          Save Logs
        </Button.Root>
      </div>
    </Card.Root>
  </Dialog.Content>
</Dialog.Root>