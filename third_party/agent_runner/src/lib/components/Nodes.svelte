<script lang="ts">
  import { fade } from 'svelte/transition';

  import { switchNetwork, } from '@wagmi/core';
  import type Provider from "@walletconnect/ethereum-provider";
  import type { Address, ProviderConnectInfo, Chain } from "viem";
  import { HandCoins, Clock, Users, Gift, DollarSign, CircleDollarSign, Info, Timer, BrainCircuit, TimerReset, Sparkles, Flame, SeparatorVertical, StopCircle } from "lucide-svelte";
  import * as Button from "./ui/button";
  import * as Input from "./ui/input";
  import * as Progress from "./ui/progress";
  import * as Seperator from "./ui/separator";
  import * as Alert from "./ui/alert";
  import * as Card from "$lib/components/ui/card";
import { getVersion } from '@tauri-apps/api/app';
    import { onDestroy, onMount } from 'svelte';
import { walletConnect } from '@wagmi/connectors';
import Separator from './ui/separator/separator.svelte';
import { getAccount, readContract, type CreateConnectorFn } from '@wagmi/core'
import { toast } from "svelte-sonner";

import { mainnet, polygon, optimism, arbitrum, base, zkSync, avalanche, bsc } from 'viem/chains'; // or wherever your chain imports come from
import { claim, contribute, endEpoch, loadContracts, topUpOlas } from "$lib/contracts/interface";

import { WC, disconnectWagmi, defaultConfig, chainId, signerAddress, connected, wagmiConfig } from 'svelte-wagmi';

let PUBLIC_WALLETCONNECT_ID = "189298bf7ea32b9f16f1369599ad0ad4"

let config: { appName: string; walletConnectProjectId: string; connectors: CreateConnectorFn<Provider, { connect(parameters?: { chainId?: number | undefined; isReconnecting?: boolean | undefined; pairingTopic?: string | undefined; }): Promise<{ accounts: readonly Address[]; chainId: number; }>; getNamespaceChainsIds(): number[]; getRequestedChainsIds(): Promise<number[]>; isChainsStale(): Promise<boolean>; onConnect(connectInfo: ProviderConnectInfo): void; onDisplayUri(uri: string): void; onSessionDelete(data: { topic: string; }): void; setRequestedChainsIds(chains: number[]): void; requestedChainsStorageKey: `${string}.requestedChains`; }, { [x: `${string}.requestedChains`]: number[]; }>[] | CreateConnectorFn[]; appIcon?: string | null | undefined; appDescription?: string | null | undefined; appUrl?: string | null | undefined; autoConnect?: boolean | undefined; alchemyId?: string | null | undefined; chains?: Chain[] | null | undefined; }

let epochRewards = 0
let incentiveBalance = 0
let data = {}
let intervalId: number;


let percentCompleted = 0;
let canPlayGame = false;
let epochNumber = 0;
let isRunningInTauri = false;
let totalDonated = 0;
let epochLength = 100; // e.g., 100 blocks
let blocksRemaining = epochLength;
let account: Address | undefined;
let animatedPercent = 0;
let userCurrentShare = 0;
let userClaimable = 0;

let userContribution = 0;
let userCurrentDonation = 0;
let currentTab = 'contribute'; // or 'info'

let minimalDonation = 0.00001; // e.g., 0.1 ETH

const SUPPORTED_CHAIN_ID = base.id;



let chains = [
  base,
];

let pendingChainId: number | null = null;

async function handleSwitch(chainId: number) {
    pendingChainId = chainId;
    try {
      await switchNetwork({ chainId });
    } finally {
      pendingChainId = null;
    }
  }


async function connect() {
        console.log('Connecting to Ethereum...');
		try {
            console.log('Connecting to WalletConnect...');
			let res = await WC();
            console.log('WalletConnect connected' + res);

		} catch (e) {
			console.error('WalletConnect failed', e);
		}
}

async function isTauri(): Promise<boolean> {
  try {
    await getVersion();
    isRunningInTauri = true;
  } catch {
    isRunningInTauri = false;
  }
  return isRunningInTauri;
}

  let wagmi: any;
	onMount(async () => {
    let isRunningInTauri = await isTauri();
    console.log('Running in Tauri:', isRunningInTauri);
    if (isRunningInTauri) {
      console.log('Running in Tauri, not initializing WalletConnect');
      return;
    } 

    console.log('Initializing WalletConnect...');

    const chains = [mainnet, polygon, optimism, arbitrum, base, zkSync, avalanche, bsc]; // Add any others you want
    config = {
      appName: 'erc.kit',
      walletConnectProjectId: PUBLIC_WALLETCONNECT_ID,
      chains: chains,
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
    };
    wagmi = defaultConfig(config);
    console.log('Wagmi config:', wagmi);


    console.log('WalletConnect initialized');
    await wagmi.init();
    console.log('Contracts loaded');
    account = await getAccount($wagmiConfig)
    console.log('Account:', account);
    refreshData();
    intervalId = setInterval(() => {
      refreshData();
      console.log('Data refreshed:', data);
    }, 2000);
   
  });

    async function refreshData() {

    const data = await loadContracts(account.address);

    console.log('Data loaded:', data);
    blocksRemaining = Number(data.blocksRemaining);
    totalDonated = Number(data.totalDonated);
    epochNumber = Number(data.currentEpoch);
    epochLength = Number(data.epochLength);
    minimalDonation = Number(data.minimalDonation);
    epochRewards = Number(data.epochRewards);
    userCurrentShare = Number(data.userCurrentShare);
    userClaimable = Number(data.userClaimable);
    userCurrentDonation = Number(data.userCurrentDonation);
    canPlayGame = data.canPlayGame;
    incentiveBalance = Number(data.incentiveBalance);
    percentCompleted = Math.floor((epochLength - blocksRemaining) / epochLength * 100);

    animatedPercent = Math.floor((epochLength - blocksRemaining) / epochLength * 100);
  }

  onDestroy(() => {
    clearInterval(intervalId);
  });



</script>

{#if !isRunningInTauri}
<header class="w-full bg-black text-green-400 font-mono text-sm px-4 py-3 flex justify-between items-center flex-wrap">

  <!-- Left side (empty) -->
  <div class="w-1/3 flex justify-start">
    <!-- Optional: Add logo or leave blank -->
  </div>

  <!-- Center navigation -->
  <div class="w-1/3 flex justify-center gap-4">
    <Button.Root on:click={() => currentTab = 'contribute'} variant={currentTab === 'contribute' ? 'default' : 'outline'}>
      Contribute
    </Button.Root>
    <Button.Root on:click={() => currentTab = 'info'} variant={currentTab === 'info' ? 'default' : 'outline'}>
      How It Works
    </Button.Root>
  </div>

  <!-- Right side wallet controls -->
  <div class="w-1/3 flex justify-end items-center gap-4 flex-wrap">

    {#if $chainId != SUPPORTED_CHAIN_ID && $connected}
      <Alert.Root variant="destructive" class="mb-3">
        <Alert.Title class="text-red-500">Unsupported Network</Alert.Title>
        <Alert.Description class="text-red-400">
          Please switch to the Base network.
          {#each chains as chain}
            <Button.Root
              on:click={() => handleSwitch(chain.id)}
              disabled={pendingChainId === chain.id}
            >
              {pendingChainId === chain.id ? 'Switching...' : `Switch to ${chain.name}`}
            </Button.Root>
          {/each}
        </Alert.Description>
      </Alert.Root>
    {/if}

    {#if $signerAddress}
      <div class="flex flex-col text-right leading-tight">
        <span class="text-green-500 text-xs">Chain: {$chainId}</span>
        <span class="text-green-300 truncate max-w-[120px] text-xs">{$signerAddress}</span>
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
<Card.Root class="space-y-8 p-6 shadow-lg border border-green-500 bg-black text-green-400 font-mono">
  <!-- Header -->
  <Card.Header class="text-center space-y-4">
    <Card.Title class="text-2xl font-bold tracking-tight">
      Epochal Reward Split (ERS)
    </Card.Title>

    <Card.Description class="text-green-500 text-sm">
      Contribute ETH → Claim OLAS. Rewards distributed at epoch end.
    </Card.Description>

    <!-- Important Metrics Row -->
    <div class="flex flex-col sm:flex-row justify-center gap-8 text-green-400 text-sm items-center">
      <div class="flex items-center gap-2">
        <Timer class="w-4 h-4" />
        <span>Epoch {epochNumber}</span>
      </div>

      <div class="flex items-center gap-2">
        <CircleDollarSign class="w-4 h-4" />
        <span>{(incentiveBalance / 1e18).toFixed(2)} OLAS Available</span>
      </div>

      <div class="flex items-center gap-2">
        <Flame class="w-4 h-4" />
        <span>{(incentiveBalance / epochRewards).toFixed(0)} Epochs Remaining</span>
      </div>
    </div>

    <!-- Progress -->
    <div class="space-y-1 pt-4">
      <Progress.Root value={animatedPercent} class="h-2 rounded bg-green-900 transition-all" />
      <div ></div>
      <div class="text-xs text-center text-green-600">{percentCompleted}% complete</div>
    </div>

  </Card.Header>


{#if currentTab === 'contribute'}
  <div transition:fade>

  <!-- <div class="space-y-1">
    <Progress.Root value={animatedPercent} class="h-2 rounded bg-green-900 transition-all" />
    <div class="text-xs text-right text-green-600">{percentCompleted}% complete</div>
  </div> -->

  <div class="grid md:grid-cols-2 gap-6">

  <!-- Contribution Overview -->
  <Card.Root class="p-4 border border-green-500 bg-black text-green-400 shadow-md">
    <Card.Header class="pb-2">
      <Card.Title class="text-base font-bold">Contribution Overview</Card.Title>
    </Card.Header>
    <Card.Content class="grid grid-cols-2 gap-y-1 text-sm">
      <div class="text-green-500">Your Contribution</div>
      <div class="text-green-300 text-right">{(userCurrentDonation / 1e18).toFixed(6)} ETH</div>

      <div class="text-green-500">Your Share</div>
      <div class="text-green-300 text-right">{(userCurrentShare / 1e16).toFixed(2)} %</div>

      <div class="text-green-500">Total Donations</div>
      <div class="text-green-300 text-right">{(totalDonated / 1e18).toFixed(6)} ETH</div>

      <div class="text-green-500">Minimum Donation</div>
      <div class="text-green-300 text-right">{(minimalDonation / 1e18).toFixed(6)} ETH</div>
    </Card.Content>
  </Card.Root>

  <!-- Epoch Controls -->
  <Card.Root class="p-4 border border-green-500 bg-black text-green-400 shadow-md">
    <Card.Header class="pb-2">
      <Card.Title class="text-base font-bold">Epoch Controls</Card.Title>
    </Card.Header>

    <Card.Content class="flex flex-col gap-4">
      {#if userClaimable > 0}
        <Button.Root
          class="w-full bg-green-600 hover:bg-green-500 text-black font-bold py-3 rounded-lg"
          on:click={claim}
          disabled={!$connected}
        >
          Claim {(userClaimable / 1e18).toFixed(2)} OLAS
        </Button.Root>
      {/if}

      {#if blocksRemaining == 0}
        <Button.Root
          class="w-full bg-red-600 hover:bg-red-500 text-black font-bold py-3 rounded-lg"
          on:click={endEpoch}
          disabled={!$connected}
        >
          End Epoch
        </Button.Root>
      {/if}

      {#if $connected && blocksRemaining > 0}
        <div class="flex flex-col gap-2 mt-4">
          <Input.Root
            placeholder="Enter at least {(minimalDonation / 1e18).toFixed(6)} ETH"
            bind:value={userContribution}
            type="number"
            min={(minimalDonation / 1e18)}
            step="0.00001"
            max="0.01"
            class="text-center"
          />

          {#if userContribution < minimalDonation / 1e18}
            <Alert.Root variant="destructive">
              <Alert.Description class="text-sm">
                Minimum {(minimalDonation / 1e18).toFixed(6)} ETH required
              </Alert.Description>
            </Alert.Root>
          {/if}

          <Button.Root
            class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-lg"
            on:click={() => contribute(userContribution * 1e18)}
            disabled={userContribution < minimalDonation / 1e18 || blocksRemaining == 0 || userCurrentDonation > 0}
          >
            Contribute {userContribution} ETH
          </Button.Root>
        </div>
      {/if}
    </Card.Content>
  </Card.Root>

</div>

  </div>

<!-- Epoch Metrics -->
<div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
  <!-- Total Donations -->
  <Card.Root class="border border-green-700 bg-green-950 px-4 py-3 rounded-lg space-y-2">
    <Card.Header class="flex items-center gap-2">
      <HandCoins class="w-6 h-6 text-green-400" />
      <Card.Title class="text-base font-semibold">Donations</Card.Title>
    </Card.Header>
    <Card.Content class="text-center text-2xl font-bold">{totalDonated / 1e18}</Card.Content>
  </Card.Root>

  <!-- Blocks Remaining -->
  <Card.Root class="border border-green-700 bg-green-950 px-4 py-3 rounded-lg space-y-2">
    <Card.Header class="flex items-center gap-2">
      <Clock class="w-6 h-6 text-green-400" />
      <Card.Title class="text-base font-semibold">Blocks Remaining</Card.Title>
    </Card.Header>
    <Card.Content class="text-center text-2xl font-bold">{blocksRemaining}</Card.Content>
  </Card.Root>

  <!-- Contributors -->
  <Card.Root class="border border-green-700 bg-green-950 px-4 py-3 rounded-lg space-y-2">
    <Card.Header class="flex items-center gap-2">
      <Users class="w-6 h-6 text-green-400" />
      <Card.Title class="text-base font-semibold">Current Share</Card.Title>
    </Card.Header>
    <Card.Content class="text-center text-2xl font-bold">{userCurrentShare / 1e18 * 100} %</Card.Content>
  </Card.Root>
</div>
{:else}

  <div transition:fade>





  <!-- Epoch Breakdown with callouts -->
  <div class="space-y-6 text-green-300 max-w-2xl mx-auto">
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">

    <!-- Reward Distribution Card -->
    <div class="bg-green-950 border border-green-700 p-4 rounded-lg flex flex-col gap-2">
      <div>
        <Alert.Root variant="default" class="mb-3">
          <Alert.Title >Proportional Split</Alert.Title>
          <Separator class="my-2" />
          <Alert.Description class="text-green-400">
            8 contributors each round.
          </Alert.Description>
        </Alert.Root>
      </div>
    </div>
    
    <!-- Epoch Progress Card -->
    <div class="bg-green-950 border border-green-700 p-4 rounded-lg flex flex-col gap-2">
      <div>
        <Alert.Root variant={
          epochRewards > 0 ? "default" : "destructive"
        } class="mb-3">
          {#if epochRewards > 0}
            <Alert.Title>Epoch Rewards</Alert.Title>
            <Separator class="my-2" />
            <Alert.Description class="text-green-400">
              {epochRewards / 1e18} OLAS each epoch.
            </Alert.Description>
          {:else}
            <Alert.Title class="text-red-500">No rewards available</Alert.Title>
          {/if}
        </Alert.Root>
      </div>
    </div>
  </div>
</div>

<!-- Final Epoch Summary -->
<div class="space-y-6 text-green-300 max-w-2xl mx-auto">
  <!-- Epoch Breakdown with callouts -->
  <div class="space-y-6 text-green-300 max-w-2xl mx-auto">
    <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
      <!-- Epoch Progress Card -->
      <div class="bg-green-950 border border-green-700 p-4 rounded-lg flex flex-col gap-2">
        <div>
          <Alert.Root variant="default" class="mb-3">
            <Alert.Title>Epoch Progress</Alert.Title>
            <Separator class="my-2" />
            <Alert.Description class="text-green-400">
              {blocksRemaining}/{epochLength} blocks
            </Alert.Description>
          </Alert.Root>
        </div>
      </div>
      <!-- Reward Distribution Card -->
      <div class="bg-green-950 border border-green-700 p-4 rounded-lg flex flex-col gap-2">
        <div>
          <Alert.Root variant="default" class="mb-3">
            <Alert.Title>Minimum Donation</Alert.Title>
            <Separator class="my-2" />
            <Alert.Description class="text-green-400">
              {minimalDonation / 1e18} ETH
            </Alert.Description>
          </Alert.Root>
        </div>
      </div>
    </div>
  <!-- Epoch Summary -->
    <div class="space-y-6 text-green-300 max-w-2xl mx-auto">
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
           <!-- Prisoner's Dilemma -->
           <li class="flex items-start gap-4">

             <Alert.Root variant="destructive" class="mb-3">
               <Alert.Title class="text-red-500">Rewards Are Only Claimable for 1 Epoch!</Alert.Title>
               <Separator class="my-2" />
               <Alert.Description class="text-red-400">
                 <p>
                   If you do not claim your rewards within the current epoch, they will be donated to the pool and you will not receive them.
                 </p>
               </Alert.Description>
             </Alert.Root>
           </li>
         </ul>
       </Card.Content>
     </Card.Root>

    </div>
  </div>
</div>
 
  </div>

{/if}

</Card.Root>
