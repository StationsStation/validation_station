
<script lang="ts">

  import { invoke } from '@tauri-apps/api/core';
  import { AgentStatus, type Agent } from '../types/src_tauri';
  import { onDestroy, onMount } from 'svelte';
  import { afterUpdate } from 'svelte';
import { exists, BaseDirectory } from '@tauri-apps/plugin-fs';
// when using `"withGlobalTauri": true`, you may use
// const { exists, BaseDirectory } = window.__TAURI__.fs;

import { open } from '@tauri-apps/plugin-dialog';

async function selectPrivateKey() {
  const selected = await open({
    title: 'Select Private Key File',
    multiple: false,
    filters: [{ name: 'private key files', extensions: ['txt'] }],
  });

  if (typeof selected === 'string') {
    privateKeyPath = selected;
  }
}
  let selectedAgentId: string | null = null;
  let logs: string = "";
  let isLogsModalOpen = false;

  let agents: Agent[] = [];
  let isStopping: Record<string, boolean> = {};

  let isFollowingLogs = true;
  let logInterval: number | null = 10;



  // config
  let isConfigModalOpen = false;
  let privateKeyPath = "";
  let environmentPath = "";



  async function selectEnvironmentFile() {
    console.log("Selecting environment file...");
    const selected = await open({
      title: 'Select Environment File',
      multiple: false,
      filters: [{ name: 'Environment', extensions: ['config', 'txt'] }],
    });
    if (typeof selected === 'string') {
      environmentPath = selected;
    }
  }
  

  let logContainer: HTMLPreElement;

  afterUpdate(() => {
    if (logContainer && isFollowingLogs) {
      logContainer.scrollTop = logContainer.scrollHeight;
    }
  }); 
  async function openLogsModal(agentId: string) {
    console.log("Opening logs modal for agent:", agentId);
    selectedAgentId = agentId;
    isLogsModalOpen = true;
    await fetchLogs(); // no param
  }
  
  async function fetchLogs() {
    if (!selectedAgentId) return;
    logs = await invoke("get_container_logs", { id: selectedAgentId });

    // If following is enabled, scroll to bottom after fetching new logs
    if (isFollowingLogs && logContainer) {
      // Use setTimeout to ensure this happens after the DOM updates
      setTimeout(() => {
        logContainer.scrollTop = logContainer.scrollHeight;
      }, 0);
    }
  }

  $: if (isLogsModalOpen && isFollowingLogs && selectedAgentId) {
    cleanupLogInterval();
    logInterval = setInterval(fetchLogs, 3000);
  } else if (!isLogsModalOpen || !isFollowingLogs) {
    cleanupLogInterval();
  }


  async function stopAgent(id: string) {
    isStopping[id] = true;
    await invoke("stop_container_command", { id });
    await fetchAgents();
    isStopping[id] = false;
  }

  async function fetchAgents() {
    agents = await invoke<Agent[]>("list_agents");
  }

  async function startAgent(id: string) {
    await invoke("start_container_command", { id });
    await fetchAgents();
  }

  async function createNewAgent() {
    let config = {
      privateKeyPath,
      environmentPath,
    }
    await invoke("start_container_command", {config});
    await fetchAgents(); // refresh list after new agent is started
  }

  function cleanupLogInterval() {
    if (logInterval) {
      clearInterval(logInterval);
      logInterval = null;
    }
  }

  // Update the modal close handler
  function closeLogsModal() {
    isLogsModalOpen = false;
    cleanupLogInterval();
  }

  // Add to onDestroy
  onDestroy(() => {
    clearInterval(interval);
    cleanupLogInterval();
  });
  // Fetch agents when the component mounts


  async function restartAgent(id: string) {
    await invoke("restart_container_command", { id });
    await fetchAgents();
  }

  async function pauseAgent(id: string) {
  await invoke("pause_container_command", { id });
  await fetchAgents();
}

  async function unpauseAgent(id: string) {
    await invoke("unpause_container_command", { id });
    await fetchAgents();
  }

  function timeAgo(timestamp: string): string {
    const now = new Date();
    const then = new Date(timestamp);
    const diff = Math.floor((now.getTime() - then.getTime()) / 1000); // seconds

    if (diff < 5) return "just now";
    if (diff < 60) return `${diff} seconds ago`;
    if (diff < 3600) return `${Math.floor(diff / 60)} minutes ago`;
    if (diff < 86400) return `${Math.floor(diff / 3600)} hours ago`;

    return `${Math.floor(diff / 86400)} days ago`;
  }

  // run fetchAgents in a loop
  let interval = setInterval(fetchAgents, 500);
  // clear interval on component destroy
  onDestroy(() => {
    clearInterval(interval);
  });


  onMount(fetchAgents);
</script>

<div class="terminal-shell">

<main class="container">

  <h1>Derolas</h1>
  <p class="blink">Welcome to the future of decentralised Market Making</p>
  <p>Click on the logos to learn more about the technologies used in this project.</p>

  <div class="container">
  {#if isLogsModalOpen}
    <button class="modal-backdrop" aria-label="Close logs modal" on:click={() => isLogsModalOpen = false} on:keydown={(e) => { if (e.key === 'Enter' || e.key === ' ') isLogsModalOpen = false; }}></button>
    <div class="log-modal">
      <div class="modal-header">
        <div class="modal-title">
          <h3>Logs for Agent</h3>
          <code class="agent-id">{selectedAgentId}</code>
        </div>
      
        <div class="modal-controls">
          <label class="follow-toggle">
            <input type="checkbox" bind:checked={isFollowingLogs} />
            Follow
          </label>
          <button class="btn-close" on:click={closeLogsModal}>×</button>
        </div>
      </div>
        <pre class="terminal-log" bind:this={logContainer}>
          {logs}
        </pre>

    </div>
  {/if}

<main class="main-container">
  <!-- CONFIG SECTION -->
  <section class="agent-status">
    <div class="status-bar">
      <h2 class="status-title">:: CONFIG</h2>
      <button class="new-agent-btn" on:click={() => isConfigModalOpen = !isConfigModalOpen}>
        {isConfigModalOpen ? '− Close Config' : '+ Config'}
      </button>
    </div>

    <div class="config-container">
      {#if !privateKeyPath || !environmentPath}
        <div class="alert">
          ⚠️ Private Key Path and Environment Path are required.
        </div>
      {/if}

      {#if isConfigModalOpen}
        <div class="status-card config-card">
          <div class="config-field">
            <label for="private-key-path">🔐 <strong>Private Key Path</strong></label>
            <input id="private-key-path" type="text" value={privateKeyPath} readonly />
            <button on:click={selectPrivateKey}>Select Private Key</button>
          </div>

          <div class="config-field">
            <label for="environment-path">🌱 <strong>Environment Path</strong></label>
            <code id="environment-path">{environmentPath || '[Not selected]'}</code>
            <button on:click={selectEnvironmentFile}>Select Environment</button>
          </div>
        </div>
      {/if}
    </div>
  </section>

  <!-- AGENTS SECTION -->
  <section class="agent-status">
    <div class="status-bar">
      <h2 class="status-title">:: AGENTS</h2>
      <button class="create" on:click={createNewAgent}>+ New Agent</button>
    </div>

    
<div class="agent-table-wrapper">
  <table class="agent-table">
    <thead>
      <tr>
        <th>Status</th>
        <th>Address</th>
        <th>Last Seen</th>
        <th>Container ID</th>
        <th>Actions</th>
      </tr>
    </thead>
    <tbody>
      {#each agents as agent}
        <tr class="{isStopping[agent.id] ? 'stopping' : ''}">
          <td>
            <span class="status-dot {agent.status}"></span>
            <span class="status-label {agent.status}">{agent.status}</span>
          </td>

          <td><code>{agent.address}</code></td>
          <td>{timeAgo(agent.lastSeenTimestamp)}</td>
          <td>
            {#if agent.status in [AgentStatus.Running, AgentStatus.Paused]}
              <code>{agent.id}</code>
            {:else}
              —
            {/if}
          </td>
            <td>
              {#if isStopping[agent.id]}
                <span class="stopping-label">Stopping...</span>
              {:else}
                <div class="agent-actions">
                  {#if agent.status === AgentStatus.Running}
                    <button class="btn tiny pause" on:click={() => pauseAgent(agent.id)}>Pause</button>
                    <button class="btn tiny stop" on:click={() => stopAgent(agent.id)}>Stop</button>
                  {:else if agent.status === 'Paused'}
                    <button class="btn tiny unpause" on:click={() => unpauseAgent(agent.id)}>Unpause</button>
                  {:else if agent.status === AgentStatus.Stopped}
                    <button class="btn tiny start" on:click={() => startAgent(agent.id)}>Start</button>
                  {/if}
                
                  {#if agent.status in [AgentStatus.Running, AgentStatus.Paused]}
                    <button class="btn tiny restart" on:click={() => restartAgent(agent.id)}>Restart</button>
                  {/if}
                
                  <button class="btn tiny logs" on:click={() => openLogsModal(agent.id)}>Logs</button>
                </div>
              {/if}
            </td>

        </tr>
      {/each}
    </tbody>
  </table>
</div>




    </div>

  <!-- FOOTER -->
  <footer class="row logos">
    <a href="https://github.com/StationsStation/capitalisation_station" target="_blank">
      <img src="/derolas.png" class="logo" alt="Derolas Logo" width="100" height="200"/>
    </a>
    <a href="https://olas.network" target="_blank">
      <img src="/olas.png" class="logo" alt="Olas Logo" />
    </a>
    <a href="https://derive.xyz" target="_blank">
      <img src="/derive.png" class="logo" alt="Derive Logo" width="80" height="10"/>
    </a>
  </footer>
</main>
</div>



<style global>
/* === CYBERPUNK TERMINAL MODE === */
@import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&display=swap');

:root {
  font-family: 'Share Tech Mono', monospace;
  font-size: 16px;
  line-height: 1.6;
  font-weight: 400;

  background-color: #000000;
  color: #33ff33;

  text-shadow: 0 0 1px #33ff33;
  letter-spacing: 0.05em;

  font-synthesis: none;
  -webkit-font-smoothing: none;
  -moz-osx-font-smoothing: grayscale;

  background-image: repeating-linear-gradient(
    0deg,
    rgba(0, 0, 0, 0.9),
    rgba(0, 0, 0, 0.9) 1px,
    transparent 1px,
    transparent 2px
  );
}

/* === Container === */
.container {
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
  padding: 2rem;
}

/* === Glitchy Logo Style === */
.logo {
  height: 5rem;
  margin: 2rem;
  filter: drop-shadow(0 0 1em #33ff33);
  transition: filter 0.4s ease;
}

.logo.vite:hover {
  filter: drop-shadow(0 0 2em #00ffff);
}

.logo.svelte-kit:hover {
  filter: drop-shadow(0 0 2em #ff3e00);
}

.logo.tauri:hover {
  filter: drop-shadow(0 0 2em #ff00ff);
}

/* === Hacker Title === */
h1 {
  font-size: 2.5rem;
  color: #00ff00;
  text-shadow: 0 0 0.2em #00ff00, 0 0 1em #006600;
  margin-bottom: 1rem;
}

/* === Terminal Links === */
a {
  color: #00ffaa;
  text-decoration: none;
  transition: color 0.2s ease;
}

a:hover {
  color: #00ffee;
  text-shadow: 0 0 0.5em #00ffee;
}

/* === Inputs & Buttons === */
input,
button {
  font-family: inherit;
  font-size: 1rem;
  padding: 0.6em 1.2em;
  margin: 0.5rem 0;
  border: 1px solid #00ff00;
  border-radius: 4px;
  background-color: #000;
  color: #33ff33;
  box-shadow: 0 0 0.5em #00ff00;
  transition: all 0.2s ease;
  outline: none;
}

input {
  margin-right: 0.5rem;
}

button {
  cursor: pointer;
}

button:hover {
  background-color: #003300;
  color: #00ff00;
  box-shadow: 0 0 1em #00ff00;
}

button:active {
  background-color: #005500;
  border-color: #00ff00;
}

/* === Grid Row === */
.row {
  display: flex;
  justify-content: center;
  flex-wrap: wrap;
  gap: 1rem;
}

/* === Blinking Cursor Effect === */
.blink::after {
  content: '_';
  animation: blink 1s step-end infinite;
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}

/* Optional: override for light mode browsers */
@media (prefers-color-scheme: light) {
  :root {
    background-color: #000000;
    color: #33ff33;
  }
}

/* === AGENT STATUS SECTION === */
.agent-status {
  margin-top: 3rem;
  width: 100%;
  max-width: 800px;
  padding: 1rem;
  border-top: 1px solid #00ff00;
}

.status-title {
  font-size: 1.25rem;
  color: #00ff00;
  text-align: left;
  margin-bottom: 1rem;
  border-bottom: 1px solid #00ff00;
  padding-bottom: 0.5rem;
}

.status-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1rem;
}

.status-card {
  background-color: #000;
  border: 1px solid #00ff00;
  padding: 1rem;
  box-shadow: 0 0 0.5em #00ff00;
  text-align: left;
  font-size: 0.95rem;
  line-height: 1.4;
}

/* === STATUS COLORS === */
.status {
  font-weight: bold;
  padding: 0.1rem 0.4rem;
  border-radius: 4px;
}

.status.Running{
  color: #00ff00;
  text-shadow: 0 0 0.2em #00ff00;
}

.status.stopped {
  color: #ffaa00;
  text-shadow: 0 0 0.2em #ffaa00;
}
.status.starting {
  color: #00ffff;
  text-shadow: 0 0 0.2em #00ffff;
}
.status.stopping {
  color: #ff00ff;
  text-shadow: 0 0 0.2em #ff00ff;
}

.status.unhealthy {
  color: #ff0033;
  text-shadow: 0 0 0.2em #ff0033;
}
/* Base button class */
button.btn {
  font-family: inherit;
  font-size: 1rem;
  padding: 0.6em 1.2em;
  margin: 0.3rem;
  border: 1px solid #00ff00;
  border-radius: 4px;
  background-color: #000;
  color: #33ff33;
  box-shadow: 0 0 0.5em #00ff00;
  transition: all 0.2s ease;
  outline: none;
}

/* Green Start Button */
button.start {
  border-color: #00ff00;
  color: #00ff00;
  box-shadow: 0 0 0.5em #00ff00;
}
button.start:hover {
  background-color: #003300;
  box-shadow: 0 0 1em #00ff00;
}

/* Red Stop Button */
button.stop {
  border-color: #ff0033;
  color: #ff0033;
  box-shadow: 0 0 0.5em #ff0033;
}
button.stop:hover {
  background-color: #330000;
  box-shadow: 0 0 1em #ff0033;
}

/* Yellow Restart Button */
button.restart {
  border-color: #ffff33;
  color: #ffff33;
  box-shadow: 0 0 0.5em #ffff33;
}
button.restart:hover {
  background-color: #333300;
  box-shadow: 0 0 1em #ffff33;
}

/* Bright Green for Create */
button.create {
  border-color: #00ffcc;
  color: #00ffcc;
  box-shadow: 0 0 0.5em #00ffcc;
}
button.create:hover {
  background-color: #003333;
  box-shadow: 0 0 1em #00ffcc;
}

/* Pause and Unpause */
button.pause {
  border-color: #00aaff;
  color: #00aaff;
  box-shadow: 0 0 0.5em #00aaff;
}
button.pause:hover {
  background-color: #002244;
  box-shadow: 0 0 1em #00aaff;
}

button.unpause {
  border-color: #ffaa00;
  color: #ffaa00;
  box-shadow: 0 0 0.5em #ffaa00;
}
button.unpause:hover {
  background-color: #332200;
  box-shadow: 0 0 1em #ffaa00;
}

/* Logs */
button.logs {
  border-color: #00ff00;
  color: #00ff00;
  box-shadow: 0 0 0.5em #00ff00;
}
button.logs:hover {
  background-color: #003300;
  box-shadow: 0 0 1em #00ff00;
}
button.logs:disabled {
  background-color: #000;
  color: #333;
  box-shadow: none;
  cursor: not-allowed;
}
button.logs:disabled:hover {
  background-color: #000;
  box-shadow: none;
}

/* Modal styling for the logs */

.modal-backdrop {
  position: fixed;
  top: 0; left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 255, 0, 0.05);
  z-index: 10;
}

.log-modal {
  position: fixed;
  top: 10%;
  left: 50%;
  transform: translateX(-50%);
  width: 90vw;
  max-width: 900px;
  background-color: #000;
  border: 1px solid #00ff00;
  box-shadow: 0 0 1em #00ff00;
  padding: 1rem;
  z-index: 9999;
  overflow: visible; /* ✅ let internal scroll handle overflow */
  max-height: 80vh;   /* ✅ prevents overflow beyond screen */
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #00ff00;
  padding-bottom: 0.5rem;
}

.modal-title {
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.agent-id {
  font-size: 0.75rem;
  color: #00ff88;
  opacity: 0.8;
  word-break: break-all;
}

.modal-controls {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.follow-toggle {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  font-size: 0.85rem;
  color: #00ff00;
}

.follow-toggle input[type="checkbox"] {
  width: 1rem;
  height: 1rem;
  accent-color: #00ff00;
  cursor: pointer;
}

.button.close {
  background: #000;
  color: #00ff00;
  border: 1px solid #00ff00;
  font-size: 1.2rem;
  line-height: 1;
  padding: 0.3rem 0.7rem;
  cursor: pointer;
  box-shadow: 0 0 0.5em #00ff00;
}
.log-output {
  background: #000;
  color: #00ff00;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.9rem;
  max-height: 60vh;
  overflow-y: auto;
    text-align: left; /* ← Add this */
  padding: 1rem;
  border: 1px solid #00ff00;
  box-shadow: 0 0 0.5em #00ff00;
  white-space: pre-wrap;
  line-height: 1.4;
}

.log-line {
  padding: 2px 0;
}

.log-error {
  color: #ff3333;
  text-shadow: 0 0 0.2em #ff3333;
}

.log-success {
  color: #00ffcc;
  text-shadow: 0 0 0.2em #00ffcc;
}

.log-cmd {
  color: #ffff00;
  text-shadow: 0 0 0.2em #ffff00;
}

.log-indent {
  padding-left: 2rem;
  opacity: 0.85;
}

.terminal-log {
  background: #000;
  color: #00ff00;
  font-family: 'Share Tech Mono', monospace;
  font-size: 0.85rem;
  line-height: 1.5;
  white-space: pre-wrap;
  padding: 1rem;
  max-height: 60vh;
  overflow-y: auto;
  text-align: left;
  border: 1px solid #00ff00;
  box-shadow: 0 0 0.5em #00ff00;
}
/* === Status Card Improvements === */
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 0.75rem;
  border-bottom: 1px solid #00ff00;
  padding-bottom: 0.5rem;
}

.card-body {
  margin-bottom: 1rem;
}

.info-row {
  margin-bottom: 0.5rem;
}

.address, .container-id {
  color: #00ffcc;
  font-family: 'Share Tech Mono', monospace;
  word-break: break-all;
}

.card-actions {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-top: 1rem;
  border-top: 1px solid #00ff00;
  padding-top: 0.75rem;
}

.button-group {
  display: flex;
  justify-content: left;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.logs-container {
  display: flex;
  justify-content: center;
  width: 100%;
}

/* Schema for config card */
.config-card {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
  max-width: 600px;
  margin: 0 auto;
}

.config-field {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.config-field label {
  font-size: 0.9rem;
  color: #00ff00;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.config-field code {
  background: black;
  padding: 0.25rem 0.5rem;
  border: 1px solid #00ff00;
  color: #00ff00;
  font-family: monospace;
  font-size: 0.8rem;
  overflow-wrap: break-word;
  word-break: break-word;
  white-space: pre-wrap;
  max-width: 100%;
  display: block;
}



.main-container {
  max-width: 960px;
  margin: 0 auto;
  padding: 0.1rem;
  display: flex;
  flex-direction: column;
  gap: 0.1rem;
  box-sizing: border-box;
  padding-top: 0.1rem;
}



@keyframes blink {
  50% { border-color: transparent; }
}
@keyframes typing {
  from { width: 0 }
  to { width: 100% }
}

.typewriter {
  display: inline-block;
  overflow: hidden;
  white-space: nowrap;
  border-right: 2px solid #00ff00;
  width: 0;
  animation: typing 1s steps(8), blink 0.75s step-end infinite;
}
.terminal-shell {
  max-width: 960px;
  margin: 2rem auto;
  padding: 2rem;
  border: 2px solid #00ff00;
  border-radius: 0.5rem;
  box-shadow: 0 0 20px #00ff00aa;
  background-color: rgba(0, 0, 0, 0.9);
}

.terminal-header {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 1rem;
}

.circle {
  width: 10px;
  height: 10px;
  border-radius: 50%;
}

.red {
  background: #ff4b4b;
}

.yellow {
  background: #ffcc00;
}

.green {
  background: #00ff00;
}
.status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.status-title {
  font-size: 1rem;
  color: #00ff00;
  text-transform: uppercase;
  font-weight: bold;
  border-bottom: 2px solid #00ff00;
  padding-bottom: 0.25rem;
  margin: 0;
}

.new-agent-btn {
  padding: 0.25rem 1rem;
  border: 1px solid #00ff00;
  background: transparent;
  color: #00ff00;
  cursor: pointer;
  text-transform: uppercase;
  font-family: inherit;
  font-size: 0.85rem;
  box-shadow: 0 0 5px #00ff00;
}
.new-agent-btn:hover {
  background-color: #00ff0022;
}
.status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1rem;
}

.status-title {
  font-size: 1rem;
  color: #00ff00;
  text-transform: uppercase;
  font-weight: bold;
  border-bottom: 2px solid #00ff00;
  padding-bottom: 0.25rem;
  margin: 0;
}

.new-agent-btn {
  padding: 0.25rem 1rem;
  border: 1px solid #00ff00;
  background: transparent;
  color: #00ff00;
  cursor: pointer;
  text-transform: uppercase;
  font-family: inherit;
  font-size: 0.85rem;
  box-shadow: 0 0 5px #00ff00;
}

.new-agent-btn:hover {
  background-color: #00ff0022;
}

.status-dot {
  display: inline-block;
  width: 0.65rem;
  height: 0.65rem;
  border-radius: 50%;
  margin-right: 0.5rem;
  vertical-align: middle;
}

.status-dot.Running {
  background-color: #00ff00;
  animation: pulse 1.2s infinite;
}

.status-dot.Paused {
  background-color: #ffaa00;
}

.status-dot.Stopped {
  background-color: #ff4444;
  opacity: 0.5;
}

.status-dot.Stopping {
  background-color: #ff00ff;
  animation: blink 1s steps(1) infinite;
}

/* animations */
@keyframes pulse {
  0% { box-shadow: 0 0 2px #00ff00; }
  50% { box-shadow: 0 0 8px #00ff00; }
  100% { box-shadow: 0 0 2px #00ff00; }
}

@keyframes blink {
  50% { opacity: 0; }
}

.agent-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  align-items: center;
}

.btn.tiny {
  padding: 0.2rem 0.5rem;
  font-size: 0.75rem;
  line-height: 1;
  border-radius: 2px;
}

.stopping-label {
  color: #ff00ff;
  font-weight: bold;
  font-family: monospace;
  animation: blink 1s steps(1) infinite;
}

@keyframes blink {
  50% {
    opacity: 0;
  }
}

.agent-table th,
.agent-table td {
  padding: 0.6rem 1rem; /* wider horizontal padding */
  border-bottom: 1px dashed #00ff00;
  border-right: 1px dashed #00ff00;
  text-align: left;
  vertical-align: middle;
}

.agent-table th:last-child,
.agent-table td:last-child {
  border-right: none;
}

.agent-table th {
  font-size: 0.8rem;
  color: #00ffaa;
  text-transform: uppercase;
  letter-spacing: 1px;
  padding-bottom: 0.3rem;
}

.agent-table td {
  white-space: nowrap;
}

.agent-table tbody tr:nth-child(odd) {
  background-color: rgba(0, 255, 0, 0.03);
}

</style>
