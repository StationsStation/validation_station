<script lang="ts">
  import { HandCoins, Users, Gift, Flame, } from "lucide-svelte";
  import {  onMount } from 'svelte';
  
  let currentTVL: number = 0;

  let total24hrVolume: number = 0;
  let currentDerolasVolume24h: number = 0;
  let balancerBaseTVL: number = 0;

  // struuct for exchanges
  interface Exchange {
    name: string;
  }

  // struct for the chains  
  interface Chain {
    name: string;
    id: number;
    icon: string;
  }
  
  let poolId = "0x7b4c560f33a71a9f7a500af3c4c65b46fbbafdb7";

  // we now have a hashmap fo derive and balancer
  // we will use this to get the symbol from the address

  let supportedChains: Chain[] = [
    { name: "Base", id: 8453, icon: "base" },
    { name: "Derive", id: 1, icon: "ethereum" },
  ];




const GRAPHQL_ENDPOINT = "https://api-v3.balancer.fi/";
const POOL_ID = "0x7b4c560f33a71a9f7a500af3c4c65b46fbbafdb7";

const ADDRESSES = [
  "0x04C0599Ae5A44757c0af6F9eC3b93da8976c150A",
  "0x4200000000000000000000000000000000000006",
  "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
  "0x54330d28ca3357F294334BDC454a032e7f353416",
  "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
  "0x9d0E8f5b25384C7310CB8C6aE32C8fbeb645d083",
  "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf",
  "0xecAc9C5F704e954931349Da37F60E39f515c11c1"
];
const SYMBOLS = ["weETH", "WETH", "DAI", "OLAS", "USDC", "DRV", "cbBTC", "LBTC"];
const ADDRESS_TO_SYMBOL = Object.fromEntries(ADDRESSES.map((a, i) => [a, SYMBOLS[i]]));


const buildDerolasQuery = `
query GetPool(
  $chain: GqlChain
  $id: String!
) {
  poolGetPool(
    chain: $chain
    id: $id
  ) {
    dynamicData {
      volume24h
      totalShares
      totalLiquidity
      swapsCount
      fees24h
      lifetimeSwapFees
    }
    symbol
    
  }
}

`;

const buildBalancerVolumeQuery = () => `
  query protocolMetricsChain($chain: GqlChain) {
    protocolMetricsChain(chain: $chain) {
      chainId
      poolCount
      swapVolume24h
      totalLiquidity
    }
  }
`;

  
export async function generateAlignedPriceMatrix() {
  const [
    exchangeVoldata,
    derolasPoolData,
  ] = await Promise.all([
    fetch(GRAPHQL_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: buildBalancerVolumeQuery(),
        variables: {
          chain: "BASE"
        }
      })
    }).then(res => res.json()),
    fetch(GRAPHQL_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query: buildDerolasQuery,
        variables: {
          chain: "BASE",
          id: POOL_ID
        }
      })
    }).then(res => res.json()),
  ]);

  const exchangeVolJson = exchangeVoldata;
  console.log("Exchange Volume Data:", exchangeVolJson);
  if (!exchangeVolJson.data || !exchangeVolJson.data.protocolMetricsChain) {
    throw new Error("Exchange volume data fetch failed");
  }


  console.log("Exchange Volume Data:", exchangeVolJson.data.protocolMetricsChain);
  console.log("Total Liquidity:", exchangeVolJson.data.protocolMetricsChain.totalLiquidity);
  console.log("Derolas Pool Data:", derolasPoolData.data.poolGetPool.dynamicData);

  const exchangeVolume = exchangeVolJson.data.protocolMetricsChain;
  if (!exchangeVolume || !exchangeVolume.swapVolume24h) {
    throw new Error("Exchange volume data fetch failed");
  }
  const exchangeVolume24h = parseFloat(exchangeVolume.swapVolume24h);
  if (isNaN(exchangeVolume24h)) {
    throw new Error("Invalid exchange volume data");
  }
  console.log("Exchange Volume 24h:", exchangeVolume24h);
  // Add exchange volume to tokenData
  total24hrVolume = exchangeVolume24h;
  currentDerolasVolume24h = parseFloat(derolasPoolData.data.poolGetPool.dynamicData.volume24h);
  balancerBaseTVL = parseFloat(exchangeVolJson.data.protocolMetricsChain.totalLiquidity);
  currentTVL = parseFloat(derolasPoolData.data.poolGetPool.dynamicData.totalLiquidity);
  console.log("Current Derolas Volume 24h:", currentDerolasVolume24h);

}



  onMount(() => {
    let data
    const matrix = generateAlignedPriceMatrix();
   
  });





</script>
<!-- Responsive chart grid layout -->
<div class="flex flex-col gap-2 w-full p-0">

  <div class="flex flex-col gap-4 w-full p-0">
  <!-- Top row: Share Price and ROI
    <Card.Root class="flex-1 min-w-0 p-0">
      <Card.Content>
        <Card.Title>Derolas Share Price.</Card.Title>
        <div bind:this={chartDivSharePrice} class="w-full h-[150px]  p-0 m-0"></div>
      </Card.Content>
    </Card.Root> -->

  <div class="grid text-center grid-cols-1 sm:grid-cols-2 gap-4">

    <div class="bg-green-950 border border-green-700 rounded-lg p-3 flex flex-col gap-1">
      <div class="flex items-center gap-2 text-green-500 text-xs font-bold uppercase tracking-wide">
      <HandCoins class="w-4 h-4" />
      Balancer Base TVL.
      </div>
      <div class="text-green-300 text-lg font-bold font-mono">
      {balancerBaseTVL.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
      </div>
    </div>

    <div class="bg-green-950 border border-green-700 rounded-lg p-3 flex flex-col gap-1">
      <div class="flex items-center gap-2 text-green-500 text-xs font-bold uppercase tracking-wide">
      <HandCoins class="w-4 h-4" />
      Derolas Pool TVL.
      </div>
      <div class="text-green-300 text-lg font-bold font-mono">
      {currentTVL.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
      </div>
    </div>


    <div class="bg-green-950 border border-green-700 rounded-lg p-3 flex flex-col gap-1">
      <div class="flex items-center gap-2 text-green-500 text-xs font-bold uppercase tracking-wide">
        <Users class="w-4 h-4" />
        Total Volume on Balancer Base.
      </div>
      <div class="text-green-300 text-lg font-bold font-mono">
        {total24hrVolume.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
      </div>
    </div>

    <div class="bg-green-950 border border-green-700 rounded-lg p-3 flex flex-col gap-1">
      <div class="flex items-center gap-2 text-green-500 text-xs font-bold uppercase tracking-wide">
        <Gift class="w-4 h-4" />
        Volume from Derolas Pool.
      </div>
      <div class="text-green-300 text-lg font-bold font-mono">
        {currentDerolasVolume24h.toLocaleString('en-US', { style: 'currency', currency: 'USD' })}
        <!-- {(roundRewards / 1e18).toFixed(2)} OLAS each round -->
      </div>
    </div>

    <!-- Total Swaps -->
    <!-- TVL -->



    <!-- Average capital efficiency -->

    <div class="bg-green-950 border border-green-700 rounded-lg p-3 flex flex-col gap-1">
      <div class="flex items-center gap-2 text-green-500 text-xs font-bold uppercase tracking-wide">
        <HandCoins class="w-4 h-4" />
        Average Balancer Capital Efficiency Ratio.
      </div>
      <div class="text-green-300 text-lg font-bold font-mono">
        { (1 / (balancerBaseTVL / total24hrVolume)).toFixed(2)}
      </div>
      </div>
    <!-- Total Tvl is Derolas pool -->
    <div class="bg-green-950 border border-green-700 rounded-lg p-3 flex flex-col gap-1">
      <div class="flex items-center gap-2 text-green-500 text-xs font-bold uppercase tracking-wide">
        <HandCoins class="w-4 h-4" />
        Derolas Pool Capital Efficiency Ratio.
      </div>
      <div class="text-green-300 text-lg font-bold font-mono">
        {(1 / (currentTVL / currentDerolasVolume24h)).toFixed(2)}
      </div>

    </div>

    <!-- Percentage tvl is Derolas -->
    <div class="bg-green-950 border border-green-700 rounded-lg p-3 flex flex-col gap-1">
      <div class="flex items-center gap-2 text-green-500 text-xs font-bold uppercase tracking-wide">
        <Flame class="w-4 h-4" />
        Total % of Bal TVL on Base is Derolas.
      </div>
      <div class="text-green-300 text-lg font-bold font-mono">
        {(currentTVL / balancerBaseTVL * 100).toFixed(2)}%
      </div>
    </div>

    <div class="bg-green-950 border border-green-700 rounded-lg p-3 flex flex-col gap-1">
      <div class="flex items-center gap-2 text-green-500 text-xs font-bold uppercase tracking-wide">
        <Flame class="w-4 h-4" />
        Total % of Bal Volume on Base is Derolas.
      </div>
      <div class="text-green-300 text-lg font-bold font-mono">
        {(currentDerolasVolume24h / total24hrVolume * 100).toFixed(2)}%
      </div>
    </div>
  </div>
  </div>
</div>
