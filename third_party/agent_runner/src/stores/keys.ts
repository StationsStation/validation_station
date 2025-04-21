import { writable } from 'svelte/store';
import { load } from '@tauri-apps/plugin-store';
import { invoke } from '@tauri-apps/api/core';

const CONFIG_KEY = 'keys';


const DEFAULT_KEY_FILE = "ethereum_private_key.txt"

export const keyStore = writable<Record<string, string>>({});

// Load from Tauri store and update Svelte store
export async function loadKeysFromStore() {
  const store = await load(CONFIG_KEY, { autoSave: true });
  const raw = await store.get(CONFIG_KEY);
  const data = (raw ?? {}) as Record<string, string>;
  keyStore.set(data);
  console.log("Loaded keys from store:", data);
  return data;
}

// Save to Tauri store and update Svelte store
export async function saveKeysToStore(keys: Record<string, string>) {
  const store = await load(CONFIG_KEY, { autoSave: true });
  await store.set(CONFIG_KEY, keys);
  await store.save();
  keyStore.set(keys);
  console.log("Saved keys to store:", keys);
}

export async function removeKeyFromStore(key: string) {
  const store = await load(CONFIG_KEY, { autoSave: true });
  const keys = (await store.get(CONFIG_KEY)) as Record<string, string>;
  if (!keys) {
    console.log("No keys found in store to remove:", key);
    return;
  }
  console.log("Removing key from store:", key);
  delete keys[key];
  keyStore.set(keys as Record<string, string>);
  await store.set(CONFIG_KEY, keys);
  await store.save();
}

export async function copyKey(id: string, newKey: string) {
  const store = await load(CONFIG_KEY, { autoSave: true });
  const keys = (await store.get(CONFIG_KEY)) as Record<string, string>;
  if (!keys) {
    console.log("No keys found in store to copy:", id);
    return;
  }
  console.log("Copying key in store:", id, "to", newKey);
  const key = keys[id];
  if (!key) {
    console.log("key not found in store to copy:", id);
    return;
  }
  let newData = String(key);
  keys[newKey] = newData;
  keyStore.set(keys as Record<string, string>);
  await store.set(CONFIG_KEY, keys);
  await store.save();
}


export async function updatekey(key: string, data: string) {
  const store = await load(CONFIG_KEY, { autoSave: true });
  const keys = (await store.get(CONFIG_KEY)) as Record<string, string>;
  if (!keys) {
    console.log("No keys found in store to update:", key);
    return;
  }
  console.log("Updating key in store:", key);
  keys[key] = data;
  keyStore.set(keys as Record<string, string>);
  await store.set(CONFIG_KEY, keys);
  await store.save();
}


export async function generateKeyFile(keyName: string) {
  // TODO: Implement this function to generate a key file
   let config = {
      keyName: keyName,
      keyFile: DEFAULT_KEY_FILE,
    }
    console.log("Generating key file with config:", config);
    let key_path = await invoke<string>("generate_key_file", {
      "keyName": keyName,
      "keyFile": DEFAULT_KEY_FILE,
    });
    console.log("Generated key file:", key_path);
    let keys = await loadKeysFromStore();
    keys[keyName] = key_path;
    keyStore.set(keys);
    await saveKeysToStore(keys);
    return key_path;
}