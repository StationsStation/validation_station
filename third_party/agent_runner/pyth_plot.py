"""

"""
import requests
import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use("WebAgg")  # or "Qt5Agg" if you have PyQt5 installed

GRAPHQL_ENDPOINT = "https://api-v3.balancer.fi/"

def filter_by_min_timestamp(df, min_timestamp=None):
    if min_timestamp is None:
        min_timestamp = df["timestamp"].min()
    return df[df["timestamp"] > min_timestamp]



def fetch_prices(endpoint):

    query = build_batched_historical_prices_query(ADDRESSES)
    print(query)
    headers = {
        "Content-Type": "application/json"
    }
    payload = {
        "query": query
    }
    response = requests.post(endpoint, json=payload, headers=headers)

    if response.status_code != 200:
        raise RuntimeError(f"Query failed with status code {response.status_code}: {response.text}")

    result = response.json()


    return result

def cut_all_prices_to_common_start(all_prices):
    # Step 1: Find the min timestamp for each address
    asset_mins = {}
    for addr, prices in all_prices.items():
        min_ts = min(int(p["timestamp"]) for p in prices)
        asset_mins[addr] = min_ts

    # Step 2: Find the newest minimum across all addresses
    newest_common_min = max(asset_mins.values())

    # Step 3: Cut each asset's price history
    filtered = {}
    for addr, prices in all_prices.items():
        filtered[addr] = [
            p for p in prices if int(p["timestamp"]) >= newest_common_min
        ]

    return filtered


def parse_historical_prices(result):

    flat_rows = []

    # This map must be built right after constructing the query
    token_id_to_address = {f"token{idx}": address for idx, address in enumerate(ADDRESSES)}

    for token_id, token_address in token_id_to_address.items():
        token_data = result["data"][token_id][0]
        if not token_data:
            print(f"No prices for {token_id}")
            continue

        # Filter out prices with None values
        prices = [p for p in token_data['prices'] if p["price"] is not None]

        for price in prices:
            flat_rows.append({
                "address": token_address,
                "symbol": ADDRESS_TO_SYMBOL[token_address],
                "price": price["price"],
                "timestamp": price["timestamp"],
            })
    


    if not flat_rows:
        raise ValueError("No price data extracted")

    df = pd.DataFrame(flat_rows)
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    df["price"] = pd.to_numeric(df["price"], errors="coerce")
    return df



ADDRESSES = [
      "0x04C0599Ae5A44757c0af6F9eC3b93da8976c150A",
      "0x4200000000000000000000000000000000000006",
      "0x50c5725949A6F0c72E6C4a641F24049A917DB0Cb",
      "0x54330d28ca3357F294334BDC454a032e7f353416",
      "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
      "0x9d0E8f5b25384C7310CB8C6aE32C8fbeb645d083",
      "0xcbB7C0000aB88B473b1f5aFd9ef808440eed33Bf",
      "0xecAc9C5F704e954931349Da37F60E39f515c11c1"
    ]
ADDRESS_TO_NAME = [
    "weETH",
    "WETH",
    "DAI",
    "OLAS",
    "USDC",
    "DRV",
    "cbBTC",
    "LBTC",
]
ADDRESS_TO_SYMBOL = dict(zip(ADDRESSES, ADDRESS_TO_NAME))
token_id_to_address = {f"token{idx}": address for idx, address in enumerate(ADDRESSES)}





def build_batched_historical_prices_query(addresses, chain="BASE", range_="THIRTY_DAY"):
    query_fragments = []
    for idx, address in enumerate(addresses):
        fragment = f"""
        token{idx}: tokenGetHistoricalPrices(
            addresses: ["{address}"],
            chain: {chain},
            range: {range_}
        ) {{
            prices {{
                price
                timestamp
            }}
        }}
        """
        query_fragments.append(fragment)

    full_query = "query GetHistoricalPrices {\n" + "\n".join(query_fragments) + "\n}"
    return full_query




def get_derolas_data():
    """
    Derolas data is not as granular as the underlying.

    It is an aggregation of the underlying prices.
    based on a portfolio of 8 assets.

    """
    query = """query poolGetSnapshots(
       $chain: GqlChain
      $id: String!
      $range: GqlPoolSnapshotDataRange!
    ) {
      poolGetSnapshots(
        chain: $chain
        id: $id
        range: $range
      ) {
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
    }"""
    params = {
        "chain": "BASE",
        "id": "0xaf5b7999f491c42c05b5a2ca80f1d200d617cc8c",
        "range": "THIRTY_DAYS"
    }

    response = requests.post(GRAPHQL_ENDPOINT, json={"query": query, "variables": params})
    if response.status_code != 200:
        raise RuntimeError(f"Query failed with status code {response.status_code}: {response.text}")
    
    result = response.json()
    if "errors" in result:
        raise RuntimeError(f"Query failed with errors: {result['errors']}")
    data = result["data"]["poolGetSnapshots"]
    if not data:
        raise ValueError("No data returned from query")
    df = pd.DataFrame(data)
    # we need to make sure the timestamp includes hourly
    df["timestamp"] = pd.to_datetime(df["timestamp"], unit="s")
    df["sharePrice"] = pd.to_numeric(df["sharePrice"], errors="coerce")
    df["totalLiquidity"] = pd.to_numeric(df["totalLiquidity"], errors="coerce")
    df["totalShares"] = pd.to_numeric(df["totalShares"], errors="coerce")
    df["fees24h"] = pd.to_numeric(df["fees24h"], errors="coerce")
    df["totalSwapFee"] = pd.to_numeric(df["totalSwapFee"], errors="coerce")
    df["totalLiquidity"] = df["totalLiquidity"].astype(float)
    df["totalShares"] = df["totalShares"].astype(float)
    df["totalSwapFee"] = df["totalSwapFee"].astype(float)
    df["fees24h"] = df["fees24h"].astype(float)
    df["holdersCount"] = pd.to_numeric(df["holdersCount"], errors="coerce")
    df["swapsCount"] = pd.to_numeric(df["swapsCount"], errors="coerce")


    # we reset the index to be hourly
    df_time_series = df.set_index("timestamp").resample("H").mean()
    # we forward fill the missing values
    df_time_series = df_time_series.ffill()

    return df_time_series.reset_index()




def plot_price_matrix(price_matrix):
    plt.figure(figsize=(14, 8))
    
    for token in price_matrix.columns:
        plt.plot(price_matrix.index, price_matrix[token], label=token)
    
    plt.xlabel("Time")
    plt.ylabel("Price")
    plt.title("Token Prices Over Time")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    print("Fetching historical prices...")
    result = fetch_prices(GRAPHQL_ENDPOINT)
    print("Parsing historical prices...")
    df_prices = parse_historical_prices(result)
    print(df_prices)

    derola_data = get_derolas_data()
    print(derola_data)
    breakpoint()
    price_matrix = df_prices.pivot(index="timestamp", columns="symbol", values="price")

    print(price_matrix)

    print("Plotting price matrix...")


    # we check each colume to verify what the earliest timestamp is
    min_timestamps = {}
    for col in price_matrix.columns:
        min_timestamps[col] = price_matrix[col].first_valid_index()
    print(min_timestamps)
    # we take the earliest timestamp of all columns WHERE all prices are not null
    min_timestamps = {k: v for k, v in min_timestamps.items() if v is not None}
    min_timestamp = max(min_timestamps.values())
    print(f"Minimum timestamp: {min_timestamp}")
    breakpoint()

    # we filter the rows with a none 0 derolas price
    # we add in the share price of the Derolas pool
    derola_data = derola_data.set_index("timestamp")
    price_matrix["DEROLAS"] = derola_data["sharePrice"]
    # we backfill the derolas price
    # we drop the rows with a 0 derolas price
    breakpoint()

    

    # we filter the dataframe to only include rows after the earliest timestamp
    price_matrix = price_matrix[price_matrix.index >= min_timestamp]
    print(price_matrix)
    relative_prices = price_matrix / price_matrix.iloc[0]

    print("Plotting relative price matrix...")


    plot_price_matrix(relative_prices)
    print("Done.")
