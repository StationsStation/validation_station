from pydantic_core import from_json
import rich_click as click
import asyncio
import json
import time
import traceback
import uuid
import websockets
import httpx
from dataclasses import asdict, dataclass
from typing import Dict, List, Optional, Union, Any
import logging
from rich.logging import RichHandler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[RichHandler(
        rich_tracebacks=True,
    )]
)
logger = logging.getLogger("async_websocket_client")

@dataclass
class HeartBeat():
    id: str
    timestamp: float = time.time()
    block_number: int = 0
    chain_id: int = 0
    provider_addr: str = "0x"

@dataclass
class ProviderRequest:
    id: str
    data: Dict[str, Any]
    timestamp: float = time.time()

class AsyncRequestProcessor:
    def __init__(self, proxy_url: str, max_concurrent: int = 50, timeout: float = 30.0):
        self.proxy_url = proxy_url
        self.max_concurrent = max_concurrent
        self.timeout = timeout
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.active_requests: Dict[str, asyncio.Task] = {}
        self.client = httpx.AsyncClient(timeout=timeout)
    
    async def close(self):
        """Properly close the HTTP client and cancel any pending tasks."""
        await self.client.aclose()
        for task_id, task in list(self.active_requests.items()):
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    logger.debug(f"Task {task_id} cancelled")
                except Exception as e:
                    logger.error(f"Error closing task {task_id}: {e}")
    
    async def process_request(self, websocket, request_data: str, heartbeat: HeartBeat
                              ) -> None:
        """Process a single request and send the response back."""
        try:
            req = from_json(request_data)
            req_id = req.get('id')
            req_data = req.get('data')
            
            # Generate a unique task ID
            task_id = f"{req_id}_{uuid.uuid4()}"
            
            async with self.semaphore:
                start_time = time.time()
                logger.debug(f"Processing request {req_id}")
                
                try:
                    # Use async HTTP client for better performance
                    response = await self.client.post(
                        self.proxy_url,
                        json=req_data,
                        headers={"Content-Type": "application/json"}
                    )
                    
                    response.raise_for_status()
                    data = response.json()
                    
                    result = {
                        "id": req_id,
                        "data": data,
                        "result": "success" if response.status_code == 200 else "error",
                        "processing_time": int(time.time() - start_time),
                        "start_time": int(start_time),
                        "end_time": int(time.time()),
                        "responder_addr": heartbeat.provider_addr,
                        "attestations": [self.proxy_url]
                    }
                    # We sign the response here with the responder's address


                    if response.status_code != 200:
                        logger.error(f"Request {req_id} failed with status code {response.status_code}")

                    data = response.json()
                    if 'error' in data:
                        logger.error(f"Request {req_id} failed with error: {data['error']}")
                        return await self._send_error_response(websocket, req_id, data['error'])
                    
                    # Send response back through websocket
                    await websocket.send(json.dumps(result))

                    logger.info(f"Request {req_id} completed in {time.time() - start_time:.3f}s")
                    
                except httpx.HTTPStatusError as e:
                    error_msg = f"HTTP error {e.response.status_code}: {e.response.text}"
                    logger.error(error_msg)
                    await self._send_error_response(websocket, req_id, error_msg)
                    
                except httpx.RequestError as e:
                    error_msg = f"Request error: {str(e)}"
                    logger.error(error_msg)
                    await self._send_error_response(websocket, req_id, error_msg)
                    
                except Exception as e:
                    error_msg = f"Unexpected error: {str(e)}"
                    logger.error(f"{error_msg}" + self.proxy_url)
                    await self._send_error_response(websocket, req_id, error_msg)
                    
                finally:
                    # Clean up task from tracking
                    if task_id in self.active_requests:
                        del self.active_requests[task_id]
        
        except Exception as e:
            logger.error(f"Error parsing request: {str(e)}\n{traceback.format_exc()}")
    
    async def _send_error_response(self, websocket, req_id: str, error_message: str) -> None:
        """Send an error response back to the client."""
        return await asyncio.sleep(0)
        try:
            result = {
                "id": req_id,
                "error": error_message,
                "result": "error"
            }
            await websocket.send(json.dumps(result))
        except Exception as e:
            logger.error(f"Failed to send error response: {str(e)}")



async def main(proxy_url: str, host: str = "127.0.0.1", port: int = 8080, path: str = "/ws"):
    """Main function to run the WebSocket client."""
    uri = f"ws://{host}:{port}{path}"
    processor = AsyncRequestProcessor(proxy_url=proxy_url)


    current_block = 0
    chain_id = 0
    address = "0x" + uuid.uuid4().hex


    heartbeat = HeartBeat(id="heartbeat", block_number=current_block, chain_id=chain_id, provider_addr=address)
    
    try:
        logger.info(f"Connecting to {uri}")

        # we overwrite the standard ping method to send a message to the server
        # to keep the connection alive
        # we use this to connect to the rpc server

        async with websockets.connect(uri) as websocket:
            logger.info(f"Connected to {uri}, waiting for requests")
            async def get_block_number(*args, **kwargs):
                block_number = await processor.client.post(
                    proxy_url,
                    json={"jsonrpc": "2.0", "method": "eth_blockNumber", "params": [], "id": 1},
                    headers={"Content-Type": "application/json"}
                )
                heartbeat.block_number = block_number.json()['result']
                heartbeat.block_number = int(heartbeat.block_number, 16)
                heartbeat.timestamp = time.time()
                logger.info(f"Block number: {heartbeat.block_number}")
                return heartbeat.block_number
            
            async def on_broker_ping(*args, **kwargs):
                print("Received ping from broker")
                await get_block_number(*args, **kwargs)
                heartbeat_data = asdict(heartbeat)
                print("Sending heartbeat to registration server" + str(heartbeat) + " " + str(args) + " " + str(kwargs))
                return websocket.send(json.dumps(heartbeat_data))
            

            async def periodic_broker_ping(websocket, processor, heartbeat, interval: float = 10.0):
                while True:
                    try:
                        heartbeat_data = asdict(heartbeat)
                        logger.info(f"Sending heartbeat: {heartbeat_data}")
                        await websocket.send(json.dumps(heartbeat_data))
                        await asyncio.sleep(interval)
                        logger.info("Sent heartbeat")
                    except asyncio.CancelledError:
                        break
                    except Exception as e:
                        logger.error(f"Error in periodic ping task: {str(e)}")
                        await periodic_broker_ping(websocket, processor, heartbeat, interval)


            websocket.ping = on_broker_ping
            # Create a task to periodically clean up completed tasks
            cleanup_task = asyncio.create_task(periodic_cleanup(processor))
            ping_broker = asyncio.create_task(periodic_broker_ping(websocket, processor, heartbeat))
            try:
                # Process incoming messages asynchronously
                async for message in websocket:
                    # Create a new task for each incoming request
                    print("Received message from broker")
                    task = asyncio.create_task(processor.process_request(websocket, message, heartbeat))
                    task_id = f"task_{uuid.uuid4()}"
                    processor.active_requests[task_id] = task
            except websockets.exceptions.ConnectionClosed as e:
                logger.warning(f"WebSocket connection closed: {e}")
            finally:
                cleanup_task.cancel()
                ping_broker.cancel()
                try:
                    await cleanup_task
                    await ping_broker
                except asyncio.CancelledError:
                    pass
    except Exception as e:
        logger.error(f"Connection error: {str(e)}\n{traceback.format_exc()}")
    finally:
        # Ensure proper cleanup
        await processor.close()
        logger.info("Client shutdown complete")

async def periodic_cleanup(processor: AsyncRequestProcessor, interval: float = 10.0):
    """Periodically clean up completed tasks to prevent memory leaks."""
    while True:
        try:
            await asyncio.sleep(interval)
            # Remove completed tasks from the active_requests dictionary
            completed_tasks = [task_id for task_id, task in processor.active_requests.items() if task.done()]
            for task_id in completed_tasks:
                try:
                    # Check for exceptions
                    processor.active_requests[task_id].result()
                except Exception as e:
                    logger.error(f"Task {task_id} failed with error: {str(e)}")
                finally:
                    del processor.active_requests[task_id]
            
            if completed_tasks:
                logger.debug(f"Cleaned up {len(completed_tasks)} completed tasks")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in cleanup task: {str(e)}")

@click.command()
@click.option("--proxy_url", default="https://1rpc.io/eth", help="URL of the proxy server")
@click.option("--host", default="127.0.0.1", help="WebSocket server host")
@click.option("--port", default=8080, type=int, help="WebSocket server port")
@click.option("--path", default="/ws", help="WebSocket endpoint path")
@click.option("--log-level", default="INFO", 
              type=click.Choice(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False),
              help="Set the logging level")
def cli(proxy_url: str, host: str, port: int, path: str, log_level: str):
    """WebSocket client for handling asynchronous blockchain RPC requests."""
    # Set the log level
    logging.getLogger().setLevel(getattr(logging, log_level.upper()))
    
    # Run the main async function
    try:
        asyncio.run(main(proxy_url, host, port, path))
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
    except Exception as e:
        logger.critical(f"Fatal error: {str(e)}\n{traceback.format_exc()}")
        return 1
    return 0

if __name__ == "__main__":
    cli()