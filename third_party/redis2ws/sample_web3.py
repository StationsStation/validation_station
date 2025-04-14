"""
Perform a simple test of the redis2ws module by running rpc_server.py and then running this script.
"""

import time
import web3

url = "http://159.223.245.14:80/public-rpc"

import rich
import rich_click as click

# We really focus on the beaitifcation of the output here.
def get_time():
    return round(time.time(), 4)

@click.command()
@click.option("--host", "-h", default="localhost", help="The host to connect to.")
@click.option("--port", "-p", default=8080, help="The port to connect to.")
@click.option("--track-stats", "-t", is_flag=True, help="Track stats of the connection.", default=False)
@click.option("--watch", "-w", is_flag=True, help="Watch the connection.", default=False)
def start(host: str, port: int, track_stats: bool, watch: bool):
    w3 = web3.Web3(web3.HTTPProvider(f"http://{host}:{port}/public-rpc"))

    results = []

    def get_stats():
        start_time = get_time()
        return {
            "block_number": w3.eth.block_number,
            "hash": w3.eth.get_block("latest")['hash'].hex(),
            "total_time": get_time() - start_time,
            "time": get_time()
        }
    
    while True:
        results.append(get_stats())

        print(f"Block number: {results[-1]['block_number']}")
        print(f"Hash: {results[-1]['hash']}")
        print(f"Total time: {results[-1]['total_time']}")
        print("")
        if not watch:
            break
        time.sleep(1)


        
    

if __name__ == "__main__":
    start()
