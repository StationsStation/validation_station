<script lang="ts">
  import * as Table from "$lib/components/ui/table";
  import * as Dialog from "$lib/components/ui/dialog";
  import * as Input from "$lib/components/ui/input";
    import * as Button from "$lib/components/ui/button";
  import { 
    Delete,
    Edit,
    Copy,
    Plus,
    Save,
  } from 'lucide-svelte';
    import { configStore, removeConfigFromStore, copyConfig, updateConfig } from "../../stores/configs";
    import AgentBuilder from "./AgentBuilder.svelte";


  let isCopying = false;
  let configName = "";

  function openCopy(oldKey: String) {
    isCopying = true;
  }

  function closeCopy() {
    isCopying = false;
  }


  // we make it reactive so that we can use it in the template
  $: configName
  $: isCopying


</script>
	

  <div class="flex justify-between items-center mb-4">
    <h2 class="font-semibold">Strategy Configurations</h2>
    <AgentBuilder />
  </div>


  <Table.Root>
    <Table.Header>
      <Table.Row>
        <Table.Head class="w-[100px]">Name</Table.Head>
        <Table.Head>Strategy</Table.Head>
        <Table.Head class="text-right">Actions</Table.Head>
      </Table.Row>
    </Table.Header>

    <Table.Body>
      {#if Object.values($configStore).length === 0}
        <Table.Row>
          <Table.Cell colspan={3} class="text-center text-muted-foreground py-4">
            No configurations found.
          </Table.Cell>
        </Table.Row>
      {:else}
        {#each Object.values($configStore) as item}
          <Table.Row class="hover:bg-muted/30 transition">
            <Table.Cell class="font-medium">{item.name}</Table.Cell>
            <Table.Cell>{item.strategy}</Table.Cell>
            <Table.Cell class="text-right">
              <div class="flex justify-end gap-2">
                <Button.Root variant="ghost" size="icon" onclick={() => {openCopy(item.name)}}>
                  <Dialog.Root>
                      <Dialog.Trigger >
                        <Button.Root variant="ghost" size="icon">
                          <Copy class="w-4 h-4" />
                        </Button.Root>
                      </Dialog.Trigger>
                    <Dialog.Content>
                      <Input.Root
                        type="text"
                        placeholder="Enter a name for the new config"
                        bind:value={configName}
                        class="w-full"
                      />
                        <Dialog.Close>
                          <Button.Root
                            variant="outline"
                            onclick={() => {
                              if (configName) {
                                copyConfig(item.name, configName,);
                              }
                              closeCopy();
                            }}
                          >
                            <Plus class="w-4 h-4" />
                          </Button.Root>
                        </Dialog.Close>
                      </Dialog.Content>
                  </Dialog.Root>
                </Button.Root>
                <Button.Root variant="ghost" size="icon" onclick={() => {removeConfigFromStore(item.name)}}>
                  <Delete class="w-4 h-4" />
                </Button.Root>

                <Dialog.Root>
                  <Dialog.Trigger >
                    <Button.Root variant="ghost" size="icon">
                      <Edit class="w-4 h-4" />
                    </Button.Root>
                  </Dialog.Trigger>
                
                  <Dialog.Content>
                    <!-- Edit dialog content goes here -->
                    <p>Edit config: {item.name}</p>
                      {#each Object.entries(item.vars) as [key, varObj]}
                        <h6 class="text-sm font-semibold">{key}</h6>
                        <Input.Root
                          type="text"
                          placeholder={varObj.description}
                          bind:value={varObj.value}
                          class="w-full"
                        />
                      {/each}
                        <div class="flex gap-2 mt-4">
                          <!-- Save button (with logic if needed) -->
                          <Dialog.Close >
                            <Button.Root
                              variant="default"
                              on:click={() => {
                                updateConfig(item.name, item);
                              }}
                            >
                            <Save class="w-4 h-4" />
                              Save
                            </Button.Root>
                          </Dialog.Close>
                        </div>
                  </Dialog.Content>
                </Dialog.Root>
              </div>
            </Table.Cell>
          </Table.Row>
        {/each}
      {/if}
    </Table.Body>
  </Table.Root>