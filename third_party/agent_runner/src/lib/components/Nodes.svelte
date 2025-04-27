<script lang="ts">

  import type Provider from "@walletconnect/ethereum-provider";
  import type { Address, ProviderConnectInfo, Chain } from "viem";
  import { MessageCircleWarningIcon,  HandCoins, Clock, Users, Gift, DollarSign, CircleDollarSign, Info, Timer, BrainCircuit, TimerReset, Sparkles, Flame, SeparatorVertical } from "lucide-svelte";
  import * as Button from "./ui/button";
  import * as Badge from "./ui/badge";
  import * as Tooltip from "./ui/tooltip";
  import * as Input from "./ui/input";
  import * as Progress from "./ui/progress";
  import * as Alert from "./ui/alert";
  import * as Accordion from "./ui/accordion";
  import { ChevronDown, } from "lucide-svelte";
	import { WC, disconnectWagmi} from 'svelte-wagmi';
  import { defaultConfig } from 'svelte-wagmi';
  import * as Card from "$lib/components/ui/card";
	import { chainId } from 'svelte-wagmi';
	import { signerAddress } from 'svelte-wagmi';
    import { get } from "svelte/store";
import { getVersion } from '@tauri-apps/api/app';
    import { onDestroy, onMount } from 'svelte';
import { walletConnect } from '@wagmi/connectors';
import Separator from './ui/separator/separator.svelte';
import { getAccount, readContract, type CreateConnectorFn } from '@wagmi/core'
import { toast } from "svelte-sonner";
import { connected } from 'svelte-wagmi';

import { mainnet, polygon, optimism, arbitrum, base, zkSync, avalanche, bsc } from 'viem/chains'; // or wherever your chain imports come from
import { wagmiConfig } from 'svelte-wagmi';
import { claim, contribute, endEpoch, loadContracts, topUpOlas } from "$lib/contracts/interface";


let PUBLIC_WALLETCONNECT_ID = "189298bf7ea32b9f16f1369599ad0ad4"

let config: { appName: string; walletConnectProjectId: string; connectors: CreateConnectorFn<Provider, { connect(parameters?: { chainId?: number | undefined; isReconnecting?: boolean | undefined; pairingTopic?: string | undefined; }): Promise<{ accounts: readonly Address[]; chainId: number; }>; getNamespaceChainsIds(): number[]; getRequestedChainsIds(): Promise<number[]>; isChainsStale(): Promise<boolean>; onConnect(connectInfo: ProviderConnectInfo): void; onDisplayUri(uri: string): void; onSessionDelete(data: { topic: string; }): void; setRequestedChainsIds(chains: number[]): void; requestedChainsStorageKey: `${string}.requestedChains`; }, { [x: `${string}.requestedChains`]: number[]; }>[] | CreateConnectorFn[]; appIcon?: string | null | undefined; appDescription?: string | null | undefined; appUrl?: string | null | undefined; autoConnect?: boolean | undefined; alchemyId?: string | null | undefined; chains?: Chain[] | null | undefined; }

let epochProgress = 60; // e.g., 60% through
let epochRewards = 0
let incentiveBalance = 0
let data = {}
let intervalId: number;


let percentCompleted = 0;
let canPlayGame = false;
let epochNumber = 0;
let isRunningInTauri = false;
let totalDonated = 0;
let contributors = 0
let totalRewards = 0
let epochLength = 100; // e.g., 100 blocks
let blocksRemaining = epochLength;
let account: Address | undefined;
let animatedPercent = 0;
let userCurrentShare = 0;
let userClaimable = 0;

let userContribution = 0;
let userCurrentDonation = 0;

let minimalDonation = 0.00001; // e.g., 0.1 ETH
$: minimalDonation

$: userContribution

$: blocksRemaining
$: contributors
$: totalRewards
$: epochLength
$: percentCompleted
$: epochRewards
$: canPlayGame
$: incentiveBalance
$: totalRewards
$: chainId
$: signerAddress
$: isRunningInTauri;
$: account
$: totalDonated
$: userClaimable
$: userCurrentShare
$: userCurrentDonation



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
    }, 1000);
   
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
<header class="w-full bg-black text-green-400 font-mono text-sm px-4 py-3 flex justify-between items-center">
  <div class="font-bold tracking-wide text-green-300">
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
    <Card.Description class="text-green-500 text-sm">
      Contribute ETH → Claim OLAS. Rewards distributed at epoch end.
    </Card.Description>
    <Card.Description class="text-green-500 text-sm">
      Current epoch: {epochNumber}  Current Reward Balance: {incentiveBalance / 1e18} OLAS Remaining Epochs {incentiveBalance / epochRewards}
    </Card.Description>
      <Separator class="my-2" />
  </Card.Header>


  <!-- Progress Bar -->
  <div class="space-y-1">
    <Progress.Root value={animatedPercent} class="h-2 rounded bg-green-900 transition-all" />
    <div class="text-xs text-right text-green-600">{percentCompleted}% complete</div>
  </div>





<!-- Epochal Action Panel (Simplified) -->
<div class="mt-8 px-4 py-6 border border-green-700 bg-black/30 w-full max-w-4xl mx-auto">
  <h3 class="text-center text-green-300 text-base font-medium mb-3">
    Epoch Actions
  </h3>

  <!-- Connection Status -->
  <!-- Connection Status -->
{#if $connected}
  {#if canPlayGame && blocksRemaining > 0}
    <Input.Root class="mb-3" disabled={blocksRemaining == 0 || userCurrentShare > 0
    } placeholder="Enter your contribution in ETH" bind:value={userContribution}>
    </Input.Root>

    <!-- We now calculate the user share of the donation based on the donation -->

    <div class="text-center text-green-500 text-sm mb-3">
      {#if userContribution < minimalDonation / 1e18}
        <span class="text-red-500">Minimum donation is {minimalDonation / 1e18} ETH</span>
      {/if}

      <Separator class="my-2" />

      {#if !totalDonated}
        <span class="text-green-500">No donations made yet</span>
      {:else}
        <span class="text-green-500">Total donations: {totalDonated / 1e18} ETH</span>
      {/if}

      <Separator class="my-2" />

      {#if userCurrentShare > 0}
        <span class="text-green-500">Your contribution: {userCurrentDonation / 1e18} ETH</span>
      <Separator class="my-2" />
        <span class="text-green-500">Your share of the pool: {userCurrentShare / 1e18 * 100} %</span>
      {/if}

      {#if userContribution > 0}
        <span class="text-green-500">Projected contribution: {userContribution} ETH</span>
      <Separator class="my-2" />

        {#if totalDonated > 0}
          <span class="text-green-500">Total donations: {totalDonated / 1e18} ETH</span>
          <Separator class="my-2" />
          <span class="text-green-500">Your Projected share of the pool: {userCurrentDonation / totalDonated * 100} %</span>
        {:else}
          <span class="text-green-500">No donations made yet</span>
          <Separator class="my-2" />
          <span class="text-green-500">Your Projected share of the pool: {100} %</span>
          <Separator class="my-2" />
          <span class="text-green-500">Your implied price per OLAS: {userContribution * 1e18 / epochRewards } ETH</span>
        {/if}
      {/if}

    </div>

  {:else}
    <Alert.Root variant="destructive" class="mb-3">
      {#if blocksRemaining === 0}
        <Alert.Title class="text-red-500">Epoch in progress</Alert.Title>
        <Alert.Description class="text-red-400">
          You cannot play the game until the epoch is completed. Please end the epoch.
        </Alert.Description>
      {:else}
        <Alert.Title class="text-red-500">
          The game is not available until the contract has been funded.
        </Alert.Title>
      {/if}
    </Alert.Root>
  {/if}
{:else}
  <p class="text-center text-red-500 text-sm mb-3">Not connected</p>
{/if}

  <!-- Buttons -->
  <div class="grid grid-cols-2 gap-3 mb-3">
    <Button.Root variant="outline"
      disabled={!$connected || !canPlayGame || blocksRemaining == 0 || userContribution < minimalDonation / 1e18}
      on:click={() => contribute(userContribution * 1e18)}
    >
      <Flame class="w-4 h-4 mr-1" /> Contribute ETH
    </Button.Root>

    <Button.Root variant="outline"
      disabled={!$connected}
      on:click={() => topUpOlas(epochRewards)}
    >
      <Flame class="w-4 h-4 mr-1" /> Top Up OLAS for Game
    </Button.Root>
  </div>

  <div class="grid grid-cols-2 gap-3">
    <Button.Root variant="default"
      disabled={!$connected || userClaimable == 0}
      on:click={claim}
    >
      <Sparkles class="w-4 h-4 mr-1" /> Claim {userClaimable / 1e18} OLAS
    </Button.Root>

    <Button.Root variant="destructive"
      disabled={!$connected || blocksRemaining > 0}
      on:click={endEpoch}
    >
      <TimerReset class="w-4 h-4 mr-1" /> End Epoch
    </Button.Root>
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
        <!-- {#if blocksRemaining > 0}
          <span class="inline-block text-xs bg-green-800 border border-green-600 text-green-300 rounded px-2 py-1">
            {blocksRemaining} blocks remaining
          </span>
        {:else}
          <span class="inline-block text-xs bg-green-800 border border-green-600 text-green-300 rounded px-2 py-1">
            Epoch completed
          </span>
        {/if} -->
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
 




</Card.Root>