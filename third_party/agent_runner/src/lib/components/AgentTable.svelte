<script lang="ts">
  import * as Table from "$lib/components/ui/table";
  import * as Button from "$lib/components/ui/button";
  import * as Dialog from "$lib/components/ui/dialog";
  import * as Card from "$lib/components/ui/card";
  import { onMount } from "svelte";
  import { AgentStatus} from '../../types/src_tauri';
  import type { Agent } from '../../types/src_tauri';
  import { invoke } from '@tauri-apps/api/core';
  import { 
    Pause, 
    Play, 
    StopCircle, 
    FileText,
    Activity,
    Plus,
    RefreshCw,
    Download,
  } from 'lucide-svelte';
    import AgentDeployer from "./AgentDeployer.svelte";
    import { toast } from "svelte-sonner";
    import { save } from "@tauri-apps/plugin-dialog";
    import { Root } from "./ui/input";
    import { Content } from "./ui/select";
    import { on } from "svelte/events";
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


  let selectedAgentId: string | null = null;
  let isLogsModalOpen = false;
  let isFollowingLogs = true;
  let logContainer: HTMLPreElement;
  let logs: string = "";
  let isStatsModalOpen = false;
  let currentState: any = null;


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
      await invoke("save_logs_to_file", { path: filePath, logs });
      toast(`Logs saved to ${filePath}`);
    }
  }
  async function openStatsModal(id: string) {
    console.log("Opening stats modal for agent:", id);
    selectedAgentId = id;
    isStatsModalOpen = true;
    currentState = await invoke("get_agent_state", { id });
    console.log("Agent state:", currentState);
    // we call until the modal is closed
    while (isStatsModalOpen) {
      currentState = await invoke("get_agent_state", { id });
      console.log("Agent state:", currentState);
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  }
  async function closeLogsModal() {
    console.log("Closing logs modal");
    isLogsModalOpen = false;
  }
  async function closeStatsModal() {
    console.log("Closing stats modal");
    isStatsModalOpen = false;
  }


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
            {:else if [AgentStatus.Stopped].includes(item.status)}
                <Button.Root variant="outline" size="icon" on:click={() => startAgent(item.id)}>
                <Play size={16} />
                </Button.Root>
            {:else if isStopping[item.id]}
                <Button.Root variant="outline" size="icon" disabled>
                <StopCircle size={16} />
                </Button.Root>
            {/if}
            <Dialog.Root >
              <Dialog.Trigger onclick={() => openLogsModal(item.id)} onclose={() => closeLogsModal()}>
                <Button.Root variant="outline" size="icon">
                  <FileText size={16} />
                </Button.Root>
              </Dialog.Trigger>
              <Dialog.Content class="w-full max-w-screen-2xl">
                <Dialog.Title>Logs for {item.address}</Dialog.Title>
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
                          fetchLogs(item.id); // Start fetching
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
                        saveLogs(item.id);
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
            <!-- Stats Modal -->

            <Dialog.Root bind:open={isStatsModalOpen}>
              <Dialog.Trigger onclick={() => openStatsModal(item.id)} >
                <Button.Root variant="outline" size="icon">
                  <Activity size={16} />
                </Button.Root>
              </Dialog.Trigger>
              <Dialog.Content  class="w-full max-w-5xl">
                <Dialog.Title>Stats for {item.address}</Dialog.Title>
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
        </Table.Cell>
      </Table.Row>
    {/each}
  </Table.Body>
</Table.Root>

