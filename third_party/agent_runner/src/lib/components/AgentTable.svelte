<script lang="ts">
  import * as Table from "$lib/components/ui/table";
  import * as Button from "$lib/components/ui/button";
  import type { Agent } from '$lib/components/types/src_tauri';
  import { AgentStatus} from '$lib/components/types/src_tauri';
  import { toast } from "svelte-sonner";
  import { onMount } from "svelte";
  import { invoke } from '@tauri-apps/api/core';
  import { 
    Pause, 
    Play, 
    StopCircle, 
    CircleX
  } from 'lucide-svelte';
  import StatsModal from "./StatsModal.svelte";
  import LogsModal from "./LogsModal.svelte";
  import AgentDeployer from "./AgentDeployer.svelte";

  let agentsList : Agent[] = [];
  let isStopping: Record<string, boolean> = {};


  async function fetchAgents() {
    agentsList = await invoke<Agent[]>("list_agents");
  }

  async function stopAgent(id: string) {
    isStopping[id] = true;
    toast("Stopping agent...");
    await invoke("stop_container_command", { id });
    await fetchAgents();
    isStopping[id] = false;

  }

  async function pauseAgent(id: string) {
    await invoke("pause_container_command", { id });
    await fetchAgents();
  }


  async function deleteAgent(id: string) {
    isStopping[id] = true;
    toast("Deleting agent...");
    await invoke("delete_container_command", { id });
    await fetchAgents();
    isStopping[id] = false;
  }

  async function unpauseAgent(id: string) {
    await invoke("unpause_container_command", { id });
    await fetchAgents();
  }

  async function startAgent(id: string) {
    await invoke("start_container_command", { id });
    await fetchAgents();
  } 
//   we need to call this function when the component mounts
  onMount(() => {
    fetchAgents();
  });

  setInterval(fetchAgents, 500);

</script>


  <div class="flex justify-between items-center mb-4">
    <h2 class="font-semibold">Agent Deployments</h2>
    <AgentDeployer />
  </div>
<Table.Root>
  <Table.Caption>Your Active Agents.</Table.Caption>
  <Table.Header>
    <Table.Row>
      <Table.Head class="w-[100px]">Status</Table.Head>
      <Table.Head>Name</Table.Head>
      <Table.Head class="text-right">Actions</Table.Head>
    </Table.Row>
  </Table.Header>
  <Table.Body>
    {#each agentsList as item}
      <Table.Row>
        {#if !isStopping[item.id]}
          <Table.Cell>{item.status}</Table.Cell>
        {:else}
          <Table.Cell>
            <div class="flex items-center gap-2">
              <StopCircle class="animate-spin" />
              <span>Stopping...</span>
            </div>
          </Table.Cell>
        {/if}
        <Table.Cell class="font-medium">{item.address}</Table.Cell>
        <Table.Cell class="text-right">
            {#if [AgentStatus.Running].includes(item.status) && !isStopping[item.id]}
                <Button.Root variant="outline" size="icon" on:click={() => pauseAgent(item.id)}>
                <Pause size={16} />
                </Button.Root>
                <Button.Root variant="destructive" size="icon" on:click={() => stopAgent(item.id)}>
                    <StopCircle size={16} />
                </Button.Root>
            {:else if [AgentStatus.Paused].includes(item.status)}
                <Button.Root variant="default" size="icon" on:click={() => unpauseAgent(item.id)}>
                <Play size={16} />
                </Button.Root>
                <Button.Root variant="destructive" size="icon" on:click={() => stopAgent(item.id)}>
                    <StopCircle size={16} />
                </Button.Root>
            {:else if [AgentStatus.Exited].includes(item.status)}
                <Button.Root variant="destructive" size="icon" on:click={() => deleteAgent(item.id)}>
                  <CircleX size={16} />
                </Button.Root>
            {:else if isStopping[item.id]}
                <Button.Root variant="outline" size="icon" disabled>
                <StopCircle size={16} class="animate-spin" />
                </Button.Root>
            {/if}
            <!-- Logs Modal -->
             <LogsModal
              agentId={item.id}
              ></LogsModal>
            <!-- Stats Modal -->
             <StatsModal
              agentId={item.id}
              ></StatsModal>
            <!-- Delete Agent -->
        </Table.Cell>
      </Table.Row>
    {/each}
  </Table.Body>
</Table.Root>

