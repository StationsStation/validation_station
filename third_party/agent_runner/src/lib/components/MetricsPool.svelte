<script lang="ts">

  import { HandCoins, Clock, Users, Gift, DollarSign, CircleDollarSign, Info, Timer, BrainCircuit } from "lucide-svelte";
  import * as Button from "./ui/button";
  import * as Badge from "./ui/badge";
  import * as Tooltip from "./ui/tooltip";
  import * as Progress from "./ui/progress";
  import * as Alert from "./ui/alert";
  import * as Accordion from "./ui/accordion";
  import { ChevronDown, } from "lucide-svelte";
	import { WC, disconnectWagmi} from 'svelte-wagmi';
  import { defaultConfig } from 'svelte-wagmi';
  import * as Card from "$lib/components/ui/card";
	import { chainId } from 'svelte-wagmi';
	import { signerAddress } from 'svelte-wagmi';
import { getVersion } from '@tauri-apps/api/app';
    import { onMount } from 'svelte';
 // src/lib/wagmi.ts
// import { defaultConfig } from 'svelte-wagmi';
    import { walletConnect } from '@wagmi/connectors';
    import Separator from './ui/separator/separator.svelte';
    import { Root } from "./ui/dialog";

let PUBLIC_WALLETCONNECT_ID = "189298bf7ea32b9f16f1369599ad0ad4"


let isRunningInTauri = false;
$: isRunningInTauri;


  let epochProgress = 60; // e.g., 60% through
  let epochLength = 100; // e.g., 100 blocks

  $: chainId
  $: signerAddress

	async function connect() {
        console.log('Connecting to Ethereum...');
		try {
            // Initialize WalletConnect
            console.log('Connecting to WalletConnect...');
			let res = await WC();
            console.log('WalletConnect connected' + res);
            console.log(res);
            console.log('WalletConnect session:', chainId);
            console.log('WalletConnect accounts:', signerAddress);

		} catch (e) {
			console.error('WalletConnect failed', e);
		}
	}

  	import { connected } from 'svelte-wagmi';


async function isTauri(): Promise<boolean> {
  try {
    await getVersion();
    isRunningInTauri = true;
  } catch {
    isRunningInTauri = false;
  }
  return isRunningInTauri;
}

	onMount(async () => {
    let isRunningInTauri = await isTauri();
    console.log('Running in Tauri:', isRunningInTauri);
    if (isRunningInTauri) {
      console.log('Running in Tauri, not initializing WalletConnect');
      return;
    } 

    console.log('Initializing WalletConnect...');
    		const wagmi = defaultConfig({
			appName: 'erc.kit',
			walletConnectProjectId: PUBLIC_WALLETCONNECT_ID,
			connectors: [
	walletConnect({
    		projectId: PUBLIC_WALLETCONNECT_ID,
    		metadata: {
    			name: 'erc.kit',
    			description: 'Tauri Dev App',
    			url: 'http://localhost',
    			icons: ['https://walletconnect.com/walletconnect-logo.png']
    		},
    		relayUrl: 'wss://relay.walletconnect.com'
    	})
    ]
		});

		await wagmi.init();
	});



  async function contribute() {
    console.log('Contributing ETH...');
    // Logic to contribute ETH
  }

  async function claim() {
    console.log('Claiming OLAS...');
    // Logic to claim OLAS
  }

  async function endEpoch() {
    console.log('Ending epoch...');
    // Logic to end the epoch
  }


 
</script>

{#if !isRunningInTauri}
<header class="w-full border-b border-green-700 bg-black text-green-400 font-mono text-sm px-4 py-3 flex justify-between items-center">
  <div class="font-bold tracking-wide text-green-300">
    🧭 Derolas
  </div>

  <div class="flex items-center gap-4">
    {#if $signerAddress}
      <div class="flex flex-col text-right leading-tight">
        <span class="text-green-500">Chain: {$chainId}</span>
        <span class="text-green-300 truncate max-w-[160px]">{$signerAddress}</span>
      </div>
        <Button.Root
          class="bg-red-500 hover:bg-red-400 text-black font-bold px-3 py-1 rounded transition"
          on:click={() => {
            console.log('Disconnecting...');
            disconnectWagmi();
          }}>
          Disconnect
        </Button.Root>
    {:else}
      <Button.Root
        class="bg-green-500 hover:bg-green-400 text-black font-bold px-3 py-1 rounded transition"
        on:click={connect}>
        Connect Wallet
      </Button.Root>
    {/if}
  </div>
</header>
{/if}

  <Card.Root class="space-y-8 p-6 rounded-xl shadow-lg border border-green-500 bg-black text-green-400 font-mono">
  <!-- Header -->
  <Card.Header class="text-center space-y-2">
    <Card.Title class="text-2xl font-bold tracking-tight">Epochal Reward Split (ERS)</Card.Title>
      <Separator class="my-2" />
    <Card.Description class="text-green-500 text-sm">
      Contribute ETH → Claim OLAS. Rewards distributed at epoch end.
    </Card.Description>
  </Card.Header>


  <!-- Progress Bar -->
  <div class="space-y-1">
    <Progress.Root value={epochProgress} class="h-2 rounded bg-green-900 transition-all" />
    <div class="text-xs text-right text-green-600">{epochProgress}% complete</div>
  </div>

<!-- Final Epoch Summary -->
<div class="space-y-6 text-green-300 max-w-2xl mx-auto">
  <!-- Epoch Breakdown with callouts -->
  <div class="space-y-6 text-green-300 max-w-2xl mx-auto">
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
    
    <!-- Epoch Progress Card -->
    <div class="bg-green-950 border border-green-700 p-4 rounded-lg flex flex-col gap-2">
      <div>
        <span class="inline-block text-xs bg-green-800 border border-green-600 text-green-300 rounded px-2 py-1">
          {epochProgress} blocks completed
        </span>
      </div>
      <p class="text-sm text-green-500">
        Each epoch runs for {epochLength} blocks.
      </p>
    </div>

    <!-- Reward Distribution Card -->
    <div class="bg-green-950 border border-green-700 p-4 rounded-lg flex flex-col gap-2">
      <div>
        <span class="inline-block text-xs bg-green-800 border border-green-600 text-green-300 rounded px-2 py-1">
          Proportional Split
        </span>
      </div>
      <p class="text-sm text-green-500">
        Reward OLAS is split proportionally based on ETH donated.
      </p>
    </div>

  </div>
</div>


<Card.Root>
  <Card.Content>
    <ul class="space-y-6">
      
      <!-- ETH Donations -->
      <li class="flex items-start gap-4">
        <HandCoins class="w-8 h-8 text-green-300 mt-1" />
        <p>
          <strong class="text-green-100">ETH donations:</strong> Sent directly into the Balancer pool, increasing protocol liquidity in real time.
        </p>
      </li>

      <!-- OLAS Rewards -->
      <li class="flex items-start gap-4">
        <Gift class="w-8 h-8 text-green-300 mt-1" />
        <p>
          <strong class="text-green-100">OLAS rewards:</strong> Distributed at the end of each epoch based on your pro-rata contribution to the donation pool.
        </p>
      </li>

      <!-- Unclaimed Rewards -->
      <li class="flex items-start gap-4">
        <CircleDollarSign class="w-8 h-8 text-green-300 mt-1" />
        <p>
          <strong class="text-green-100">Unclaimed rewards:</strong> Recycled into the pool, improving long-term liquidity and fairness.
        </p>
      </li>

      <!-- Cooperative Strategy -->
      <li class="flex items-start gap-4">
        <Users class="w-8 h-8 text-green-300 mt-1" />
        <p>
          <strong class="text-green-100">Collaborative, Not Competitive:</strong> The optimal strategy is for everyone to donate the minimum and receive equal shares.
        </p>
      </li>

      <!-- Prisoner's Dilemma -->
      <li class="flex items-start gap-4">
        <BrainCircuit class="w-8 h-8 text-green-300 mt-1" />
        <p>
          <strong class="text-green-100">Prisoner's Dilemma:</strong> Each epoch, you can donate more to increase your share of rewards — but if everyone does this, rewards are diluted.
        </p>
      </li>

    </ul>
  </Card.Content>
</Card.Root>
 


  <!-- High-emphasis Alert (with Call-to-Action) -->
<Card.Root class="bg-green-900 border border-green-600 text-green-300 px-4 py-5 rounded-lg">
  <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
    <!-- Info Section -->
    <div class="flex items-center gap-2 text-lg font-semibold">
      <CircleDollarSign class="w-5 h-5" />
      <span>Actions</span>
    </div>

    <!-- Action Buttons -->
    <div class="flex flex-wrap gap-3">
      <button
        class="bg-green-600 text-green-950 px-4 py-2 rounded-md font-semibold text-sm hover:bg-green-500 transition"
        on:click={contribute}
      >
        Contribute ETH
      </button>

      <button
        class="bg-green-800 text-green-100 border border-green-500 px-4 py-2 rounded-md font-semibold text-sm hover:bg-green-700 transition"
        on:click={claim}
      >
        Claim OLAS
      </button>
    <!-- End the epoch -->
      <button
        class="bg-green-600 text-green-950 px-4 py-2 rounded-md font-semibold text-sm hover:bg-green-500 transition"
        on:click={endEpoch}
      >
        End Epoch
      </button>
    </div>

    
  </div>
</Card.Root>

</div>
<!-- Epoch Metrics -->
<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
  <!-- Total Donations -->
  <Card.Root class="border border-green-700 bg-green-950 px-4 py-3 rounded-lg space-y-2">
    <Card.Header class="flex items-center gap-2">
      <HandCoins class="w-6 h-6 text-green-400" />
      <Card.Title class="text-base font-semibold">Donations</Card.Title>
    </Card.Header>
    <Card.Content class="text-center text-2xl font-bold">$2.65k</Card.Content>
  </Card.Root>

  <!-- Time Remaining -->
  <Card.Root class="border border-green-700 bg-green-950 px-4 py-3 rounded-lg space-y-2">
    <Card.Header class="flex items-center gap-2">
      <Clock class="w-6 h-6 text-green-400" />
      <Card.Title class="text-base font-semibold">Time Remaining</Card.Title>
    </Card.Header>
    <Card.Content class="text-center text-2xl font-bold">100</Card.Content>
  </Card.Root>

  <!-- Contributors -->
  <Card.Root class="border border-green-700 bg-green-950 px-4 py-3 rounded-lg space-y-2">
    <Card.Header class="flex items-center gap-2">
      <Users class="w-6 h-6 text-green-400" />
      <Card.Title class="text-base font-semibold">Contributors</Card.Title>
    </Card.Header>
    <Card.Content class="text-center text-2xl font-bold">6</Card.Content>
  </Card.Root>
</div>

<!-- Reward Metrics -->
<div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6">
  <!-- Reward Rate -->
  <Card.Root class="border border-green-700 bg-green-950 px-4 py-3 rounded-lg space-y-2">
    <Card.Header class="flex items-center gap-2">
      <Gift class="w-6 h-6 text-green-400" />
      <Card.Title class="text-base font-semibold">Reward Rate</Card.Title>
    </Card.Header>
    <Card.Description class="text-xs text-green-400 ml-8">
      OLAS per 1 USD donated
    </Card.Description>
    <Card.Content class="text-center text-2xl font-bold">675</Card.Content>
  </Card.Root>

  <!-- Min Donation -->
  <Card.Root class="border border-green-700 bg-green-950 px-4 py-3 rounded-lg space-y-2">
    <Card.Header class="flex items-center gap-2">
      <DollarSign class="w-6 h-6 text-green-400" />
      <Card.Title class="text-base font-semibold">Min Donation</Card.Title>
    </Card.Header>
    <Card.Description class="text-xs text-green-400 ml-8">
      Minimum required to join
    </Card.Description>
    <Card.Content class="text-center text-2xl font-bold">1 USD</Card.Content>
  </Card.Root>

  <!-- Effective Price -->
  <Card.Root class="border border-green-700 bg-green-950 px-4 py-3 rounded-lg space-y-2">
    <Card.Header class="flex items-center gap-2">
      <CircleDollarSign class="w-6 h-6 text-green-400" />
      <Card.Title class="text-base font-semibold">Effective Price</Card.Title>
    </Card.Header>
    <Card.Description class="text-xs text-green-400 ml-8">
      Estimated ETH per OLAS
    </Card.Description>
    <Card.Content class="text-center text-2xl font-bold">0.01</Card.Content>
  </Card.Root>
</div>

  <Separator />

<!-- TVL Metrics -->
<div class="grid grid-cols-1 sm:grid-cols-3 gap-4 mt-6">
  <!-- Reward Rate -->
  <Card.Root class="border border-green-700 bg-green-950 px-4 py-3 rounded-lg space-y-2">
    <Card.Header class="flex items-center gap-2">
      <Gift class="w-6 h-6 text-green-400" />
      <Card.Title class="text-base font-semibold">Current Rate</Card.Title>
    </Card.Header>
    <Card.Description class="text-xs text-green-400 ml-8">
      OLAS per 1 USD donated
    </Card.Description>
    <Card.Content class="text-center text-2xl font-bold">675</Card.Content>
  </Card.Root>

  <!-- Min Donation -->
  <Card.Root class="border border-green-700 bg-green-950 px-4 py-3 rounded-lg space-y-2">
    <Card.Header class="flex items-center gap-2">
      <DollarSign class="w-6 h-6 text-green-400" />
      <Card.Title class="text-base font-semibold">Min Donation</Card.Title>
    </Card.Header>
    <Card.Description class="text-xs text-green-400 ml-8">
      Minimum required to join
    </Card.Description>
    <Card.Content class="text-center text-2xl font-bold">1 USD</Card.Content>
  </Card.Root>

  <!-- Effective Price -->
  <Card.Root class="border border-green-700 bg-green-950 px-4 py-3 rounded-lg space-y-2">
    <Card.Header class="flex items-center gap-2">
      <CircleDollarSign class="w-6 h-6 text-green-400" />
      <Card.Title class="text-base font-semibold">Effective Price</Card.Title>
    </Card.Header>
    <Card.Description class="text-xs text-green-400 ml-8">
      Estimated ETH per OLAS
    </Card.Description>
    <Card.Content class="text-center text-2xl font-bold">0.01</Card.Content>
  </Card.Root>
</div>

</Card.Root>