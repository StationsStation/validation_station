<script lang="ts">
  import * as Dialog from "$lib/components/ui/dialog";
  import * as Card from "$lib/components/ui/card";

  import * as Input from "$lib/components/ui/input";
  import * as Button from "$lib/components/ui/button";
  import * as ToggleGroup from "$lib/components/ui/toggle-group";
  import { open } from '@tauri-apps/plugin-dialog';
  const KeyMode = {
    Existing:  'existing',
    NewKey: 'new_key'
  }
  import { toast } from "svelte-sonner";
  import { Delete, Save,} from "lucide-svelte";
  import { generateKeyFile, keyStore, loadKeysFromStore, removeKeyFromStore, saveKeysToStore,} from "../../stores/keys";
  let mode: string = KeyMode.NewKey;
  let file: string = "";
  let keyName: string = "";
  loadKeysFromStore();

  import * as Table from "$lib/components/ui/table";

  async function handleGenerate() {
    console.log("Generating new key...");
    toast("Generating new key...");
    await generateKeyFile(keyName)
    console.log("Key generated successfully.");

  }

  function handleSelectFile() {
    open({
      title: 'Select Existing Key File',
      multiple: false,
      filters: [{ name: 'Key Files', extensions: ['txt', 'json'] }],
    }).then((selected) => {
      if (typeof selected === 'string') {
        file = selected;
        console.log("Selected file:", file);
      }
    });
  }


  async function handleSave(id:string, path: string) {
    let currentKeys = $keyStore
    currentKeys[id] = path;
    await saveKeysToStore(currentKeys);
    toast(`Key ${id} saved successfully.`);
    }
</script>
  <div class="flex justify-end items-center mb-4">

<Dialog.Root>
  <Dialog.Trigger>
    <Button.Root>
      User Settings
    </Button.Root>
  </Dialog.Trigger>

  <Dialog.Content>
    <Card.Root>
      <Card.Header>
        <Card.Title>User Key</Card.Title>
        <Card.Description>
          Manage your agent's cryptographic key
        </Card.Description>
      </Card.Header>

      <Card.Content>
        <div class="key-config-container">
          <!-- Toggle group with vertical margin and centered -->
           <Card.Root class="key-mode-card">
          <div class="key-mode-toggle">
            <ToggleGroup.Root type="single" bind:value={mode}>
              <ToggleGroup.Item value={KeyMode.NewKey}>
                Use a new key
              </ToggleGroup.Item>
              <ToggleGroup.Item value={KeyMode.Existing}>
                Use an existing key
              </ToggleGroup.Item>
            </ToggleGroup.Root>
          </div>
           </Card.Root>

          <!-- Mode-based content within a card -->
           <Card.Root class="key-mode-card">
            <Card.Header>
              <Card.Title>{mode === KeyMode.NewKey ? "Generate New Key" : "Existing Key"}</Card.Title>
              <Card.Description>
                {mode === KeyMode.NewKey ? "Generate a new key for your agent." : "Select an existing key file."}
              </Card.Description>
            </Card.Header>
            <Card.Content>
              <div class="key-mode-content">
                {#if mode === KeyMode.Existing}
                    <div class="existing-key space-y-2">
                        <Button.Root on:click={handleSelectFile}>
                            Select Existing Key
                        </Button.Root>
                    </div>
                {/if}
              </div>
              <div>
                {#if file && mode === KeyMode.Existing}
                <!-- file is quite long so we shorted it -->
                  <p class="file-selected">Selected file: {file.length > 20 ? file.slice(0, 20) + '...' : file}</p>
                {/if}
              </div>
            </Card.Content>
            <!-- Config Name -->
            <div class="flex items-center gap-0 my-8">
              <h5 class="text-sm font-semibold">Config Name:</h5>
              <Input.Root class="flex-1" bind:value={keyName}>
                <Input.Input
                  type="text"
                  placeholder="Enter a name for the config"
                  class="w-full"
                />
              </Input.Root>
            <Dialog.Close class="flex-1">
              <Button.Root on:click={
                () => {
                  if (mode === KeyMode.NewKey) {
                    handleGenerate();
                  } else if (mode === KeyMode.Existing) {
                    handleSave(keyName, file);

                  }
                }
              } class="save-config" disabled={
                !keyName || (mode === KeyMode.Existing && !file)
                }>
                <Save />
                Save Config
              </Button.Root>
            </Dialog.Close>
            </div>
            <!-- end config name -->
          </Card.Root>
      </Card.Content>
    </Card.Root>
  </Dialog.Content>
</Dialog.Root>
</div>

<Table.Root>
  <Table.Caption>Your Keys.</Table.Caption>
  <Table.Header>
    <Table.Row>
      <Table.Head class="w-[100px]">Name</Table.Head>
      <Table.Head>Path</Table.Head>
      <Table.Head class="text-right">Actions</Table.Head>
    </Table.Row>
  </Table.Header>
  <Table.Body>
    {#each Object.entries($keyStore) as [key, path]} <!-- we need to use the key as the key for the row -->
      <Table.Row>
        <Table.Cell class="font-medium">{key}</Table.Cell>
        <Table.Cell title={path}>{path.length > 20 ? path.slice(0, 20) + '...' : path}</Table.Cell>
        <Table.Cell class="text-right">
          <div class="flex justify-end gap-2">
            <Button.Root variant="destructive" size="icon" on:click={() => removeKeyFromStore(key)}>
              <Delete size={16} />
            </Button.Root>
          </div>
        </Table.Cell>
      </Table.Row>
    {/each}
  </Table.Body>
</Table.Root>



