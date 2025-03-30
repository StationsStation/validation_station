// File: src/provider/mod.rs
use crate::shared::Config;
use actix_web::{get, App, HttpResponse, HttpServer, Responder};

#[get("/health")]
async fn health_check() -> impl Responder {
    HttpResponse::Ok().json(serde_json::json!({
        "status": "operational",
        "service": "provider"
    }))
}

pub async fn start_service(config: Config) -> anyhow::Result<()> {
    // Construct binding address
    let bind_address = format!("{}:{}", config.host, config.port);
    
    // Initialize and start server
    HttpServer::new(|| {
        App::new()
            .service(health_check)
    })
    .bind(bind_address)?
    .run()
    .await?;
    
    Ok(())
}