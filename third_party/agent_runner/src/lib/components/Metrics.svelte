<script lang="ts">
  import { HandCoins, Clock, Users, Gift, DollarSign, CircleDollarSign, Info, Timer, BrainCircuit, TimerReset, Sparkles, Flame, SeparatorVertical, StopCircle, Coins } from "lucide-svelte";
  import * as Card from "$lib/components/ui/card";
   import {  onMount } from 'svelte';
  import * as echarts from 'echarts';
  
  let chartDivRoi: HTMLElement | null | undefined;
  let chartDivTVL: HTMLElement | null | undefined;
  let chartDivSharePrice: HTMLElement | null | undefined;
  let chartDivFees: HTMLElement | null | undefined;
  let chartDivShares: HTMLElement | null | undefined;

  let currentAPR: number = 0;
  let currentTrades24h: number = 0;
  let currentFees24h: number = 0;
  let currentTVL: number = 0;
  let currentShares: number = 0;
  let currentSharePrice: number = 0;
  let initialSharePrice: number = 0;


  import dayjs from 'dayjs';
    import { parse } from "svelte/compiler";
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




const darkGreenTheme = {
  backgroundColor: '#000000',
  textStyle: {
    color: '#00ff00',
    fontFamily: 'monospace',
  },
  axisLine: {
    lineStyle: {
      color: '#00ff00',
    },
  },
  splitLine: {
    lineStyle: {
      color: '#004400',
    },
  },
  tooltip: {
    backgroundColor: '#001100',
    borderColor: '#00ff00',
    textStyle: {
      color: '#00ff00',
    },
    // we round to 3 decimal places
  },
};

  

// Dummy time series price data for 9 tokens
const generateDummyData = () => {
  const symbols = ["weETH", "WETH", "DAI", "OLAS", "USDC", "DRV", "cbBTC", "LBTC", "DEROLAS"];
  const basePrices = {
    weETH: 3200,
    WETH: 3150,
    DAI: 1.0,
    OLAS: 2.5,
    USDC: 1.0,
    DRV: 0.25,
    cbBTC: 64000,
    LBTC: 63500,
    DEROLAS: 1.0
  };

  const hours = 100;
  const now = new Date();

  const data = symbols.map(symbol => {
    const prices = [];
    let price = basePrices[symbol as keyof typeof basePrices];
    for (let i = 0; i < hours; i++) {
      const time = new Date(now.getTime() - (hours - i) * 60 * 60 * 1000).toISOString();
      const change = (Math.random() - 0.5) * 0.02; // ±1% volatility
      if (symbol !== "DEROLAS") price *= 1 + change;
      prices.push([time, parseFloat(price.toFixed(2))]);
    }
    return { name: symbol, 
      type: "line", 
      data: prices , 
      emphasis: { focus: 'series' },
      showSymbol:false,
    };
  });

  return data;
};


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

const buildPriceQuery = (addresses: any[], chain = "BASE", range = "THIRTY_DAY") => {
  const fragments = addresses.map((addr: any, i: any) => `
    token${i}: tokenGetHistoricalPrices(
      addresses: ["${addr}"],
      chain: ${chain},
      range: ${range}
    ) {
      prices {
        price
        timestamp
      }
    }`).join("\n");

  return `query { ${fragments} }`;
};

const buildDerolasQuery = (chain = "BASE", id = POOL_ID, range = "THIRTY_DAYS") => `
  query {
    poolGetSnapshots(chain: ${chain}, id: "${id}", range: ${range}) {
      timestamp
      totalLiquidity
      totalShares
      holdersCount
      swapsCount
      fees24h
      sharePrice
      totalSwapFee
      totalLiquidity
  }
    }
`;

export async function generateAlignedPriceMatrix() {
  const [tokenRes, derolaRes] = await Promise.all([
    fetch(GRAPHQL_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: buildPriceQuery(ADDRESSES) })
    }),
    fetch(GRAPHQL_ENDPOINT, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: buildDerolasQuery() })
    })
  ]);

  const tokenJson = await tokenRes.json();
  const derolaJson = await derolaRes.json();

  if (!tokenJson.data || !derolaJson.data.poolGetSnapshots)
    throw new Error("Data fetch failed");

  // Flatten token data
  const tokenData: Record<string, Record<string, number | { totalLiquidity: number; totalShares: number; holdersCount: any; swapsCount: any; fees24h: number; totalSwapFee: number; sharePrice: number; }>> = {};
  for (const [key, value] of Object.entries(tokenJson.data)) {
    const index = parseInt(key.replace("token", ""));
    const address = ADDRESSES[index];
    const symbol = ADDRESS_TO_SYMBOL[address];
    const entries = (value as { prices: { price: number; timestamp: number }[] }[])[0]?.prices?.filter(p => p.price != null) || [];

    for (const { 
      price, 
      timestamp, 
      
    } of entries) {
      const ts = dayjs.unix(timestamp).startOf('hour').toISOString();
      if (!tokenData[ts]) tokenData[ts] = {};
      tokenData[ts][symbol] = parseFloat(price.toString());
    }
  }

  // Process Derolas
  const derolaPrices = derolaJson.data.poolGetSnapshots || [];

  for (const snapshot of derolaPrices) {
  const ts = dayjs.unix(snapshot.timestamp).startOf('hour').toISOString();
  if (!tokenData[ts]) tokenData[ts] = {};
  tokenData[ts]["DEROLAS"] = parseFloat(snapshot.sharePrice);
  tokenData[ts]["_DEROLAS_META"] = {
    totalLiquidity: parseFloat(snapshot.totalLiquidity),
    totalShares: parseFloat(snapshot.totalShares),
    holdersCount: snapshot.holdersCount,
    swapsCount: snapshot.swapsCount,
    fees24h: parseFloat(snapshot.fees24h),
    totalSwapFee: parseFloat(snapshot.totalSwapFee),
    sharePrice: parseFloat(snapshot.sharePrice),
  };
  currentTrades24h = snapshot.swapsCount;
  currentFees24h = parseFloat(snapshot.fees24h);
  currentTVL = parseFloat(snapshot.totalLiquidity);
  currentAPR = (parseFloat(snapshot.fees24h) * 365 / parseFloat(snapshot.totalLiquidity)) * 100;
  // current shares is the total shares in the pool
  currentShares = parseFloat(snapshot.totalShares);
}
  // Set initial share price based on the first snapshot
  if (derolaPrices.length > 0) {
    initialSharePrice = parseFloat(derolaPrices[0].sharePrice);
    currentSharePrice = parseFloat(derolaPrices[derolaPrices.length - 1].sharePrice);
  } else {
    initialSharePrice = 0;
    currentSharePrice = 0;
  }

  // Filter timestamps to shared minimum
  const allSymbols = [...SYMBOLS, "DEROLAS"];
  const validTimestamps = Object.entries(tokenData)
    .filter(([, row]) => allSymbols.every(sym => sym in row))
    .map(([ts]) => ts)
    .sort();

  const minTs = validTimestamps[0];

  const matrix = validTimestamps.map(ts => ({
    timestamp: ts,
    ...tokenData[ts]
  })).filter(row => dayjs(row.timestamp).isAfter(minTs));

  return matrix;
}




let chartRoi: echarts.ECharts;
let chartTVL: echarts.ECharts;
let chart24hFees: echarts.ECharts;

let chartSharePrice: echarts.ECharts;
let chartShares: echarts.ECharts;


  onMount(() => {
    let data
    interface DerolasMeta {
      totalLiquidity: number;
      totalShares: number;
      holdersCount: number;
      swapsCount: number;
      fees24h: number;
      totalSwapFee: number;
      sharePrice: number;
    }
    
    interface MatrixRow {
      timestamp: string;
      [key: string]: number | DerolasMeta | string;
    }
    
    const matrix: Promise<MatrixRow[]> = generateAlignedPriceMatrix();
    chartRoi = echarts.init(chartDivRoi, darkGreenTheme,  { renderer: 'canvas' });
    data = matrix.then((matrix) => {
        const tokens = Object.keys(matrix[0]).filter(k => k !== "timestamp" && k !== "_DEROLAS_META");
        const first = matrix[0];
        const baseline = Object.fromEntries(tokens.map(t => [t, first[t]]));

          return tokens.map(symbol => ({
            name: symbol,
            type: "line",
            showSymbol: false,
            emphasis: { focus: 'series' },
            data: matrix.map(row => [
              row.timestamp,
              (((row[symbol] as number) / (baseline[symbol] as number)) - 1) * 100
            ])
          }));
        });

    data.then((data) => {
      pltData(data, chartRoi);
    });

    // longer term we will abstract the series logic, for now we mak another chart.

    chartTVL = echarts.init(chartDivTVL, darkGreenTheme,  { renderer: 'canvas' });
    data = matrix.then((matrix) => {
      // We only want the derolas meta data
      // We want to raw tvl 
      const tokens = Object.keys(matrix[0]).filter(k => k !== "timestamp" && k === "_DEROLAS_META");

      // no baseline needed for this chart as its a bar chart
      // We do need to make suer the label is called "TVL" and not "_DEROLAS_META"
      return tokens.map(symbol => ({
        name: "TVL",
        type: "line",
        showSymbol: false,
        emphasis: { focus: 'series' },
        data: matrix.map(row => [
          row.timestamp,
          typeof row[symbol] === 'object' && 'totalLiquidity' in row[symbol] ? row[symbol].totalLiquidity : 0
        ]),
        label: {
          show: true,
          position: 'top',
          formatter: (params: any) => {
            return `${params.value[1].toFixed(0)}`;
          },
          textStyle: {
            color: '#00ff00',
            fontSize: 10,
          }
        },
      }));
    });

    data.then((data) => {
      pltData(data, chartTVL);
    });

    chart24hFees = echarts.init(chartDivFees, darkGreenTheme,  { renderer: 'canvas' });
    data = matrix.then((matrix) => {
      // We only want the derolas meta data
      // We want to raw tvl 
      const tokens = Object.keys(matrix[0]).filter(k => k !== "timestamp" && k === "_DEROLAS_META");

      // no baseline needed for this chart as its a bar chart
      // We do need to make suer the label is called "TVL" and not "_DEROLAS_META"
      return tokens.map(symbol => ({
        name: "Fees",
        type: "line",
        showSymbol: false,
        emphasis: { focus: 'series' },
        data: matrix.map(row => [
          row.timestamp,
          typeof row[symbol] === 'object' && 'fees24h' in row[symbol] ? row[symbol].fees24h : 0
        ]),
        label: {
          show: true,
          position: 'top',
          formatter: (params: any) => {
            return `${params.value[1].toFixed(2)}`;
          },
          textStyle: {
            color: '#00ff00',
            fontSize: 10,
          }
        },
      }));
    });
    data.then((data) => {
      pltData(data, chart24hFees);
    });


  chartSharePrice = echarts.init(chartDivSharePrice, darkGreenTheme,  { renderer: 'canvas' });


data = matrix.then((matrix) => {
  const tokens = Object.keys(matrix[0]).filter(k => k === "_DEROLAS_META");

  return tokens.map(symbol => ({
    name: "Share Price",
    type: "line",
    showSymbol: false,
    emphasis: { focus: 'series' },
    data: matrix.map(row => [
      row.timestamp, // Ensure this is a valid timestamp (ISO or Unix ms)
      typeof row[symbol] === 'object' && 'sharePrice' in row[symbol] ? row[symbol].sharePrice : 0
    ]),
    label: {
      show: true,
      position: 'top',
      textStyle: {
        color: '#00ff00',
        fontSize: 10,
      }
    }
  }));
});

data.then((seriesData) => {
    const allYValues = seriesData
    .flatMap(s => s.data)
    .map(d => d[1])
    .filter(v => typeof v === 'number' && isFinite(v) && v < 1e6); // Ignore rogue large numbers

  console.log("All Y Values:", allYValues);
  console.log("Series Data:", seriesData);
  const option = {

    grid: {
      top: 15,
      bottom: 10,
      left: 10,
      right: 15,
      containLabel: true
    },
    tooltip: { trigger: 'axis' },
    xAxis: {
      type: 'time',
    },
    yAxis: {
      type: 'value',
      max: Math.max(...allYValues.filter((v): v is number => typeof v === 'number')) * 1.01,
      min: Math.min(...allYValues.filter((v): v is number => typeof v === 'number')) * 0.99,
      splitLine: {
        show: false
      },
      axisLabel: {
        formatter: (value: number) => {
          return value.toFixed(2);
        }
      }
    },
    series: seriesData
  };

  chartSharePrice.setOption(option);
});

  console.log("Matrix:", matrix);
  console.log("Data:", data);

  chartShares = echarts.init(chartDivShares, darkGreenTheme,  { renderer: 'canvas' });
  data = matrix.then((matrix) => {
    const tokens = Object.keys(matrix[0]).filter(k => k === "_DEROLAS_META");
    return tokens.map(symbol => ({
      type: "line",
      showSymbol: false,
      emphasis: { focus: 'series' },
      data: matrix.map(row => [
        row.timestamp,
        typeof row[symbol] === 'object' && 'totalShares' in row[symbol] ? row[symbol].totalShares : 0
      ]),
      label: {
        show: false,
        position: 'top',
        textStyle: {
          color: '#00ff00',
          fontSize: 10,
        }
      },
    }));
  });
  data.then((data) => {
    pltData(data, chartShares);
  });

  const observer = new ResizeObserver(() => {
    chartTVL?.resize();
    chart24hFees?.resize();
    chartSharePrice?.resize();
    chartRoi?.resize();
    chartShares?.resize();

  });

  // we now plot the shares chart
  if (chartDivTVL && chartDivFees && chartDivSharePrice && chartDivRoi && chartDivShares) {
    observer.observe(chartDivTVL);
    observer.observe(chartDivFees);
    observer.observe(chartDivSharePrice);
    observer.observe(chartDivRoi);
    observer.observe(chartDivShares);
  }

});


function pltData(data: any, chart: any) {
  chart.setOption({
    backgroundColor: '#000000',
  grid: {
    top: 15,
    bottom: 30,
    left: 10,
    right: 15,
    containLabel: true
  },
    tooltip: { trigger: 'axis' },
    legend: {
      type: 'scroll',
      orient: 'horizontal',
      top: 'bottom',
      textStyle: { fontSize: 10, color: '#00ff00' }
    },

    xAxis: {
      type: 'time',
      axisLine: { lineStyle: { color: '#00ff00' } },
      splitLine: { lineStyle: { color: '#003300' } },
      axisLabel: {
        // formatter: (value: number) => {
        //   const date = new Date(value);
        //   return `${date.getMonth() + 1}/${date.getDate()}`;
        // },
        textStyle: { color: '#00ff00' }
      },
    },
    yAxis: {
      type: 'value',
      axisLine: { lineStyle: { color: '#00ff00' } },
      splitLine: { lineStyle: { color: '#003300' } },

    },
    series: data,
    // We make sure everything is green
    textStyle: {
      color: '#00ff00',
      fontFamily: 'monospace',
    },
    emphasis: {
      focus: 'series',
      itemStyle: {
        color: '#00ff00',
      },
      label: {
        show: true,
        textStyle: {
          color: '#00ff00',
          fontSize: 10,
        }
      }
    },
    // by default e set the colour of the data to be green

  });

}


</script>
<!-- Responsive chart grid layout -->
<div class="flex flex-col gap-2 w-full p-0">

  <!-- Top row: Share Price and ROI -->
  <div class="flex flex-col gap-4 w-full p-0">
    <Card.Root class="flex-1 min-w-0 p-0">
      <Card.Content>
        <Card.Title>Derolas Share Price.</Card.Title>
        <div bind:this={chartDivSharePrice} class="w-full h-[150px]  p-0 m-0"></div>
      </Card.Content>
    </Card.Root>


  <div class="grid text-center grid-cols-1 sm:grid-cols-2 gap-6">

    <div class="bg-green-950 border border-green-700 rounded-lg p-3 flex flex-col gap-1">
      <div class="flex items-center gap-2 text-green-500 text-xs font-bold uppercase tracking-wide">
        <Users class="w-4 h-4" />
        Current APR
      </div>
      <div class="text-green-300 text-lg font-bold font-mono">
        {(currentAPR ).toFixed(2)}%
      </div>
    </div>

    <div class="bg-green-950 border border-green-700 rounded-lg p-3 flex flex-col gap-1">
      <div class="flex items-center gap-2 text-green-500 text-xs font-bold uppercase tracking-wide">
        <Gift class="w-4 h-4" />
        Fees 24h
      </div>
      <div class="text-green-300 text-lg font-bold font-mono">
        ${currentFees24h.toFixed(2)}
        <!-- {(roundRewards / 1e18).toFixed(2)} OLAS each round -->
      </div>
    </div>

    <!-- Total Swaps -->
    <div class="bg-green-950 border border-green-700 rounded-lg p-3 flex flex-col gap-1">
      <div class="flex items-center gap-2 text-green-500 text-xs font-bold uppercase tracking-wide">
        <Flame class="w-4 h-4" />
        Total Shares
      </div>
      <div class="text-green-300 text-lg font-bold font-mono">
        {currentShares.toFixed(2)}
      </div>
    </div>

    <!-- TVL -->

    <div class="bg-green-950 border border-green-700 rounded-lg p-3 flex flex-col gap-1">
      <div class="flex items-center gap-2 text-green-500 text-xs font-bold uppercase tracking-wide">
      <HandCoins class="w-4 h-4" />
      Total Value Locked (TVL)
      </div>
      <div class="text-green-300 text-lg font-bold font-mono">
      ${currentTVL.toFixed(2)}
      </div>
    </div>

    <div class="bg-green-950 border border-green-700 rounded-lg p-3 flex flex-col gap-1">
      <div class="flex items-center gap-2 text-green-500 text-xs font-bold uppercase tracking-wide">
      <Coins class="w-4 h-4" />
      Current Share Price
      </div>
      <div class="text-green-300 text-lg font-bold font-mono">
      ${currentShares > 0 ? (currentTVL / currentShares).toFixed(2) : "N/A"}
      </div>
    </div>


    <div class="bg-green-950 border border-green-700 rounded-lg p-3 flex flex-col gap-1">
      <div class="flex items-center gap-2 text-green-500 text-xs font-bold uppercase tracking-wide">
      <Coins class="w-4 h-4" />
      Current ROI
      </div>
      <div class="text-green-300 text-lg font-bold font-mono">
      {currentSharePrice > 0 ? ((currentSharePrice - initialSharePrice) / initialSharePrice * 100).toFixed(2) : "N/A"}%
      </div>
    </div>

  

  </div>
  <!-- Shares Price and ROI -->
  <div class="flex flex-col gap-4 w-full p-0">

    </div>  
    <Card.Root class="flex-1 min-w-0">
      <Card.Content>
        <Card.Title>Cumulative ROI of Assets in Bundle.</Card.Title>
        <div bind:this={chartDivRoi} class="w-full h-[200px]  p-0 m-0"></div>
      </Card.Content>
    </Card.Root>
  </div>

  <!-- Bottom row: TVL and Fees -->
  <div class="flex flex-col md:flex-row gap-4 w-full">
    <Card.Root class="flex-1 min-w-0">
      <Card.Content>
        <Card.Title>TVL (USD) over previous 30 Days.</Card.Title>
        <div bind:this={chartDivTVL} class="w-full h-[250px] p-0 m-0"></div>
      </Card.Content>
    </Card.Root>

    <Card.Root class="flex-1 min-w-0">
      <Card.Content>
        <Card.Title>Fees (USD) over previous 30 Days.</Card.Title>
        <div bind:this={chartDivFees} class="w-full h-[250px]"></div>
      </Card.Content>
    </Card.Root>
  </div>

    <Card.Root class="flex-1 min-w-0 p-0">
      <Card.Content>
        <Card.Title>Derolas LP Shares.</Card.Title>
        <div bind:this={chartDivShares} class="w-full h-[150px]  p-0 m-0"></div>
      </Card.Content>
    </Card.Root>

</div>
