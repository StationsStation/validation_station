use actix::{Actor, ActorContext, Addr, AsyncContext, Handler, Message, StreamHandler};
use actix_web::{web, App, Error, HttpRequest, HttpResponse, HttpServer, Responder};
use actix_web_actors::ws;
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use env_logger::{Builder, Env};
use log::LevelFilter;
use std::sync::{Arc, Mutex};
use std::time::{Duration, Instant};
use tokio::sync::mpsc;
use tokio::time::timeout;
use uuid::Uuid;
use log::{debug, error, info, trace, warn};
use crate::constants::{MAX_REQUEST_TIMEOUT, PENALTY_LATE_MESSAGE, PENALTY_MISMATCHED_DATA, REWARDS_CONSENSUS};
use crate::shared::Config;
use crate::constants::{{MAX_SIZE, 
    MIN_ATTESTATIONS, 
    HEARTBEAT_TIMEOUT, 
    HEARTBEAT_INTERVAL, 
    MAX_BROADCAST_GROUP,
    PENALTY_MISSED_HEARTBEAT, 
    REWARDS_OPTIMISTIC}};


// RPC Request/Response structures
#[derive(Serialize, Deserialize, Clone, Debug)]
struct ProviderRequest {
    id: String,
    data: serde_json::Value,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
struct Heartbeat {
    id: Option<String>,
    timestamp: u64,
    block_number: u64,
    chain_id: u64,
    provider_addr: Option<String>
}

#[derive(Serialize, Deserialize, Clone, Debug)]
pub struct ProviderResponse {
    pub id: String,
    pub result: String,
    pub data: serde_json::Value,
    pub responder_addr: Option<String>,
    pub processing_time: Option<u64>,
    pub start_time: Option<u64>,
    pub end_time: Option<u64>,
    pub error: Option<String>,
    pub attestations: Vec<String>,

}

// Rpc requests are from the USERS VIA HTTP
#[derive(Serialize, Deserialize, Clone, Debug)]
struct RpcRequest {
    id: String,
    data: serde_json::Value,
}

#[derive(Serialize, Deserialize, Clone, Debug)]
// We just want rpc response to be a json object from serde_json::Value
struct RpcResponse {
    id: String,
    result: Option<serde_json::Value>,
    responder_addr: Option<String>,
    processing_time: Option<u64>,
    start_time: Option<u64>,
    end_time: Option<u64>,
    error: Option<String>,
    data: serde_json::Value,
}

// Internal messages for actor communication
#[derive(Message,Clone)]  // Added Clone derivation here
#[rtype(result = "()")]
struct Broadcast {
    request: RpcRequest,
    response_tx: mpsc::Sender<serde_json::Value>,
}

// WebSocket session actor
struct WebSocketSession {
    id: String,
    hb_time: Instant,
    broker: Arc<Mutex<RpcBroker>>,
    pub provider_addr: String,


}

// struct ProviderSnapShot {
//     score: u64,
//     chain_id: u64,
//     latest_block: u64,
//     outstanding_requests: u64,
//     latency: u64,
//     hb_time: Instant,
// }



impl Actor for WebSocketSession {
    type Context = ws::WebsocketContext<Self>;

    fn started(&mut self, ctx: &mut Self::Context) {
        // Register heartbeat
        self.hb(ctx);
        
        // Register session with broker
        info!("WebSocket session {} started", self.id);
        self.broker.lock().unwrap().register(self.id.clone(), ctx.address());
    }

    fn stopped(&mut self, _: &mut Self::Context) {
        // Unregister session from broker
        info!("WebSocket session {} stopped", self.id);
        self.broker.lock().unwrap().unregister(&self.id);
    }
}



impl WebSocketSession {
    // Heartbeat to detect disconnected clients
    fn hb(&self, ctx: &mut ws::WebsocketContext<Self>) {
        ctx.run_interval(Duration::from_secs(HEARTBEAT_INTERVAL), |act, ctx| {
            let elapsed = Instant::now().duration_since(act.hb_time);
            debug!("Heartbeat check for client {}: {:?} elapsed", act.id, elapsed,);
            // We send a heartbeat message to the client
            let msg = serde_json::to_string(&Heartbeat {
                id: Some(act.id.clone()),
                timestamp: Instant::now().elapsed().as_secs(),
                block_number: 0,
                chain_id: 0,
                provider_addr: Some(act.provider_addr.clone())
            }).unwrap();
            ctx.text(msg);
            if elapsed > Duration::from_secs(HEARTBEAT_TIMEOUT) {
                // Client timeout
                warn!("WebSocket client {} timed out after {:?} of inactivity", act.id, elapsed);
                // we reduce the score of the client
                let mut broker = act.broker.lock().unwrap();
                let new_score = broker.penalise_provider_score(act.id.clone(), PENALTY_MISSED_HEARTBEAT);
                debug!("new score for client {} is {}", act.id, new_score);
                ctx.stop();
                return;
            }
        });
    }


}

// Handler for WebSocket messages
impl StreamHandler<Result<ws::Message, ws::ProtocolError>> for WebSocketSession {
    fn handle(&mut self, msg: Result<ws::Message, ws::ProtocolError>, ctx: &mut Self::Context) {
        match msg {
            Ok(ws::Message::Ping(msg)) => {
                info!("Received Ping from client {}", self.id);
                self.hb_time = Instant::now();
                ctx.pong(&msg);
            }
            Ok(ws::Message::Pong(_)) => {
                trace!("Received Pong from client {}", self.id);
                self.hb_time = Instant::now();
            }
            Ok(ws::Message::Text(text)) => {
                self.hb_time = Instant::now();
                debug!("Received text message from client {}: {}", self.id, text);


                match serde_json::from_str::<Heartbeat>(&text) {
                    Ok(hb) => {
                        info!("Valid heartbeat received from client {}", self.id);
                        // we update the heartbeat time
                        self.hb_time = Instant::now();
                        // we update the provider address
                        let mut broker = self.broker.lock().unwrap();
                        broker.associate_session(hb.id.expect("No Id").clone(), hb.provider_addr.clone().unwrap());
                    },
                    Err(e) => {
                        debug!("Failed to parse text message from client {}: {}", self.id, e);
                        // We drop the data here and do nothing with it longer term we tarnish the provider.
                    }
                    
                }
        
                
                match serde_json::from_str::<ProviderResponse>(&text) {
                    Ok(response) => {
                        debug!("Valid provider response received from client {} for request {}", 
                             self.id, response.id);
                        
                        // Forward to broker if not already handled

                        let mut broker = self.broker.lock().unwrap();
                        // we get the optimistic responses from the broker
                        let pending_settlement = broker.pending_settlements.get(&response.id);
                        let session_id = self.id.clone();
                        if pending_settlement.is_some() {
                            debug!("Late response for request {} from client {} has already been settled", response.id, self.id);
                            // We drop the data here and do nothing with it longer term we tarnish the provider.
                            broker.penalise_provider_score(session_id, PENALTY_LATE_MESSAGE);
                            return;
                        }
                        let optimistic_response = broker.optimistic_responses.get(&response.id);

                        if optimistic_response.is_some() {
                            debug!("Optimistic response already received for request {} checking if data aligned?", response.id);
                            let optimistic_response = optimistic_response.clone().unwrap();
                            let mut op_data = optimistic_response.data.clone();
                            let mut late_response = response.data.clone();
                            // we drop the attestation from the late response
                            op_data["attestations"] = serde_json::Value::Null;
                            late_response["attestations"] = serde_json::Value::Null;
                            if op_data != late_response {
                                let reporter = optimistic_response.responder_addr.clone().unwrap();
                                debug!("Optimistic response for request {} from client {} is not aligned with the late response from client {}", response.id, self.id, reporter);
                                let new_score = broker.penalise_provider_score(self.provider_addr.clone(), PENALTY_MISMATCHED_DATA);
                                info!("new score for client {} is {}", self.id, new_score);
                                return;
                            } else {
                                let mut optimistic_response = optimistic_response.clone();
                                optimistic_response.attestations.push(response.id.clone());
                                let new_attestations = optimistic_response.attestations.clone();


                                if new_attestations.len() >= MIN_ATTESTATIONS {
                                    info!("Optimistic response fully attested for request {}", response.id);
                                    // we can now drop the optimistic response
                                    broker.optimistic_responses.remove(&response.id);
                                    broker.pending_settlements.insert(response.id.clone(), optimistic_response.clone());
                                    let new_score =  broker.reward_provider_score(self.provider_addr.clone(), REWARDS_CONSENSUS);
                                    info!("new score for client {} is {}", optimistic_response.responder_addr.clone().unwrap(), new_score)
                                }
                                broker.optimistic_responses.insert(response.id.clone(), optimistic_response);
                            }

                            return;
                        }
                        // get optimistic responses from broker
                        let raw_response: RpcResponse = RpcResponse {
                            id: response.id.clone(),
                            result: Some(serde_json::Value::String(response.result)),
                            error: None,
                            data: response.data,
                            responder_addr: response.responder_addr,
                            processing_time: response.processing_time,
                            start_time: response.start_time,
                            end_time: response.end_time,

                        };
                        
                        info!("Optimisitic response for request {} from client {}", response.id, self.id);
                        broker.reward_provider_score(session_id, REWARDS_OPTIMISTIC);
                        broker.handle_response(raw_response);
                    },
                    Err(e) => {
                        debug!("Failed to parse text message from client {}: {}", self.id, e);
                        // We drop the data here and do nothing with it longer term we tarnish the provider.
                    }
                }
            }
            Ok(ws::Message::Close(reason)) => {
                info!("WebSocket close request received from client {}: {:?}", self.id, reason);
                ctx.close(reason);
            }
            Ok(ws::Message::Binary(data)) => {
                warn!("Received binary message from client {}: {:?}", self.id, data);
                // we drop the data here and do nothing with it longer term we tarnish the provider.
            }
            Ok(msg) => {
                debug!("Received other message type from client {}: {:?}", self.id, msg);
            }
            Err(e) => {
                error!("WebSocket protocol error from client {}: {}", self.id, e);
                ctx.stop();
            }
        }
    }
}

// Handler for Broadcast messages
impl Handler<Broadcast> for WebSocketSession {
    type Result = ();

    fn handle(&mut self, msg: Broadcast, ctx: &mut Self::Context) {
        // Forward RPC request to client
        match serde_json::to_string(&msg.request) {
            Ok(request_json) => {
                debug!("Broadcasting request {} to client {}", msg.request.id, self.id);
                
                ctx.text(request_json);
            },
            Err(e) => {
                error!("Failed to serialize request {} for client {}: {}", 
                      msg.request.id, self.id, e);
            }
        }
    }
}

// Centralized RPC broker
struct RpcBroker {
    sessions: HashMap<String, Addr<WebSocketSession>>,
    pending_requests: HashMap<String, mpsc::Sender<serde_json::Value>>,
    optimistic_responses: HashMap<String, ProviderResponse>,
    pending_settlements: HashMap<String, ProviderResponse>,
    scores: HashMap<String, u64>,
    session_to_address: HashMap<String, String>,
}





impl RpcBroker {
    fn new() -> Self {
        info!("Initializing new RPC Broker");
        RpcBroker {
            sessions: HashMap::new(),
            pending_requests: HashMap::new(),
            optimistic_responses: HashMap::new(),
            pending_settlements: HashMap::new(),
            scores: HashMap::new(),
            session_to_address: HashMap::new(),
        }
    }

    fn register(&mut self, id: String, addr: Addr<WebSocketSession>) {
        // TODO perform validation of 
        info!("WebSocket client {} registered with broker", id);
        self.sessions.insert(id.clone(), addr);
        self.scores.insert(id.clone(), 0);
        info!("Current active sessions: {}", self.sessions.len());
    }

    fn unregister(&mut self, id: &str) {
        info!("WebSocket client {} unregistered from broker", id);
        self.sessions.remove(id);
        info!("Current active sessions: {}", self.sessions.len());
    }

    fn associate_session(&mut self, id: String, addr: String) {
        info!("WebSocket client {} associated with provider address {}", id, addr);
        self.session_to_address.insert(id, addr);
    }

    fn broadcast(&mut self, request: RpcRequest, response_tx: mpsc::Sender<serde_json::Value>) {
        // Store channel for response correlation
        self.pending_requests.insert(request.id.clone(), response_tx.clone());
        let session_count = self.sessions.len();

        debug!("Broadcasting request {} to {} connected clients", request.id, session_count);
        // Broadcast to all connected sessions
        let broadcast_msg = Broadcast {
            request: request.clone(),
            response_tx,
        };
        
        let mut broadcast_to = 0;
        for (id, provider_addr) in &self.sessions {
            debug!("Broadcasting request {} to client {}", request.id, id);
            if broadcast_to >= MAX_BROADCAST_GROUP {
                break;
            }
            provider_addr.do_send(broadcast_msg.clone());
            broadcast_to += 1;
        }
    }

    fn handle_response(&mut self, response: RpcResponse) {
        debug!("Handling response for request {}", response.id);
        
        let tx = self.pending_requests.get(&response.id);

        if let Some(tx) = tx {
            match tx.try_send(response.data.clone()) {
                Ok(_) => {
                    let optimistic_solver = response.responder_addr.clone().unwrap();

                    debug!("Optimistically sent response for request {} to client solver {}", response.id, optimistic_solver);
                    self.pending_requests.remove(&response.id);
                    self.optimistic_responses.insert(response.id.clone(), ProviderResponse {
                        id: response.id.clone(),
                        result: response.result.unwrap().to_string(),
                        data: response.data.clone(),
                        responder_addr: response.responder_addr,
                        processing_time: response.processing_time,
                        start_time: response.start_time,
                        end_time: response.end_time,
                        error: response.error,
                        attestations: [response.id.clone()].to_vec(),
                    });
                },
                Err(e) => {
                    error!("Failed to send response to client for request {}: {}", response.id, e);
                }
            }
        } else {
            debug!("No pending request found for response {} solver is late", response.id);
        }

        debug!("Pending requests remaining: {}", self.pending_requests.len());
    }

    
    fn penalise_provider_score(&mut self, session_id: String, penalty: u64) -> u64 {
        let mut new_score = 0;
        match self.scores.get(&session_id) {
            Some(score) => {
                if *score <= penalty {
                    new_score = 0;
                } else {
                    new_score = score - penalty;
                }
            },
            None => {
                error!("No score found for provider {}", session_id);
            }
        }
        self.scores.insert(session_id, new_score);
        return new_score
    }

    fn reward_provider_score(&mut self, session_id: String, reward: u64) -> u64 {
        let mut new_score = 0;
        match self.scores.get(&session_id) {
            Some(score) => {
                new_score = score + reward;
            },
            None => {
                error!("No score found for provider {}", session_id);
            }
        }
        self.scores.insert(session_id, new_score);
        return new_score
    }


    // fn select_provider(&mut self) -> String {
    //     let mut best_provider = String::new();
    //     let mut best_score = 0;
    //     for (provider, score) in &self.scores {
    //         if score >= &best_score {
    //             best_score = *score;
    //             best_provider = provider.clone();
    //         }
    //     }
    //     return best_provider;
    // }

}


// Application state
struct AppState {
    broker: Arc<Mutex<RpcBroker>>,
    // counter: Mutex<usize>,
}

// HTTP GET handler
async fn index() -> impl Responder {
    info!("Serving index page");
    HttpResponse::Ok().body("Welcome to the RPC broker server. Use /ws for WebSocket connections and /rpc for RPC requests.")
}

// WebSocket handshake handler
async fn ws_route(
    req: HttpRequest,
    stream: web::Payload,
    state: web::Data<Arc<AppState>>,
) -> Result<HttpResponse, Error> {
    // Generate unique client ID
    let client_id = Uuid::new_v4().to_string();
    info!("New WebSocket client connecting: {}", client_id);
    
    // Log connection details
    let connection_info = req.connection_info();
    info!("Connection from {}:{} for client {}", 
           connection_info.realip_remote_addr().unwrap_or("unknown"),
           connection_info.scheme(),
           client_id);
    
    // Create WebSocket session
    let ws_session = WebSocketSession {
        id: client_id.clone(),
        hb_time: Instant::now(),
        broker: state.broker.clone(),
        provider_addr: connection_info.realip_remote_addr().unwrap_or("unknown").to_string(),
    };

    // Initiate WebSocket connection
    // limit size of messages to 5mb
    
    ws::start(ws_session, &req, stream)
        
}

// RPC handler
async fn public_rpc(
    body: String,
    state: web::Data<Arc<AppState>>,
) -> impl Responder {
    debug!("Received User request: {}", body);
    
    // Parse request body
    let rpc_req = match serde_json::from_str::<serde_json::Value>(&body) {
        Ok(req) => {
            debug!("Successfully parsed RPC request");
            req
        },
        Err(e) => {
            error!("Invalid JSON in RPC request: {}", e);
            return HttpResponse::BadRequest().body(format!("Invalid JSON: {}", e));
        }
    };
    
    // Create RPC request with UUID
    let request_id = Uuid::new_v4().to_string();
    let request = RpcRequest {
        id: request_id.clone(),
        data: rpc_req.clone(),
    };
    
    debug!("Created RPC request with ID: {}", request_id);
    
    // Create response channel
    let (tx, mut rx) = mpsc::channel::<serde_json::Value>(1);
    
    // Broadcast to all clients
    {
        let mut broker = state.broker.lock().unwrap();
        if broker.sessions.is_empty() {
            warn!("No WebSocket clients connected to handle RPC request");
            return HttpResponse::ServiceUnavailable().body("No WebSocket clients connected");
        }
        broker.broadcast(request, tx);
    }
    
    // Wait for first response with timeout
    info!("Waiting for response to request {}", request_id);
    match timeout(Duration::from_secs(MAX_REQUEST_TIMEOUT), rx.recv()).await {
        Ok(Some(response)) => {
            debug!("Response received for request {}", request_id);
            debug!("Response data: {}", response);
            HttpResponse::Ok().json(response)
        }
        Ok(None) => {
            error!("Response channel closed unexpectedly for request {}", request_id);
            HttpResponse::InternalServerError().body("Response channel closed unexpectedly")
        }
        Err(_) => {
            error!("Timeout waiting for response to request {}", request_id);
            HttpResponse::RequestTimeout().body("No response received within timeout period")
        }
    }
}

async fn scores(
    state: web::Data<Arc<AppState>>,
) -> impl Responder {
    let broker = state.broker.lock().unwrap();
    // We sort the scores by value
    let scores = broker.scores.clone()
        .into_iter()
        .collect::<Vec<_>>();
    let mut sorted_scores = Vec::new();

    let provider_addresses = broker.session_to_address.clone();


    provider_addresses.iter().for_each(|(k, v)| {
        info!("Provider {} has address {}", k, v);
    });
    for (session_id, score) in &scores {

        let provider_session = provider_addresses
            .get(session_id);
        // we check if there is a null value
        info!("Provider session for {} is {:?}", session_id, provider_session);
        if provider_session.is_none() {
            continue;
        }

        let provider_addr = provider_session.clone();
        info!("Provider {} has score {}", provider_addr.clone().unwrap(), score);
        sorted_scores.push((provider_addr.unwrap().clone(), *score));
    }
    sorted_scores.sort_by(|a, b| b.1.cmp(&a.1));
    HttpResponse::Ok().json(sorted_scores)
}

// Subsequent logging operations will propagate with guaranteed visibility...
// Private endpoint
// we check the id of the request and we send the response to the client


pub async fn start_service(config: Config) -> std::io::Result<()> {
    info!("Initializing RPC broker service");
    let mut builder = Builder::from_env(Env::default());
    builder.filter_level(LevelFilter::Info);

    builder.init();
    // Initialize application state
    let broker = Arc::new(Mutex::new(RpcBroker::new()));
    let app_state = Arc::new(AppState {
        broker: broker.clone(),
        // counter: Mutex::new(0),
    });

    info!("Starting server at http://{}:{}", config.host, config.port);
    info!("WebSocket endpoint available at ws://{}:{}/ws", config.host, config.port);

    // Create and run HTTP server
    HttpServer::new(move || {
        App::new()
            .app_data(web::Data::new(app_state.clone()))
            .app_data(web::JsonConfig::default().limit(MAX_SIZE))
            .route("/", web::get().to(index))
            .route("/public-rpc", web::post().to(public_rpc))
            .route("/ws", web::get().to(ws_route))
            .route("/scores", web::get().to(scores))
    })
    .bind(format!("{}:{}", config.host, config.port))?
    .run()
    .await
}