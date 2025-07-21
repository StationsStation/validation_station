
  let FunctionNames = {
    canPlayGame : 'canPlayGame',
    roundLength : 'getRoundLength',
    getRoundProgress : 'getRoundProgress',
    getTotalContributions : 'getTotalDonated',
    getTotalRewards : 'getTotalRewards',
    getUserContributions : 'getUserContributions',
    getUserRewards : 'getUserRewards',
    getBlockRemaining : 'getBlocksRemaining',
    minimumDonation : 'minimumDonation',
    topUpIncentives : 'topUpIncentiveBalance',
    endRound : 'endRound',
    getIncentiveBalance : 'currentIncentiveBalance',
    getRoundRewards : 'getRoundRewards',
    getCurrentRound : 'getCurrentRound',
    donate: 'donate',
    claim: 'claim',
  };
import IncentiveTokenAbi from './IERC20.json';
import DerolasStakingJson from './DerolasStaking.json';
import { readContract, type CreateConnectorFn } from '@wagmi/core'
import {writeContract} from 'viem/actions'
import {custom, type Abi, type Client} from 'viem'
import { base, } from 'viem/chains'; // or wherever your chain imports come from
import { createConfig, http } from '@wagmi/core'
import { createClient, createWalletClient } from 'viem'
import { toast } from 'svelte-sonner';

const derolasAbi = DerolasStakingJson;

const BASE_RPC_URL = "https://base.llamarpc.com";


const configWrite = createConfig({
  chains: [base, base],
  transports: {
    [base.id]: http(BASE_RPC_URL),
  },
})




let DEPLOYED_CONTRACT_ADDRESS: `0x${string}` = derolasAbi.address as `0x${string}`;
let OLAS_TOKEN_ADDRESS: `0x${string}` = "0x54330d28ca3357f294334bdc454a032e7f353416";



async function topUpOlas(topUpAmount: number) {
  console.log('Topping up OLAS...');
  // Logic to top up OLAS
  console.log('Round Rewards:', topUpAmount);
  const _accounts = await (window as any).ethereum.request({ method: 'eth_requestAccounts' });
  const _account = _accounts[0];
  console.log('Account:', _account);
  const walletClient = createWalletClient({
    chain: base,
    transport: custom((window as any).ethereum)
  });
  const accounts = await walletClient.getAddresses();
  let abi = derolasAbi.abi;

  // We now check the approvals 
  const olasToken = await readContract(configWrite, {
    address: OLAS_TOKEN_ADDRESS,
    abi: IncentiveTokenAbi.abi,
    functionName: 'allowance',
    args: [accounts[0], DEPLOYED_CONTRACT_ADDRESS]
  });
  console.log('Allowance:', olasToken);
  if (Number(olasToken) < topUpAmount) {
    console.log('Not enough allowance, approving...');
    const tx = await writeContract(walletClient, {
      abi: IncentiveTokenAbi.abi,
      address: OLAS_TOKEN_ADDRESS,
      functionName: 'approve',
      args: [DEPLOYED_CONTRACT_ADDRESS, BigInt(topUpAmount)],
      account: accounts[0],
    });
    console.log('Transaction submitted:', tx);
  } else {
    console.log('Allowance is sufficient');
  }
  // Now we can top up the incentives



  const tx = await writeContract(walletClient, {
    abi: abi,
    address: DEPLOYED_CONTRACT_ADDRESS,
    functionName: FunctionNames.topUpIncentives,
    args: [BigInt(topUpAmount)],
    account: accounts[0],
    gas: BigInt(3184000),
  });

  console.log('Transaction submitted:', tx);

}

  async function claim(walletClient: any) {
    console.log('Claiming OLAS...');
    // Logic to claim OLAS
    const accounts = await walletClient.getAddresses();
    console.log(accounts);
    const tx = await writeContract(walletClient, {
      abi: derolasAbi.abi,
      address: DEPLOYED_CONTRACT_ADDRESS,
      functionName: FunctionNames.claim,
      args: [],
      account: accounts[0],
      gas: BigInt(8888888),
      chain: base,
    });

  }





async function endRound(walletClient: any) {
  console.log('Ending round...');

  const accounts = await walletClient.getAddresses();
  console.log(accounts);
  const tx = await writeContract(walletClient, {
    abi: derolasAbi.abi,
    address: DEPLOYED_CONTRACT_ADDRESS,
    functionName: 'endRound',
    args: [],
    account: accounts[0],
    chain: base,
    gas: BigInt(8888888),
  });

  console.log('Transaction submitted:', tx);
}



  async function contribute(donation: number, walletClient: any) {
    console.log('Contributing ETH...');
    // Logic to contribute ETH
    const accounts = await walletClient.getAddresses();
    const tx = await writeContract(walletClient, {
      abi: derolasAbi.abi,
      address: DEPLOYED_CONTRACT_ADDRESS,
      functionName: FunctionNames.donate,
      args: [],
      account: accounts[0],
      value: BigInt(donation),
      gas: BigInt(8888888),
      chain: base,
    });

    console.log('Transaction submitted:', tx);

}


async function checkTxnStatus(txHash: string, walletClient: any) {
  console.log('Checking transaction status...');
  const receipt = await walletClient.getTransactionReceipt(txHash);
  if (receipt && receipt.status === 1) {
    toast.success('Transaction successful!');
  } else {
    toast.error('Transaction failed!');
  }

}



async function loadContracts(userAddress: `0x${string}`) {
  // console.log('Loading game state...');

  const _config = createConfig({
    chains: [base],
    client({ chain }) {
      return createClient({ chain, transport: http(BASE_RPC_URL) })
    },
  });

  console.log('User Address:', userAddress);
  console.log('Contract Address:', DEPLOYED_CONTRACT_ADDRESS);
  const gameState = await readContract(_config, {
    address: DEPLOYED_CONTRACT_ADDRESS,
    abi: derolasAbi.abi,
    functionName: "getGameState",
    args: [userAddress],
  }) as {
    blocksRemaining: bigint;
    canPlayGame: boolean;
    currentRound: bigint;
    hasClaimed: boolean;
    incentiveBalance: bigint;
    minimumDonation: bigint;
    roundEndBlock: bigint;
    roundLength: bigint;
    roundRewards: bigint;
    totalClaimed: bigint;
    totalDonated: bigint;
    userClaimable: bigint;
    userCurrentDonation: bigint;
    userCurrentShare: bigint;
  };
  
  console.log('Game State:', gameState);
  return {
    blocksRemaining: Number(gameState.blocksRemaining),
    canPlayGame: Boolean(gameState.canPlayGame),
    currentRound: Number(gameState.currentRound),
    hasClaimed: Boolean(gameState.hasClaimed),
    incentiveBalance: Number(gameState.incentiveBalance),
    minimumDonation: Number(gameState.minimumDonation),
    roundEndBlock: Number(gameState.roundEndBlock),
    roundLength: Number(gameState.roundLength),
    roundRewards: Number(gameState.roundRewards),
    totalClaimed: Number(gameState.totalClaimed),
    totalDonated: Number(gameState.totalDonated),
    userClaimable: Number(gameState.userClaimable),
    userCurrentDonation: Number(gameState.userCurrentDonation),
    userCurrentShare: Number(gameState.userCurrentShare),
  };

}



  export {
    loadContracts,
    topUpOlas,
    endRound,
    contribute,
    claim,
    FunctionNames,
    OLAS_TOKEN_ADDRESS,
    DEPLOYED_CONTRACT_ADDRESS,
  }