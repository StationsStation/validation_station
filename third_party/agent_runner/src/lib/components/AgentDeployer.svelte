<script lang="ts">
  import * as Dialog from "$lib/components/ui/dialog";
  import * as Card from "$lib/components/ui/card";
  import * as Input from "$lib/components/ui/input";
  import { Separator } from "$lib/components/ui/separator";
  import * as Button from "$lib/components/ui/button";
  import * as Select from "$lib/components/ui/select/index.js";
  import { Plus } from "svelte-radix";
  import type {  StrategyVars } from "./AgentBuilder.svelte";
  import { configStore, loadConfigsFromStore,} from "../../stores/configs";
  import { keyStore, loadKeysFromStore } from "../../stores/keys";
  import { createDeployment } from "../../stores/deployments";
  import { toast } from "svelte-sonner";



  loadConfigsFromStore();
  loadKeysFromStore();
  let configName: string = "";

  let keyName: string = "";


  let deploymentName: string = "";

  async function handleSave() {
    console.log("Saving config...");

    // we first get the path of the key
    let keys = await loadKeysFromStore();
    let keyPath = keys[keyName];
    if (!keyPath) {
      toast.error("Key not found");
      return;
    }
    // we then get the path of the config data
    let configs = await loadConfigsFromStore();
    let configData = configs[configName];
    if (!configData) {
      toast.error("Config not found");
      return;
    }
    console.log("Key path: ", keyPath);
    console.log("Config data: ", configData);
    createDeployment(
      deploymentName,
      keyPath,
      configData,
    ).then(() => {
      toast("Config saved successfully.");
    }).catch((error) => {
      toast.error("Error saving deployment : " + error);
    })

  }

</script>
<Dialog.Root>
  <Dialog.Trigger>
    <Button.Root>
      <Plus class="w-4 h-4 mr-1" />
      New Agent
    </Button.Root>
  </Dialog.Trigger>

  <Dialog.Content class="space-y-6">
    <Card.Root>
      <Card.Header>
        <Card.Title></Card.Title>
        <Card.Description>
          Deploy your agent configuration using a key and a configuration.
        </Card.Description>
      </Card.Header>

      <Card.Content>
        <div class="key-config-container">
          <!-- Config Select -->
          <div class="border p-4 rounded">
            <Select.Root onSelectedChange={(value) => {configName = value?.value as string;}}>
              <h3 class="text-sm font-semibold">
                Select a Configuration
              </h3>
              <Select.Trigger class="w-full">
                <Select.Value placeholder="Select a Config" />
              </Select.Trigger>
              <Select.Content>
                <Select.Group>
                  {#each Object.keys($configStore) as key}
                    <Select.Item value={key}>{key}</Select.Item>
                  {/each}
                </Select.Group>
              </Select.Content>
            </Select.Root>

            <Separator class="my-4" />

            <Select.Root onSelectedChange={(value) => {keyName = value?.value as string;}}>
              <h3 class="text-sm font-semibold">
                Select a Key
              </h3>
              <Select.Trigger class="w-full">
                <Select.Value placeholder="Select a Key" />
              </Select.Trigger>
              <Select.Content>
                <Select.Group>
                  {#each Object.keys($keyStore) as key}
                    <Select.Item value={key}>{key}</Select.Item>
                  {/each}
                </Select.Group>
              </Select.Content>
            </Select.Root>
          </div>

          <!-- Agent Name -->
          <div class="flex items-center gap-2 mt-8">
            <h5 class="text-sm font-semibold whitespace-nowrap">Agent Name</h5>
            <Input.Root class="flex-1" bind:value={deploymentName}>
              <Input.Input
                type="text"
                placeholder="Enter a name for the agent"
                class="w-full"
              />
            </Input.Root>
          </div>
        </div>
      </Card.Content>
    </Card.Root>
    <!-- Buttons -->
      <div class="flex gap-3 mt-0 w-full px-0">
        <Dialog.Close class="flex-1">
          <Button.Root variant="destructive" class="w-full">
            Cancel
          </Button.Root>
        </Dialog.Close>
        <Dialog.Close class="flex-1">
          <Button.Root
            variant="default"
            class="w-full"
            disabled={!configName || !keyName || !deploymentName}
            onclick={() => {
              // deploy logic
              console.log("Deploying agent with config: ", configName);
              console.log("Using key: ", keyName);
              handleSave();
            }}
          >
            <Plus class="w-4 h-4 mr-1" />
            Deploy
          </Button.Root>
        </Dialog.Close>
      </div>
  </Dialog.Content>
</Dialog.Root>
