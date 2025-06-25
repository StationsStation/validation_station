<script lang="ts">
  import * as Card from "$lib/components/ui/card";
  import UserSettings from "$lib/components/UserSettings.svelte";
  import AgentTable from "$lib/components/AgentTable.svelte";
  import ConfigTable from "$lib/components/ConfigTable.svelte";
  import Nodes from "$lib/components/Nodes.svelte";
  import StartDockerDialog from "$lib/components/StartDockerDialog.svelte";
  import ApplicationVersionBadge from "$lib/components/ApplicationVersionBadge.svelte";
  import { getVersion } from "@tauri-apps/api/app";
  import { invoke } from "@tauri-apps/api/core";
  import { onMount } from "svelte";

  let isRunningInTauri: boolean = false;
  let isDockerRunning: boolean = false;
  let isLoading: boolean = true;
  let appVersion: string | null = null;

  async function readAppVersion(): Promise<string | null> {
    if (appVersion) return appVersion;
    try {
      appVersion = await getVersion();
    } catch (error) {
      appVersion = null;
    }
    return appVersion;
  }

  async function isTauri(): Promise<boolean> {
    if (null !== await readAppVersion()) {
      isRunningInTauri = true;
    }

    return isRunningInTauri;
  }

  async function isDockerAlive(): Promise<boolean> {
    try {
      isDockerRunning = await invoke("connect_to_docker");
    } catch {
      isDockerRunning = false;
    }
    return isDockerRunning;
  }

  onMount(async () => {
    await isTauri();
    if (isRunningInTauri) await isDockerAlive();
    isLoading = false;
  });
</script>

<title>Derolas</title>
<div>
  <main>
    {#if isLoading}
      <p class="text-center text-muted text-sm mt-10">Loading...</p>
    {:else if isRunningInTauri}
      <ApplicationVersionBadge {appVersion} />
      {#if !isDockerRunning}
        <StartDockerDialog {isDockerAlive} />
      {:else}
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
                <ConfigTable />
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
      {/if}
    {:else}
      <Nodes />
    {/if}
  </main>
</div>
