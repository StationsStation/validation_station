use bollard::container::{
    Config, CreateContainerOptions, ListContainersOptions, LogsOptions, StartContainerOptions,
};
use bollard::models::HostConfig;
use bollard::Docker;
use chrono::Utc;
use futures::StreamExt;
use tokio::runtime::Runtime;

mod types;
use crate::types::{Agent, AgentStatus, UserConfiguration};

fn get_docker_client() -> Docker {
    Docker::connect_with_local_defaults().unwrap_or_else(|_| {
        eprintln!("Failed to connect to Docker");
        std::process::exit(1);
    })
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

async fn container_exists(id: &str) -> bool {
    let docker = get_docker_client();
    let containers = docker
        .list_containers(None::<ListContainersOptions<String>>)
        .await
        .unwrap_or_default();

    containers.iter().any(|c| c.id.as_deref() == Some(id))
}

async fn get_container_status() -> Vec<Agent> {
    let docker = get_docker_client();
    let containers = docker
        .list_containers(None::<ListContainersOptions<String>>)
        .await
        .unwrap_or_default();

    let mut result = vec![];

    for container in containers {
        if let Some(image) = &container.image {
            if image.contains("test") {
                let raw_status = container.status.clone().unwrap_or_default();
                result.push(Agent {
                    id: container.id.unwrap_or_default(),
                    status: parse_agent_status(&raw_status),
                    last_seen_timestamp: Utc::now().to_rfc3339(),
                    address: container
                        .names
                        .unwrap_or_default()
                        .get(0)
                        .unwrap_or(&"".to_string())
                        .to_string(),
                });
            }
        }
    }

    result
}

#[tauri::command]
fn greet(name: &str) -> String {
    format!("Hello, {}! You've been greeted from Rust!", name)
}

#[tauri::command]
fn get_container_status_command() -> Vec<Agent> {
    let rt = Runtime::new().expect("Failed to create Tokio runtime");
    rt.block_on(get_container_status())
}

#[tauri::command]
fn list_agents() -> Vec<Agent> {
    get_container_status_command()
}

#[tauri::command]
async fn stop_container_command(id: String) -> Result<String, String> {
    let docker = get_docker_client();

    if !container_exists(&id).await {
        return Err("Container not found.".into());
    }

    docker
        .stop_container(&id, None)
        .await
        .map(|_| format!("Stopped container: {}", id))
        .map_err(|e| format!("Failed to stop container {}: {}", id, e))
}

#[tauri::command]
async fn pause_container_command(id: String) -> Result<String, String> {
    let docker = get_docker_client();

    if !container_exists(&id).await {
        return Err("Container not found.".into());
    }

    docker
        .pause_container(&id)
        .await
        .map(|_| format!("Paused container: {}", id))
        .map_err(|e| format!("Failed to pause container {}: {}", id, e))
}

#[tauri::command]
async fn unpause_container_command(id: String) -> Result<String, String> {
    let docker = get_docker_client();

    if !container_exists(&id).await {
        return Err("Container not found.".into());
    }

    docker
        .unpause_container(&id)
        .await
        .map(|_| format!("Unpaused container: {}", id))
        .map_err(|e| format!("Failed to unpause container {}: {}", id, e))
}

#[tauri::command]
async fn get_container_logs(id: String) -> Result<String, String> {
    let docker = get_docker_client();

    let mut logs = docker.logs(
        &id,
        Some(LogsOptions::<String> {
            stdout: true,
            stderr: true,
            follow: false,
            ..Default::default()
        }),
    );

    let mut output = String::new();

    while let Some(log_result) = logs.next().await {
        match log_result {
            Ok(bollard::container::LogOutput::StdOut { message })
            | Ok(bollard::container::LogOutput::StdErr { message }) => {
                output.push_str(&String::from_utf8_lossy(&message));
            }
            Ok(_) => {}
            Err(e) => return Err(format!("Error streaming logs: {}", e)),
        }
    }

    Ok(output)
}

fn start_docker_container(config: UserConfiguration) -> Result<(), String> {
    let rt = Runtime::new().map_err(|e| format!("Failed to create Tokio runtime: {}", e))?;

    rt.block_on(async {
        let docker = get_docker_client();

        let volume_bindings = vec![
            format!("{}:/app/ethereum_private_key.txt:ro", config.private_key_path),
            format!("{}:/app/.env:ro", config.environment_path),
        ];

        let container_config = Config {
            image: Some("test"),
            host_config: Some(HostConfig {
                binds: Some(volume_bindings),
                ..Default::default()
            }),
            ..Default::default()
        };

        let create_options = CreateContainerOptions { name: "test-agent", platform: None };

        let container = docker
            .create_container(Some(create_options), container_config)
            .await
            .map_err(|e| format!("Error creating container: {}", e))?;

        docker
            .start_container(&container.id, None::<StartContainerOptions<String>>)
            .await
            .map_err(|e| format!("Error starting container: {}", e))?;

        println!("Started container {}", container.id);
        Ok(())
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
            list_agents,
            get_container_status_command
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
