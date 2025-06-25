<script lang="ts">
  export let isDockerAlive: () => Promise<boolean>;
  import * as AlertDialog from "$lib/components/ui/alert-dialog";
  import * as Button from "$lib/components/ui/button";
</script>

<AlertDialog.Root open>
  <AlertDialog.Content>
    <AlertDialog.Title>Docker is not Running</AlertDialog.Title>
    <AlertDialog.Description>
      You need to start Docker to manage your agents.
    </AlertDialog.Description>
    <Button.Root>
      <!-- svelte-ignore a11y_click_events_have_key_events -->
      <!-- svelte-ignore a11y_no_static_element_interactions -->
      <span on:click={() => isDockerAlive()}>Try Again</span>
    </Button.Root>
  </AlertDialog.Content>
</AlertDialog.Root>
