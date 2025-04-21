
<script lang="ts">

  import { invoke } from '@tauri-apps/api/core';
  import { onDestroy, onMount } from 'svelte';
  import { afterUpdate } from 'svelte';
  import { DefaultService, OpenAPI } from '$lib/api';
  import type { StateResponse } from '$lib/api';

  import * as Card from "$lib/components/ui/card";
  import Footer from "$lib/components/Footer.svelte";

import { open } from '@tauri-apps/plugin-dialog';
  import UserSettings from '$lib/components/UserSettings.svelte';
  import AgentTable from '$lib/components/AgentTable.svelte';
  import ConfigTable from '$lib/components/ConfigTable.svelte';
  import AgentBuilder from '$lib/components/AgentBuilder.svelte';

  let isConfigModalOpen = false;
  let privateKeyPath = "";
  let environmentPath = "";

  // let interval = setInterval(fetchAgents, 500);
  let currentState: StateResponse | null = null;
  let statsInterval: number | null = null;

  let version = "latest";

  let isUpdating = false;
  let isUpdatingVersion = false;

  let logs: string = "";
  let isStatsModalOpen = false;


  let isFollowingLogs = true;
  let logInterval: number | null = 10;

  let expandedGear = -1;
  let logContainer: HTMLPreElement;

//   // config



//   async function selectEnvironmentFile() {
//     console.log("Selecting environment file...");
//     const selected = await open({
//       title: 'Select Environment File',
//       multiple: false,
//       filters: [{ name: 'Environment', extensions: ['config', 'txt'] }],
//     });
//     if (typeof selected === 'string') {
//       environmentPath = selected;
//     }
//   }
  
// async function selectPrivateKey() {
//   const selected = await open({
//     title: 'Select Private Key File',
//     multiple: false,
//     filters: [{ name: 'private key files', extensions: ['txt'] }],
//   });

//   if (typeof selected === 'string') {
//     privateKeyPath = selected;
//   }
// }


  // afterUpdate(() => {
  //   if (logContainer && isFollowingLogs) {
  //     logContainer.scrollTop = logContainer.scrollHeight;
  //   }
  // }); 

  // $: if (isLogsModalOpen && isFollowingLogs && selectedAgentId) {
  //   cleanupLogInterval();
  //   logInterval = setInterval(fetchLogs, 3000);
  // } else if (!isLogsModalOpen || !isFollowingLogs) {
  //   cleanupLogInterval();
  // }



  // async function createNewAgent() {
  //   let config = {
  //     privateKeyPath,
  //     environmentPath,
  //   }
  //   await invoke("start_container_command", {config});
  //   await fetchAgents(); // refresh list after new agent is started
  // }

  // function cleanupLogInterval() {
  //   if (logInterval) {
  //     clearInterval(logInterval);
  //     logInterval = null;
  //   }
  // }

  // // Update the modal close handler
  // function closeLogsModal() {
  //   isLogsModalOpen = false;
  //   cleanupLogInterval();
  // }

  // function closeStatsModal() {
  //   isStatsModalOpen = false;
  // }

  // // clear interval on component destroy
  // onDestroy(() => {
  //   clearInterval(interval);
  // });


  // OpenAPI.BASE = "http://localhost:8889";

  // console.log("OpenAPI.BASE:", OpenAPI.BASE);
  // export async function load() {
  //   const state = await DefaultService.get(); // fully typed
  //   return { state };
  // }
  

  // load()
  //   .then(({ state }) => {
  //     console.log("State loaded:", state);
  //     // do something with the state
  //     console.log("State:", state);
  //   })
  //   .catch((error) => {
  //     console.error("Error loading state:", error);
  //   });

  



  // $: {
  //   if (isStatsModalOpen) {
  //     // clear any existing interval before setting a new one
  //     if (statsInterval) clearInterval(statsInterval);

  //     statsInterval = setInterval(async () => {
  //       currentState = await invoke("get_agent_state", { id: selectedAgentId });
  //       console.log("Agent state:", currentState);
  //     }, 500);
  //   } else {
  //     if (statsInterval) {
  //       clearInterval(statsInterval);
  //       statsInterval = null;
  //     }
  //   }
  // }

  // onDestroy(() => {
  //   if (statsInterval) clearInterval(statsInterval);
  //   clearInterval(interval);
  //   cleanupLogInterval();
  // });

  // onMount(fetchAgents);
</script>
<!--  -->

<title>Derolas</title>
<div>
  <main>
    <Card.Root>
      <Card.Content>
        <Card.Root>
          <Card.Header>
            <Card.Title>Deloras</Card.Title>
            <Card.Description>
              Manage your agents and their configurations.
            </Card.Description>
          </Card.Header>
          <Card.Content> 
            <UserSettings />
          </Card.Content>
        </Card.Root>
        <div class="my-8"></div>
        <Card.Root>
          <Card.Content>
            <ConfigTable/>
          </Card.Content>
        </Card.Root>
        <div class="my-8"></div>
        <Card.Root>
          <Card.Content>
            <AgentTable />
          </Card.Content>
        </Card.Root>
      </Card.Content>
    </Card.Root>
</div>
