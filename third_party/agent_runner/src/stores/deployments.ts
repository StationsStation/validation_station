import { writable } from 'svelte/store';
import { load } from '@tauri-apps/plugin-store';
import { invoke } from '@tauri-apps/api/core';
import type {  StrategyVars } from "./../lib/components/AgentBuilder.svelte";

const CONFIG_KEY = 'deployments';

export const deploymentStore = writable<Record<string, Deployment>>({});



export type Deployment = {
  name: string;
  keyPath: string;
  configData: StrategyVars;
  deploymentId: string;
};


export async function loadDeploymentsFromStore() {
  const store = await load(CONFIG_KEY, { autoSave: true });
  const raw = await store.get(CONFIG_KEY);
  const data = (raw ?? {}) as Record<string, Deployment>;
  deploymentStore.set(data);
  console.log("Loaded deployments from store:", data);
  return data;
}

export async function createDeployment(deploymentName: string, 
  keyPath: string,
  configData: StrategyVars,
) {
  const store = await load(CONFIG_KEY, { autoSave: true });

  const raw = await store.get(CONFIG_KEY);
  let data = (raw ?? {}) as Record<string, Deployment>;
  if (!data) {
    data = {};
  }
  let deployment: Deployment = {
    name: deploymentName,
    keyPath: keyPath,
    configData: configData,
    deploymentId: "",
  };
  data[deploymentName] = deployment;
  console.log("Saved deployment to store:", data);
  console.log("Creating deployment in store:", deploymentName, keyPath, configData);

  let envVars = Object.entries(configData.vars)
    .map(([key, value]) => {
      return {
        key, 
        value
      };
    })

  let mappedEnvVars: Record<string, string> = {};
  Object.entries(envVars).map(([key, value]) => {
    mappedEnvVars[value.key] = value.value.value;
  }
  );

  console.log("Starting agent with env vars", mappedEnvVars);

  let deploymentId: string = await invoke("start_container_command", {
      config: {
        privateKeyPath: keyPath,
        environmentVars: mappedEnvVars,
      }
  });

  deployment.deploymentId = deploymentId;
  data[deploymentName] = deployment;
  await store.set(CONFIG_KEY, data);
  await store.save();
  deploymentStore.set(data);


  return deployment;
}

export async function listDeployments() {
  const store = await load(CONFIG_KEY, { autoSave: true });
  const raw = await store.get(CONFIG_KEY);
  const data = (raw ?? {}) as Record<string, Deployment>;
  deploymentStore.set(data);
  console.log("Loaded deployments from store:", data);
  return data;
}


