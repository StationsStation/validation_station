use bollard::container::{
    Config, CreateContainerOptions, ListContainersOptions, LogsOptions, StartContainerOptions,
};
use bollard::models::HostConfig;

use bollard::Docker;
use chrono::Utc;
use futures::StreamExt;
use tokio::runtime::Runtime;
use rand::seq::SliceRandom;
use rand;
use bollard::models::CreateImageInfo;
use bollard::image::CreateImageOptions;
mod types;
use crate::types::{Agent, AgentStatus, UserConfiguration};

const IMAGE_NAME: &str = "8ball030/capitalisation_station:latest";

use std::path::PathBuf;
use std::fs;
use std::process;
use dirs::home_dir;
use bollard::auth::DockerCredentials;
use std::collections::HashMap;
use serde::Deserialize;

use base64::engine::general_purpose::STANDARD;
use base64::Engine as _;
const REGISTRY: &str = "https://index.docker.io/v1/"; // Adjust for private registries

/// Connect to Docker based on the current platform.
fn get_docker_client() -> Docker {
    #[cfg(target_os = "windows")]
    {
        Docker::connect_with_named_pipe_defaults().unwrap_or_else(|e| {
            eprintln!("❌ Failed to connect to Docker via named pipe: {}", e);
            process::exit(1);
        })
    }

    #[cfg(not(target_os = "windows"))]
    {
        Docker::connect_with_unix_defaults().unwrap_or_else(|e| {
            eprintln!("❌ Failed to connect to Docker via unix socket: {}", e);
            process::exit(1);
        })
    }
}

/// Get the path to Docker's config.json
fn get_docker_config_path() -> PathBuf {
    home_dir()
        .map(|home| home.join(".docker").join("config.json"))
        .unwrap_or_else(|| {
            eprintln!("❌ Could not determine the home directory.");
            process::exit(1);
        })
}

#[derive(Debug, Deserialize)]
struct DockerConfig {
    auths: HashMap<String, RegistryAuth>,
}

#[derive(Debug, Deserialize)]
struct RegistryAuth {
    auth: Option<String>,
}

/// Try to extract credentials for a specific registry from ~/.docker/config.json
fn get_credentials_for_registry(registry: &str) -> Option<DockerCredentials> {
    let path = get_docker_config_path();
    let contents = fs::read_to_string(path).ok()?;
    let config: DockerConfig = serde_json::from_str(&contents).ok()?;
    let entry = config.auths.get(registry)?;

    let auth_str = entry.auth.as_ref()?;
    let decoded = STANDARD.decode(auth_str).ok()?;
    let decoded_str = String::from_utf8(decoded).ok()?;
    let parts: Vec<&str> = decoded_str.splitn(2, ':').collect();

    if parts.len() != 2 {
        println!("❌ Invalid auth format in config.json");
        return None;
    }

    Some(DockerCredentials {
        username: Some(parts[0].to_string()),
        password: Some(parts[1].to_string()),
        serveraddress: Some(registry.to_string()),
        ..Default::default()
    })
}

/// Pull a Docker image, streaming output status.
pub async fn fetch_docker_image() -> Result<(), String> {
    let docker = get_docker_client();

    // Check if the image already exists
    let images = docker
        .list_images(None::<bollard::image::ListImagesOptions<String>>)
        .await
        .unwrap_or_default();
    if images.iter().any(|image| {
        image.repo_tags.iter().any(|tag| tag == IMAGE_NAME)
    }) {
        println!("✅ Image {} already exists", IMAGE_NAME);
        return Ok(());
    }
    
    // If not, we pull it
    println!("🛠️ Pulling image {}...", IMAGE_NAME);

    let pull_options = Some(CreateImageOptions {
        from_image: IMAGE_NAME,
        ..Default::default()
    });

    let credentials = get_credentials_for_registry(REGISTRY);

    let mut stream = docker.create_image(pull_options, None, credentials);

    println!("🚀 Pulling image: {}", IMAGE_NAME);

    while let Some(result) = stream.next().await {
        match result {
            Ok(CreateImageInfo { status: Some(status), .. }) => {
                println!("📦 {}", status);
            }
            Ok(_) => {}
            Err(e) => {
                eprintln!("❌ Error pulling image: {}", e);
                return Err(format!("Failed to pull image {}: {}", IMAGE_NAME, e));
            }
        }
    }

    println!("✅ Image {} pulled successfully", IMAGE_NAME);
    Ok(())
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

fn generate_agent_name() -> String {
    let adjectives = ["quick", "lazy", "sleepy", "happy", "sad", "angry", "funny", "serious", "curious", "brave", "smart", "silly", "shy", "bold", "calm", "wild", "friendly", "grumpy", "playful", "mischievous"];
    let names = ["cat", "dog", "fox", "bear", "lion", "tiger", "wolf", "eagle", "hawk", "shark", "whale", "dolphin", "octopus", "frog", "rabbit", "squirrel", "deer", "zebra", "giraffe", "elephant"];
    let words = ["agent", "bot", "unit", "module", "component", "device", "system", "entity", "object", "process", "task", "operation", "function", "service", "application", "program", "script", "daemon", "worker"];
    let mut rng = rand::thread_rng(); // Create a random number generator
    let word = words.choose(&mut rng).unwrap_or(&"agent");
    let adjective = adjectives.choose(&mut rng).unwrap_or(&"quick");
    let name = names.choose(&mut rng).unwrap_or(&"cat");
    format!("{}-{}-{}", word, adjective, name)
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
            if image.contains(IMAGE_NAME) {
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
        if let Err(e) = fetch_docker_image().await {
            eprintln!("❌ Error pulling image: {}", e);
            return Err(format!("Failed to pull image {}: {}", IMAGE_NAME, e));
        }
        let volume_bindings = vec![
            format!("{}:/app/ethereum_private_key.txt:ro", config.private_key_path),
            format!("{}:/app/.env:ro", config.environment_path),
        ];


        let container_config = Config {
            image: Some(IMAGE_NAME),
            host_config: Some(HostConfig {
                binds: Some(volume_bindings),
                ..Default::default()
            }),
            ..Default::default()
        };

        // We pull the image to ensure it's available

        let name = generate_agent_name();
        let create_options = CreateContainerOptions { name, platform: None };

        let container = docker
            .create_container(Some(create_options), container_config)
            .await
            .map_err(|e| format!("❌ Error creating container: {}", e))?;

        docker
            .start_container(&container.id, None::<StartContainerOptions<String>>)
            .await
            .map_err(|e| format!("❌ Error starting container: {}", e))?;

        println!("🚀 Container started with ID: {}", container.id);
        Ok(())
    })
}

#[tauri::command]
fn start_container_command(config: UserConfiguration) -> String {
    println!("🛠️ Starting container with config from user!");
    match start_docker_container(config) {
        Ok(_) => "✅ Container started successfully".to_string(),
        Err(e) => format!("❌ Failed to Start! Error: {}", e),
    }
}

#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
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
