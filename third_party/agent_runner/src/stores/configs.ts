import type { StrategyVars } from '$lib/components/AgentBuilder.svelte';
import { writable } from 'svelte/store';
import { load } from '@tauri-apps/plugin-store';

const CONFIG_KEY = 'configs';

export const configStore = writable<Record<string, StrategyVars>>({});

// Load from Tauri store and update Svelte store
export async function loadConfigsFromStore() {
  const store = await load(CONFIG_KEY, { autoSave: true });
  const raw = await store.get(CONFIG_KEY);
  const configs = (raw ?? {}) as Record<string, StrategyVars>;
  configStore.set(configs);
  console.log("Loaded configs from store:", configs);
  return configs;
}

// Save to Tauri store and update Svelte store
export async function saveConfigsToStore(configs: Record<string, StrategyVars>) {
  const store = await load(CONFIG_KEY, { autoSave: true });
  await store.set(CONFIG_KEY, configs);
  await store.save();
  configStore.set(configs);
  console.log("Saved configs to store:", configs);
}

export async function removeConfigFromStore(key: string) {
  const store = await load(CONFIG_KEY, { autoSave: true });
  const configs = (await store.get(CONFIG_KEY)) as Record<string, StrategyVars>;
  if (!configs) {
    console.log("No configs found in store to remove:", key);
    return;
  }
  console.log("Removing config from store:", key);
  delete configs[key];
  configStore.set(configs as Record<string, StrategyVars>);
  await store.set(CONFIG_KEY, configs);
  await store.save();
}

export async function copyConfig(key: string, newKey: string) {
  const store = await load(CONFIG_KEY, { autoSave: true });
  const configs = (await store.get(CONFIG_KEY)) as Record<string, StrategyVars>;
  if (!configs) {
    console.log("No configs found in store to copy:", key);
    return;
  }
  console.log("Copying config in store:", key, "to", newKey);
  const config = configs[key];
  if (!config) {
    console.log("Config not found in store to copy:", key);
    return;
  }
  let newConfig = { ...config };
  newConfig.name = newKey;
  configs[newKey] = newConfig;
  configStore.set(configs as Record<string, StrategyVars>);
  await store.set(CONFIG_KEY, configs);
  await store.save();
}


export async function updateConfig(key: string, config: StrategyVars) {
  const store = await load(CONFIG_KEY, { autoSave: true });
  const configs = (await store.get(CONFIG_KEY)) as Record<string, StrategyVars>;
  if (!configs) {
    console.log("No configs found in store to update:", key);
    return;
  }
  console.log("Updating config in store:", key);
  configs[key] = config;
  configStore.set(configs as Record<string, StrategyVars>);
  await store.set(CONFIG_KEY, configs);
  await store.save();
}
