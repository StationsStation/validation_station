<script lang="ts">
  export let agentId: string = "";

  import * as Button from "$lib/components/ui/button";
  import * as Dialog from "$lib/components/ui/dialog";
  import * as Card from "$lib/components/ui/card";
  import type { StateResponse } from '$lib/api';
  import { invoke } from '@tauri-apps/api/core';
  import {
    Activity,
  } from 'lucide-svelte';

  let isStatsModalOpen: boolean = false;
  let currentState: StateResponse | null = null;

  async function openStatsModal(id: string) {
    console.log("Opening stats modal for agent:", id);
    isStatsModalOpen = true;
    currentState = await invoke("get_agent_state", { id });
    console.log("Agent state:", currentState);
    // we call until the modal is closed
    console.log("Starting to poll agent state");
    while (isStatsModalOpen) {
      console.log("Agent state:", currentState);
      currentState = await invoke("get_agent_state", { id });
      console.log("Agent state:", currentState);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }

  async function closeStatsModal() {
    console.log("Closing stats modal");
    isStatsModalOpen = false;
    currentState = null;
    agentId = "";
  }

</script>
<Dialog.Root bind:open={isStatsModalOpen}>
    <Dialog.Trigger onclick={() => openStatsModal(agentId)} onclose={() => closeStatsModal()}>
    <Button.Root variant="outline" size="icon">
      <Activity size={16} />
    </Button.Root>
  </Dialog.Trigger>
  <Dialog.Content  class="w-full max-w-5xl">
    <Dialog.Title>Stats for {agentId}</Dialog.Title>
    <Card.Root class="p-4 border border-green-700">
      <Card.Header class="mb-4">
        <Card.Title class="text-lg font-semibold text-green-400">Agent Status</Card.Title>
        <Card.Description>
          <code class={currentState?.is_healthy ? "text-green-500" : "text-red-500"}>
            {currentState?.is_healthy ? "Everything Ok!" : "Please Check Me!"}
          </code>
        </Card.Description>
      </Card.Header>
    
      <Card.Content class="grid grid-cols-2 gap-4 text-sm">
        <div>
          <h4 class="font-semibold text-green-300">Current Period</h4>
          <code class="block mt-1 text-green-200">{currentState?.current_period}</code>
        </div>
        <div>
          <h4 class="font-semibold text-green-300">Total Open Orders</h4>
          <code class="block mt-1 text-green-200">{currentState?.total_open_orders}</code>
        </div>
        <div>
          <h4 class="font-semibold text-green-300">Ready</h4>
          <code class="block mt-1">
            {#if currentState?.is_healthy}
              <span class="text-green-500">Yes</span>
            {:else}
              <span class="text-red-500">No</span>
            {/if}
          </code>
        </div>
        <div>
          <h4 class="font-semibold text-green-300">Current Agent State</h4>
          <code class="block mt-1 text-green-200">{currentState?.current_state}</code>
        </div>
      </Card.Content>
    </Card.Root>
  </Dialog.Content>
</Dialog.Root>
