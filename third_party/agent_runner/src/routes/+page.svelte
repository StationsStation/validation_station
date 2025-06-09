
<script lang="ts">
  import * as Card from "$lib/components/ui/card";
  import UserSettings from '$lib/components/UserSettings.svelte';
  import AgentTable from '$lib/components/AgentTable.svelte';
  import ConfigTable from '$lib/components/ConfigTable.svelte';
  import Nodes from '$lib/components/Nodes.svelte';
  import { getVersion } from "@tauri-apps/api/app";

  let isRunningInTauri: boolean = false;
  async function isTauri(): Promise<boolean> {
    try {
      await getVersion();
      isRunningInTauri = true;
    } catch {
      isRunningInTauri = false;
    }
    return isRunningInTauri;
  }

  isTauri();
</script>
<!--  -->

<title>Derolas</title>
<div>
  <main>

    {#if isRunningInTauri}

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
    {:else}
      <Nodes></Nodes>
    {/if}
</div>
