
<script lang="ts">
  import * as Card from "$lib/components/ui/card";
  import UserSettings from '$lib/components/UserSettings.svelte';
  import AgentTable from '$lib/components/AgentTable.svelte';
  import ConfigTable from '$lib/components/ConfigTable.svelte';
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
