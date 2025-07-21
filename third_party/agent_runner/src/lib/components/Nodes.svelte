

<script lang="ts">
  import { onMount } from 'svelte'; 

  // Extend the Window interface to include the ethereum property
  import { fade } from 'svelte/transition';
  import { type Address, type Chain, createWalletClient, custom, type Client } from "viem";
  import { HandCoins, Clock, Users, Gift, DollarSign, CircleDollarSign, Timer, BrainCircuit, Flame, } from "lucide-svelte";
  import * as Button from "./ui/button";
  import * as Input from "./ui/input";
  import * as Progress from "./ui/progress";
  import * as Alert from "./ui/alert";
  import * as Card from "$lib/components/ui/card";
  import { getVersion } from '@tauri-apps/api/app';
  import Separator from './ui/separator/separator.svelte';
  import { base} from 'viem/chains'; // or wherever your chain imports come from
  import { claim, contribute, endRound, loadContracts, topUpOlas } from "$lib/contracts/interface";
  import { addChain } from 'viem/actions';
  import Metrics from './Metrics.svelte';
  import BalMetrics from './ExchangeMetrics.svelte';
    

let PUBLIC_WALLETCONNECT_ID = "189298bf7ea32b9f16f1369599ad0ad4"



let roundRewards = 0
let incentiveBalance = 0
let data = {}
let intervalId: number;
let olasTopUp = 0;


let percentCompleted = 0;
let roundNumber = 0;
let isRunningInTauri = false;
let totalDonated = 0;
let roundLength = 90; // e.g., 100 blocks
let blocksRemaining = roundLength;
let account: Address = "0x0000000000000000000000000000000000000000";
let animatedPercent = 0;
let userCurrentShare = 0;
let canPlayGame = false;
let userClaimable = 0;

let userContribution = 0;
let userCurrentDonation = 0;
let currentTab = 'contribute'; // or 'info'

let minimumDonation = 0.00001; // e.g., 0.1 ETH

const SUPPORTED_CHAIN_ID = base.id;


let chainId = 0;
let connected = false;
$: chainId = base.id;
$: connected = false;

// 0. Define ui elements

// 1. Define constants
const projectId = PUBLIC_WALLETCONNECT_ID
if (!projectId) {
  throw new Error("You need to provide VITE_PROJECT_ID env variable");
}



let WalletConnectProvider: any;




let walletClient: any = null;

// return type is the wallet client

async function setUpInjectedWallet(): Promise<any> {
  // Check if browser wallet is available
  if (!(window as any).ethereum) {
    throw new Error('No injected wallet found. Please install MetaMask or another wallet extension.');
  }
  
  // Request accounts access
  const accounts = await (window as any).ethereum.request({ method: 'eth_requestAccounts' });
  
  if (!accounts || accounts.length === 0) {
    throw new Error('No accounts found or user rejected the connection');
  }
  
  console.log("Accounts found:", accounts);
  walletClient = createWalletClient({
    chain: base,
    transport: custom((window as any).ethereum),
  });
  
  return walletClient;
}

async function setUpWc(): Promise<Client>{
// let result = await setUpWalletConnectBrowser();
let result = await setUpInjectedWallet();
walletClient = result;
return result;
}

async function setUp(): Promise<any> {
  if (!WalletConnectProvider) {
    WalletConnectProvider = (await import('@walletconnect/ethereum-provider')).EthereumProvider;
  }

  const wcProvider = await WalletConnectProvider.init({
    projectId: PUBLIC_WALLETCONNECT_ID,
    chains: [base.id],
    showQrModal: false, // Disable QR code modal for browser extension
    methods: ['eth_sendTransaction', 'eth_signTransaction', 'eth_sign', 'personal_sign', 'eth_signTypedData'],
    optionalMethods: ['eth_accounts', 'eth_requestAccounts', 'eth_chainId'],
    events: ['chainChanged', 'accountsChanged'],
    metadata: {
      name: 'Derolas',
      description: 'Contribution based game',
      url: window.location.origin,
      icons: ['https://derolas.station.codes/derolasDark.png']
    }
  });

  console.log("WalletConnectProvider HERE:", wcProvider);
  // Add timeout to prevent hanging promises
  const connectPromise = new Promise(async (resolve, reject) => {
    // Set a timeout to reject if connection takes too long
    const timeoutId = setTimeout(() => {
      reject(new Error("WalletConnect browser connection timed out"));
    }, 30000); // 30 second timeout
    
    try {
      // Listen for connection events
      wcProvider.on("display_uri", () => {
        console.log("WalletConnect ready to connect");
      });
      
      wcProvider.on("connect", () => {
        clearTimeout(timeoutId);
        resolve(true);
      });
      
      wcProvider.on("disconnect", (code: number, reason: string) => {
        console.log(`WalletConnect disconnected: ${code} - ${reason}`);
        reject(new Error(`WalletConnect disconnected: ${reason}`));
      });
      
      // Initiate connection
      await wcProvider.connect();
      clearTimeout(timeoutId);
      resolve(true);
    } catch (error) {
      clearTimeout(timeoutId);
      reject(error);
    }
  });
  
  // Wait for connection to complete
  await connectPromise;

  // Create wallet client once connected
  walletClient = createWalletClient({
    chain: base,
    transport: custom(wcProvider),
  });
  
  return walletClient;
}


function disconnectWallet() {
  console.log('Disconnecting from WalletConnect...');
  walletClient = null
  account = "0x0000000000000000000000000000000000000000";
  connected = false;
  chainId = 0;
}

let pendingChainId: number | null = null;
let connectChainName = "";

let poolId = "0x7b4c560f33a71a9f7a500af3c4c65b46fbbafdb7";
/**
 * Switch the connected wallet to a different chain
 * @param newChain - The chain to switch to
 */
async function handleSwitch(newChain: Chain) {
  pendingChainId = newChain.id;
  
  try {
    console.log('Switching to chain:', newChain);
    
    // Make sure we have a wallet client
    if (!walletClient) {
      walletClient = await setUpWc(); // Or whichever method you're using to connect
    }
    
    // Using viem's wallet client approach to switch chains
    // Method 1: For MetaMask and most injected wallets
    if (walletClient.transport.type === 'custom' && (window as any).ethereum) {
      await (window as any).ethereum.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: `0x${newChain.id.toString(16)}` }],
      });
    } 
    // Method 2: For WalletConnect
    else if (walletClient.provider && typeof walletClient.provider.request === 'function') {
      await walletClient.provider.request({
        method: 'wallet_switchEthereumChain',
        params: [{ chainId: `0x${newChain.id.toString(16)}` }],
      });
    }
    // Method 3: Using viem's switchChain method if available in your version
    else if (typeof walletClient.switchChain === 'function') {
      await walletClient.switchChain({ id: newChain.id });
    }
    // Fallback method
    else {
      throw new Error('No available method to switch chains with this wallet');
    }
    
    // Update chainId state
    chainId = newChain.id;
    console.log('Successfully switched to chain ID:', chainId);
  } catch (error) {
    console.error('Failed to switch chain:', error);
    
    // Handle case where chain needs to be added first
    if ((error as { code: number }).code === 4902) { // Chain not added to wallet

      let addChainParams = {
        chain: newChain, // Add the chain property
        id: newChain.id,
        name: newChain.name,
        nativeCurrency: newChain.nativeCurrency,
        rpcUrls: newChain.rpcUrls,
        blockExplorers: newChain.blockExplorers,
      };
      await addChain(walletClient, addChainParams);
    } else {
      throw error;
    }
  } finally {
    pendingChainId = null;
  }
}

async function connect() {
        console.log('Connecting to Ethereum...');
		try {
        console.log('Connecting to WalletConnect...');
        let w = await setUpWc();
        chainId = walletClient.chain.id;

        console.log('WalletConnect initialized:', w);
        const accounts = await w.request({ method: 'eth_accounts' });
        account = accounts[0];
        connected = true;
        // w.switchChain({ id: base.id });
        if (!account) {
          console.error("No account found. Please connect your wallet.");
          account = "0x0000000000000000000000000000000000000";
        }
        console.log('WalletConnect switched to Base:', w);
        console.log('Account:', accounts[0]);
        console.log('Chain ID:', chainId);
        console.log('Connected:', connected);
        refreshData();

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

    intervalId = setInterval(() => {
      refreshData();
      // console.log('Data refreshed:', data);
    }, 2000);
   
  });

    async function refreshData() {

    if (!account) {
      console.error("Account is undefined. Cannot load contracts.");
      return;
    }
    const data = await loadContracts(account);

    // console.log('Data loaded:', data);
    blocksRemaining = Number(data.blocksRemaining);
    totalDonated = Number(data.totalDonated);
    roundNumber = Number(data.currentRound);
    roundLength = Number(data.roundLength);
    minimumDonation = Number(data.minimumDonation) / 1e18;
    roundRewards = Number(data.roundRewards);
    userCurrentShare = Number(data.userCurrentShare);
    userClaimable = Number(data.userClaimable);
    userCurrentDonation = Number(data.userCurrentDonation);
    canPlayGame = data.canPlayGame;
    incentiveBalance = Number(data.incentiveBalance);
    percentCompleted = Math.floor((roundLength - blocksRemaining) / roundLength * 100);
    animatedPercent = Math.floor((roundLength - blocksRemaining) / roundLength * 100);
  }

  // onDestroy(() => {
  //   clearInterval(intervalId);
  // });


</script>

{#if !isRunningInTauri}
<header class="w-full bg-black border-b border-green-700 shadow-lg px-6 py-4 grid grid-cols-1 sm:grid-cols-3 items-center text-center sm:text-left gap-4 sm:gap-0">

  <!-- Center: Logo -->
  <div class="text-green-400 text-xl font-mono font-bold tracking-wider justify-self-center">
      <img src="/derolas.png" alt="Derolas Logo" class="h-20 w-auto" />
  </div>
  <!-- Left: Nav -->
  <div class="flex justify-center sm:justify-start gap-4">
    <Button.Root
      variant="outline"
      onclick={() => currentTab = 'contribute'}
      class={`${currentTab === 'contribute' ? 'bg-green-500 text-black' : 'bg-black text-green-400 border-green-500'} 
      transition-all duration-200 hover:bg-green-600 hover:text-black px-6 py-2 font-mono`}
    >
      Play 
    </Button.Root>
    <Button.Root
      variant="outline"
      onclick={() => currentTab = 'info'}
      class={`${currentTab === 'info' ? 'bg-green-500 text-black' : 'bg-black text-green-400 border-green-500'} 
      transition-all duration-200 hover:bg-green-600 hover:text-black px-6 py-2 font-mono`}
    >
      Info
    </Button.Root>
    <Button.Root
      variant="outline"
      onclick={() => currentTab = 'metrics'}
      class={`${currentTab === 'metrics' ? 'bg-green-500 text-black' : 'bg-black text-green-400 border-green-500'} 
      transition-all duration-200 hover:bg-green-600 hover:text-black px-6 py-2 font-mono`}
    >
      Metrics
    </Button.Root>

  </div>

  <!-- Right: Wallet -->
  <div class="flex justify-center sm:justify-end items-center gap-3">
    {#if account && connected && chainId == SUPPORTED_CHAIN_ID}
      <div class="flex flex-col text-right">
      </div>
      <Button.Root
        variant="destructive"
        class="bg-red-600 hover:bg-red-500 text-white font-mono font-bold px-4 py-2 text-sm transition-colors"
        onclick={disconnectWallet}
      >
        Disconnect
      </Button.Root>
    {:else if account && connected && chainId != SUPPORTED_CHAIN_ID}
      <div class="bg-red-950 border border-red-600 p-3 text-sm font-mono text-red-300 space-y-2 max-w-xs">
        <div class="font-bold text-red-400">Wrong Network</div>
        <p>Please switch to Base to use this app.</p>
        <Button.Root
          onclick={() => handleSwitch(base)}
          disabled={pendingChainId === base.id}
          class="bg-red-600 hover:bg-red-500 text-white px-3 py-1 text-xs font-mono"
        >
          {pendingChainId === base.id ? 'Switching...' : 'Switch to Base'}
        </Button.Root>
      </div>
    {:else}
      <Button.Root
        variant="default"
        class="bg-green-500 hover:bg-green-400 text-black font-mono font-bold px-5 py-2 transition-colors"
        onclick={connect}
      >
        Connect Wallet
      </Button.Root>
    {/if}
  </div>
</header>

{/if}

 <Card.Root class="mb-10 p-6 shadow-lg border border-green-500 bg-black text-green-400 font-mono space-y-8">

  <!-- Header -->
{#if currentTab === 'contribute'}
  <Card.Header class="text-center space-y-4">
    <Card.Title class="text-2xl font-bold tracking-tight">
      Roundal Reward Split (ERS)
    </Card.Title>

    <Card.Description class="text-green-500 text-sm">
      Contribute ETH → Claim OLAS. Rewards distributed at round end.
    </Card.Description>

    <!-- Important Metrics Row -->
    <div class="flex flex-col sm:flex-row justify-center gap-8 text-green-400 text-sm items-center">
      <div class="flex items-center gap-2">
        <Timer class="w-4 h-4" />
        <span>Round {roundNumber}</span>
      </div>

      <div class="flex items-center gap-2">
        <CircleDollarSign class="w-4 h-4" />
        <span>{(incentiveBalance / 1e18).toFixed(2)} OLAS Available</span>
      </div>

      <div class="flex items-center gap-2">
        <Flame class="w-4 h-4" />
        <span>{(blocksRemaining).toFixed(0)} Blocks Remaining</span>
      </div>
    </div>

    <!-- Progress -->
    <div class="space-y-1 pt-4">
      <Progress.Root value={animatedPercent} class="h-2 bg-green-900 transition-all" />
      <div ></div>
      <div class="text-xs text-center text-green-600">{percentCompleted}% complete</div>
    </div>

  </Card.Header>


  <div transition:fade>

  <!-- <div class="space-y-1">
    <Progress.Root value={animatedPercent} class="h-2 bg-green-900 transition-all" />
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
      <div class="text-green-300 text-right">{(minimumDonation ).toFixed(6)} ETH</div>
    </Card.Content>
  </Card.Root>

  <!-- Round Controls -->
  <Card.Root class="p-4 border border-green-500 bg-black text-green-400 shadow-md">
    <Card.Header class="pb-2">
      <Card.Title class="text-base font-bold">Round Controls</Card.Title>
    </Card.Header>

    {#if connected}
    <Card.Content class="flex flex-col gap-4">
      {#if userClaimable > 0 && blocksRemaining > 0 && connected}
        <Button.Root
          class="w-full bg-green-600 hover:bg-green-500 text-black font-bold py-3 rounded-lg"
          onclick={() => claim(walletClient)}
          disabled={!connected}
        >
          Claim {(userClaimable / 1e18).toFixed(2)} OLAS
        </Button.Root>
      {/if}

      {#if blocksRemaining == 0}
        <Button.Root
          class="w-full bg-red-600 hover:bg-red-500 text-black font-bold py-3 rounded-lg"
          on:click={() => endRound(walletClient)}
          disabled={!connected}
        >
          End Round
        </Button.Root>
      {/if}

      {#if userCurrentShare > 0 && blocksRemaining > 0}
        <Alert.Root variant="destructive">
          <Alert.Description class="text-lg">
            Waiting for the round to contribute again!
          </Alert.Description>
        </Alert.Root>
      {/if}


      {#if connected && blocksRemaining > 0 && userCurrentShare == 0}
        <div class="flex flex-col gap-2 mt-4">
          <Input.Root
            placeholder="Enter at least {(minimumDonation / 1e18).toFixed(6)} ETH"
            bind:value={userContribution}
            type="number"
            min={(minimumDonation/ 1e18).toFixed(6)}
            step={minimumDonation}
            max="0.01"
            class="text-center"
          />

          {#if userContribution < minimumDonation / 1e18}
            <Alert.Root variant="destructive">
              <Alert.Description class="text-sm">
                Minimum {(minimumDonation ).toFixed(6)} ETH required
              </Alert.Description>
            </Alert.Root>
          {/if}

          <Button.Root
            class="w-full bg-blue-600 hover:bg-blue-500 text-white font-bold py-3 rounded-lg"
            on:click={() => contribute(userContribution * 1e18, walletClient)}
            disabled={userContribution < minimumDonation / 1e18 || blocksRemaining == 0 || userCurrentDonation > 0}
          >
            Contribute {userContribution} ETH
          </Button.Root>
        </div>
      {/if}
    </Card.Content>
    {/if}
  </Card.Root>

</div>

  </div>

<!-- Round Metrics -->
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
    <Card.Content class="text-center text-2xl font-bold">{userCurrentShare / 1e16} %</Card.Content>
  </Card.Root>
</div>

{:else if currentTab === 'info'}

  <div transition:fade>

  <Card.Header class="text-center space-y-4">
    <Card.Title class="text-2xl font-bold tracking-tight">
      Round Reward Split (RRS)
    </Card.Title>

    <Card.Description class="text-green-500 text-sm">
      Contribute ETH → Claim OLAS. Rewards distributed at round end.
    </Card.Description>
    </Card.Header>
    <Card.Content> 
    </Card.Content>

    


<div class="space-y-6 text-green-300 max-w-4xl mx-auto">
  <div class="grid grid-cols-1 sm:grid-cols-2 gap-6">

    <!-- Proportional Split -->
    <div class="bg-green-950 border border-green-700 rounded-lg p-3 flex flex-col gap-1">
      <div class="flex items-center gap-2 text-green-500 text-xs font-bold uppercase tracking-wide">
        <Users class="w-4 h-4" />
        Proportional Split
      </div>
      <div class="text-green-300 text-lg font-bold font-mono">
        8 contributors each round
      </div>
    </div>

    <!-- Round Rewards -->
    <div class="bg-green-950 border border-green-700 rounded-lg p-3 flex flex-col gap-1">
      <div class="flex items-center gap-2 text-green-500 text-xs font-bold uppercase tracking-wide">
        <Gift class="w-4 h-4" />
        Round Rewards
      </div>
      <div class="text-green-300 text-lg font-bold font-mono">
        {(roundRewards / 1e18).toFixed(2)} OLAS each round
      </div>
    </div>

    <!-- Round Progress -->
    <div class="bg-green-950 border border-green-700 rounded-lg p-3 flex flex-col gap-1">
      <div class="flex items-center gap-2 text-green-500 text-xs font-bold uppercase tracking-wide">
        <Clock class="w-4 h-4" />
        Round Progress
      </div>
      <div class="text-green-300 text-lg font-bold font-mono">
        {blocksRemaining}/{roundLength} blocks
      </div>
    </div>

    <!-- Minimum Donation -->
    <div class="bg-green-950 border border-green-700 rounded-lg p-3 flex flex-col gap-1">
      <div class="flex items-center gap-2 text-green-500 text-xs font-bold uppercase tracking-wide">
        <CircleDollarSign class="w-4 h-4" />
        Minimum Donation
      </div>
      <div class="text-green-300 text-lg font-bold font-mono">
        {(minimumDonation ).toFixed(6)} ETH
      </div>
    </div>

  </div>



  <!-- Round Summary -->
    <div class="space-y-6 text-green-300 max-w-4xl mx-auto">
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
               <strong class="text-green-100">OLAS rewards:</strong> Distributed at the end of each round based on your pro-rata contribution to the donation pool.
             </p>
           </li>
           <!-- Unclaimed Rewards -->
           <li class="flex items-start gap-4">
             <CircleDollarSign class="w-8 h-8 text-green-300 mt-1" />
             <p>
               <strong class="text-green-100">Unclaimed rewards:</strong> Recycled back into the pool to enhance long-term liquidity and promote greater fairness among participants.
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
               <strong class="text-green-100">Prisoner's Dilemma:</strong> Each round, you can donate more to increase your share of rewards — but if everyone does this, rewards are diluted.
             </p>
           </li>
           <!-- Prisoner's Dilemma -->
           <li class="flex items-start gap-4">

             <Alert.Root variant="destructive" class="mb-3">
               <Alert.Title class="text-red-500">Rewards Are Only Claimable for 1 Round!</Alert.Title>
               <Separator class="my-2" />
               <Alert.Description class="text-red-400">
                 <p>
                   If you do not claim your rewards within the current round, they will be donated to the pool and you will not receive them.
                 </p>
               </Alert.Description>
             </Alert.Root>
           </li>
         </ul>

         <!-- Topup Olasup incentives button. -->

          {#if connected }
            <div class="flex flex-col gap-2 mt-4">
              <Input.Root
                placeholder="Enter at least {(roundRewards / 1e18).toFixed(1)} OLAS"
                bind:value={olasTopUp}
                type="number"
                min={(roundRewards / 1e18)}
                step="1"
                class="text-center"
              />

              {#if userContribution < minimumDonation / 1e18}
                <Alert.Root variant="destructive">
                  <Alert.Description class="text-sm">
                    Minimum {(roundRewards/ 1e18).toFixed(1)} OLAS required
                  </Alert.Description>
                </Alert.Root>
              {/if}
            <Button.Root
              variant="default"
              class="bg-green-600 hover:bg-green-500 text-black font-bold py-3 rounded-lg w-full"
              onclick={() => topUpOlas(olasTopUp * 1e18,)}
            >
              Top Up OLAS. (THIS GIVES YOU NO SHARE IN THE POOL, IT FUNDS THE GAME)
            </Button.Root>

            </div>
          {/if}


       </Card.Content>
     </Card.Root>

    </div>
  </div>
</div>
 

{:else if currentTab === 'metrics'}
  <div transition:fade>

  <Card.Header class="text-center">
    <Card.Title class="text-2xl font-bold tracking-tight">
      Derolas Pool Metrics
    </Card.Title>
    <Card.Description class="text-green-500 text-sm">
        The <a href="https://balancer.fi/pools/base/v3/{poolId}" target="_blank" rel="noopener noreferrer" class="underline hover:text-green-400">
          Balancer pool
        </a> is the heart of the Derolas ecosystem, providing liquidity and enabling on-chain transactions and capturing value for OLAS holders.
      </Card.Description>

    </Card.Header>
    <Card.Content> 
    <Metrics />
    </Card.Content>

  <Card.Header class="text-center">
    <Card.Title class="text-2xl font-bold tracking-tight">
      Derolas Exchange Share Metrics
    </Card.Title>
    <Card.Description class="text-green-500 text-sm">
      The Derolas Exchange Share metrics provides insights into the % share of the Derolas pool as related to the total share of balancer volume.
      </Card.Description>
    </Card.Header>
    <Card.Content> 
    <BalMetrics />
    </Card.Content>
    


  </div>
{/if}

</Card.Root>
