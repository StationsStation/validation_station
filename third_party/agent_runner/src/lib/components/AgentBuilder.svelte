<script lang="ts">
  import * as Dialog from "$lib/components/ui/dialog";
  import * as Card from "$lib/components/ui/card";
  import * as Input from "$lib/components/ui/input";
  import * as Button from "$lib/components/ui/button";
  import { Save } from 'lucide-svelte';
  import * as Select from "$lib/components/ui/select/index.js";
  import type { Selected } from "bits-ui";

    import { message } from '@tauri-apps/plugin-dialog';
    import { configStore, loadConfigsFromStore, saveConfigsToStore } from "../../stores/configs";
    import { Plus } from "svelte-radix";
// Each strategy maps to a StrategyVars object directly



  const strategies: Strategy[] = [
    { 
      name: "eightballer/derive_arbitrage_agent", 
      label: "Derive Spot Arbitrage" 
    },
    ];


let config: StrategyVars = {
  vars: {},
  name: "",
  strategy: "",
};

let selectedStrategy: Strategy | undefined = undefined;


let strategiesToVars: Record<string, StrategyVars> = {
  "eightballer/derive_arbitrage_agent": {
    name: "Derive Spot Arbitrage",
    strategy: "eightballer/derive_arbitrage_agent",
    vars: {
      DERIVE_WALLET: {
        name: "DERIVE_WALLET",
        description: "Derive Smart Contract Wallet Address",
        value: "",
        provision_type: "string"
      },
      DERIVE_SUBACCOUNT_ID: {
        name: "DERIVE_SUBACCOUNT_ID",
        description: "Derive Subaccount ID",
        value: "",
        provision_type: "string"
      },
      BASE_ASSET: {
        name: "BASE_ASSET",
        description: "Base Asset",
        value: "USDC",
        provision_type: "string"
      },
      QUOTE_ASSET: {
        name: "QUOTE_ASSET",
        description: "Quote Asset",
        value: "LBTC",
        provision_type: "string"
      },
      ORDER_SIZE: {
        name: "ORDER_SIZE",
        description: "Order Size in Quote Asset",
        value: "0.01",
        provision_type: "string"
      },
      MIN_PROFIT: {
        name: "MIN_PROFIT",
        description: "Minimum Profit in Percentage (0.01 = 1%)",
        value: "0.0006",
        provision_type: "string"
      },
      APPRISE_ENDPOINT: {
        name: "APPRISE_ENDPOINT",
        description: "Apprise Endpoint for Notifications",
        value: "",
        provision_type: "string"
      },
      BASE_RPC: {
        name: "BASE_RPC",
        description: "Base RPC URL",
        value: "https://base.drpc.org",
        provision_type: "string"
      },
      COOLDOWN_PERIOD: {
        name: "COOLDOWN_PERIOD",
        description: "Cooldown Time in Seconds",
        value: "30",
        provision_type: "string"
      },
      COW_CHAINS: {
        name: "COW_CHAINS",
        description: "Cow Protocol Chains (comma-separated)",
        value: '["base"]',
        provision_type: "string"
      },
    }
  },
};

let currentConfigs: Record<string, StrategyVars> = {};

let store = configStore

async function saveConfig() {

  console.log("Saving config...");
  if (!configName) {
    message("Please enter a name for the config");
    return;
  }
  const configData = {
    name: configName,
    strategy: selectedStrategy?.name,
    vars: config.vars
  };
  // we get the current configs 
  const currentConfigs = await loadConfigsFromStore();
  console.log("Current configs:", currentConfigs);
  if (!currentConfigs) {
    console.log("No configs found in store, creating new one");
    await store.set({});
  }

  console.log("Current configs:", currentConfigs);
  // we check if the config name already exists
  if (currentConfigs[configName]) {
    message("Config name already exists, please choose a different name");
    return;
  }
  // we check if the config name is empty
  if (configName.trim() === "") {
    message("Config name cannot be empty");
    return;
  }
  // we check if the config name is too long
  if (configName.length > 50) {
    message("Config name cannot be longer than 50 characters");
    return;
  }
  if (selectedStrategy === undefined) {
    message("Please select a strategy");
    return;
  }
  currentConfigs[configName] = {
    name: configName,
    strategy: selectedStrategy.name,
    vars: config.vars
  };
  saveConfigsToStore(currentConfigs);
  console.log("Config saved to store:", currentConfigs);
}



function onStrategySelected(new_val: Selected<string> | undefined) {
  if (!new_val) {
    console.log("No strategy selected");
    return;
  }
  let strategy = strategies.find(s => s.name == new_val.value);
  if (!strategy) {
    console.log("Strategy not found");
    return;
  }
  selectedStrategy = strategy;
  config = strategiesToVars[strategy.name];
}

let configName: string = "";


</script>
<script context="module" lang="ts">


  interface StrategyVar {
    name: string;
    description: string;
    value: string;
    provision_type: string;
  }

  export interface StrategyVars {
    name: string;
    strategy: string;
    vars: Record<string, StrategyVar>;
  }

  export interface Strategy {
    name: string;
    label: string;
  }

  export type StrategyConfig = Record<string, StrategyVars>;
</script>
<Dialog.Root>
  <Dialog.Trigger>
    <Button.Root>
      <Plus class="w-4 h-4 mr-1" />
      New Config
    </Button.Root>
  </Dialog.Trigger>

  <Dialog.Content>
    <Card.Root>
      <Card.Header>
        <Card.Title>
        </Card.Title>
        <Card.Description>
          Build your agent configuration using the builder.
        </Card.Description>
      </Card.Header>

      <Card.Content>
        <div class="key-config-container">
          <Card.Root class="key-mode-card">
            <Select.Root onSelectedChange={onStrategySelected} >
              <Select.Trigger class="w-[250px]">
                <Select.Value placeholder="Select a Strategy" />
              </Select.Trigger>
              <Select.Content>
                <Select.Group>
                  {#each strategies as strategy}
                    <Select.Item value={strategy.name}>{strategy.label}</Select.Item>
                  {/each}
                </Select.Group>
              </Select.Content>
            </Select.Root>
          </Card.Root>
          <div class="my-8"></div>
            <Card.Root class="strategy-config-card h-96 overflow-y-auto p-4">
              {#if selectedStrategy}
                <div class="flex flex-col gap-4">
                  {#each Object.entries(config.vars) as [key, varObj]}
                    <div>
                      <h6 class="text-sm font-semibold">{key}</h6>
                      <Input.Root
                        type="text"
                        placeholder={varObj.description}
                        bind:value={varObj.value}
                        class="w-full"
                      />
                    </div>
                  {/each}
                </div>
              {/if}
              <div class="my-8"></div>
            </Card.Root>
        <!-- Config Name -->
        <div class="flex items-center gap-0 my-8">
          <h5 class="text-sm font-semibold">Config Name:</h5>
          <Input.Root class="flex-1" bind:value={configName}>
            <Input.Input
              type="text"
              placeholder="Enter a name for the config"
              class="w-full"
            />
          </Input.Root>
          <Button.Root on:click={saveConfig} class="save-config" disabled={!configName}>
            <Save />
            Save Config
          </Button.Root>
        </div>
        <!-- end config name -->
      </Card.Content>
    </Card.Root>
  </Dialog.Content>
</Dialog.Root>
