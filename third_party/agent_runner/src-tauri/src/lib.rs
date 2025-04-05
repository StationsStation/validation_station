
mod types;
use shiplift::{Docker, LogsOptions, ContainerOptions};
use futures::stream::StreamExt; // not futures_util
use std::str;
use tauri_plugin_dialog;

use tokio::runtime::Runtime;
use crate::types::AgentStatus;
use crate::types::Agent;
use crate::types::UserConfiguration;
// Learn more about Tauri commands at https://tauri.app/develop/calling-rust/
#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

fn parse_agent_status(raw: &str) -> AgentStatus {
    let lower = raw.to_lowercase();

    if lower.contains("up") && lower.contains("paused") {
        AgentStatus::Paused
    } else if lower.contains("up") {
        AgentStatus::Running
    } else if lower.contains("created") {
        AgentStatus::Started
    } else if lower.contains("exited") {
        AgentStatus::Exited
    } else if lower.contains("removing") || lower.contains("dead") {
        AgentStatus::Stopping
    } else {
        AgentStatus::Stopped
    }
}


async fn get_container_status() -> Vec<Agent> {
    let docker = Docker::new();
    let containers = docker.containers();

    let mut result = vec![];

    match containers.list(&Default::default()).await {
        Ok(list) => {
            for container in list {
                if container.image.contains("test") {
                    let raw_status = container.status.clone();
                    println!("Container ID: {}", container.id);
                    println!("Container Status: {}", raw_status);
                    result.push(Agent {
                        id: container.id,
                        status: parse_agent_status(raw_status.as_str()),
                        last_seen_timestamp: chrono::Utc::now().to_rfc3339(),
                        address: container.names.get(0).unwrap_or(&"".to_string()).to_string(),
                    });
                }
            }
        }
        Err(e) => {
            eprintln!("Error listing containers: {}", e);
        }
    }

    result
}


// We have a function for configuring the Docker container
// and starting it. This function can be called from the Tauri command.
// This is the command that will be called from the frontend
// to start the Docker container.
// You can also refactor this to return a result or an error
// if you want to handle errors in the frontend.


#[tauri::command]
fn get_container_status_command() -> Vec<Agent> {
    let rt = Runtime::new().expect("Failed to create Tokio runtime");
    rt.block_on(get_container_status())
}

#[tauri::command]
fn list_agents() -> Vec<Agent> {
    let rt = Runtime::new().expect("Failed to create Tokio runtime");
    rt.block_on(get_container_status())
}


#[tauri::command]
async fn stop_container_command(id: String) -> Result<String, String> {
    println!("Stopping container with ID: {}", id);

    let docker = Docker::new();
    let container = docker.containers().get(&id);

    container
        .stop(None)
        .await
        .map(|_| format!("Stopped container: {}", id))
        .map_err(|e| format!("Failed to stop container {}: {}", id, e))
}

#[tauri::command]
async fn pause_container_command(id: String) -> Result<String, String> {
    let docker = Docker::new();
    let container = docker.containers().get(&id);

    container
        .pause()
        .await
        .map(|_| format!("Paused container: {}", id))
        .map_err(|e| format!("Failed to pause container {}: {}", id, e))
}

#[tauri::command]
async fn unpause_container_command(id: String) -> Result<String, String> {
    let docker = Docker::new();
    let container = docker.containers().get(&id);

    container
        .unpause()
        .await
        .map(|_| format!("Unpaused container: {}", id))
        .map_err(|e| format!("Failed to unpause container {}: {}", id, e))
}


#[tauri::command]
async fn get_container_logs(id: String) -> Result<String, String> {
    let docker = Docker::new();

    let mut logs = docker
        .containers()
        .get(&id)
        .logs(&LogsOptions::builder()
            .stdout(true)
            .stderr(true)
            .follow(false) // you can toggle this for live logs
            .build());

    let mut output = String::new();

    while let Some(result) = logs.next().await {
        match result {
            Ok(bytes) => {
                output.push_str(&String::from_utf8_lossy(&bytes));
            }
            Err(e) => {
                return Err(format!("Error streaming logs: {}", e));
            }
        }
    }

    Ok(output)
}


// #[tauri::command]
// fn start_container_command(config: UserConfiguration) -> String {
//     match start_docker_container(config) {
//         Ok(_) => "Container start triggered!".into(),
//         Err(e) => format!("Failed to start container: {}", e),
//     }
// }
// #[tauri::command]
// fn start_container_command() -> String {
//     start_docker_container(); // You can refactor this to return a result
//     "Container start triggered!".into()
// }

// fn start_docker_container() {
//     // Create a new Tokio runtime for async execution
//     let rt = Runtime::new().expect("Failed to create Tokio runtime");

//     rt.block_on(async {
//         let docker = Docker::new();

//         let options = ContainerOptions::builder("test")
//             .build();

//         match docker.containers().create(&options).await {
//             Ok(info) => {
//                 let id = info.id;
//                 println!("Created container with ID: {}", id);

//                 match docker.containers().get(&id).start().await {
//                     Ok(_) => println!("Container started successfully."),
//                     Err(e) => eprintln!("Error starting container: {}", e),
//                 }
//             }
//             Err(e) => eprintln!("Error creating container: {}", e),
//         }
//     });
// }


fn start_docker_container(config: UserConfiguration) -> Result<(), String> {
    // Create a new Tokio runtime for async execution
    let rt = Runtime::new().map_err(|e| format!("Failed to create Tokio runtime: {}", e))?;

    rt.block_on(async {
        let docker = Docker::new();

        // Use the UserConfiguration fields (e.g., private_key_path, environment_path)
        println!(
            "Using private key path: {} and environment path: {}",
            config.private_key_path, config.environment_path
        );

        let volume_bindings = vec![
            format!("{}:/app/ethereum_private_key.txt:ro", config.private_key_path),
            format!("{}:/app/.env:ro", config.environment_path),
        ];

        let options = ContainerOptions::builder("test")
            .volumes(volume_bindings.iter().map(|s| s.as_str()).collect::<Vec<&str>>())
            .build();

        match docker.containers().create(&options).await {
            Ok(info) => {
                let id = info.id;
                println!("Created container with ID: {}", id);

                match docker.containers().get(&id).start().await {
                    Ok(_) => {
                        println!("Container started successfully.");
                        Ok(())
                    }
                    Err(e) => Err(format!("Error starting container: {}", e)),
                }
            }
            Err(e) => Err(format!("Error creating container: {}", e)),
        }
    })
}

#[tauri::command]
fn start_container_command(config: UserConfiguration) -> String {
    println!("Starting Docker container with config: {:?}", config);
    match start_docker_container(config) {
        Ok(_) => "Container start triggered!".into(),
        Err(e) => format!("Failed to start container: {}", e),
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            greet,
            start_container_command,
            stop_container_command,
            pause_container_command,
            unpause_container_command,
            get_container_logs,
            list_agents
            ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
