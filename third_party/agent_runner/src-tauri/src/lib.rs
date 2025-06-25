mod types;
use bollard::container::{
    Config, CreateContainerOptions, ListContainersOptions, LogsOptions, StartContainerOptions,
};

use bollard::container::RemoveContainerOptions;

use bollard::image::CreateImageOptions;
use bollard::models::ContainerSummary;
use bollard::models::CreateImageInfo;
use bollard::models::HostConfig;
use bollard::Docker;
use chrono::Utc;
use std::time::Duration;
use tokio::time::sleep;
use futures::StreamExt;
use rand;
use rand::prelude::IndexedRandom;
use tauri::path::BaseDirectory::AppData;
use tauri::AppHandle;
use tauri::Manager;
use tokio::runtime::Runtime;

use bollard::auth::DockerCredentials;
use dirs::home_dir;
use serde::Deserialize;
use std::collections::HashMap;
use std::fs;
use std::path::PathBuf;
use std::process;

use base64::engine::general_purpose::STANDARD;
use base64::Engine as _;

use openapi::models::StateResponse;

use crate::types::{Agent, AgentStatus, UserConfiguration};
const IMAGE_NAME: &str = "8ball030/capitalisation_station:latest";
const REGISTRY: &str = "https://index.docker.io/v1/"; // Adjust for private registries

pub async fn get_docker_client() -> Result<Docker, String> {
    // Initialize the Docker client based on platform
    let client = {
        #[cfg(target_os = "windows")]
        {
            Docker::connect_with_named_pipe_defaults()
        }

        #[cfg(not(target_os = "windows"))]
        {
            Docker::connect_with_unix_defaults()
        }
    };

    let client = match client {
        Ok(c) => c,
        Err(e) => return Err(format!("❌ Failed to connect to Docker: {}", e)),
    };

    // Ping the Docker daemon to confirm it's alive
    if let Err(e) = client.ping().await {
        return Err(format!("❌ Docker ping failed: {}", e));
    }

    Ok(client)
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
    let docker = get_docker_client().await;

    // Check if the image already exists
    let images = docker.clone()?
        .list_images(None::<bollard::image::ListImagesOptions<String>>)
        .await
        .unwrap_or_default();
    if images
        .iter()
        .any(|image| image.repo_tags.iter().any(|tag| tag == IMAGE_NAME))
    {
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

    let mut stream = docker?.create_image(pull_options, None, credentials);

    println!("🚀 Pulling image: {}", IMAGE_NAME);

    while let Some(result) = stream.next().await {
        match result {
            Ok(CreateImageInfo {
                status: Some(status),
                ..
            }) => {
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
    let adjectives = [
        "quick",
        "lazy",
        "sleepy",
        "happy",
        "sad",
        "angry",
        "funny",
        "serious",
        "curious",
        "brave",
        "smart",
        "silly",
        "shy",
        "bold",
        "calm",
        "wild",
        "friendly",
        "grumpy",
        "playful",
        "mischievous",
    ];
    let names = [
        "cat", "dog", "fox", "bear", "lion", "tiger", "wolf", "eagle", "hawk", "shark", "whale",
        "dolphin", "octopus", "frog", "rabbit", "squirrel", "deer", "zebra", "giraffe", "elephant",
    ];
    let words = [
        "agent",
        "bot",
        "unit",
        "module",
        "component",
        "device",
        "system",
        "entity",
        "object",
        "process",
        "task",
        "operation",
        "function",
        "service",
        "application",
        "program",
        "script",
        "daemon",
        "worker",
    ];
    let mut rng = rand::rng(); // Create a random number generator
    let word = words.choose(&mut rng).unwrap_or(&"agent");
    let adjective = adjectives.choose(&mut rng).unwrap_or(&"quick");
    let name = names.choose(&mut rng).unwrap_or(&"cat");
    format!("{}-{}-{}", word, adjective, name)
}

async fn get_container_status() -> Vec<Agent> {
    let docker = get_docker_client().await;

    let container_options: ListContainersOptions<String> = ListContainersOptions {
        all: true,
        ..Default::default()
    };

    let containers: Vec<ContainerSummary> = docker.expect("Failed to connect to Docker")
        .list_containers(Some(container_options))
        .await
        .expect("Failed to list containers");

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

async fn container_exists(id: &str) -> bool {
    let docker = get_docker_client().await;

    let container_options: ListContainersOptions<String> = ListContainersOptions {
        all: true,
        ..Default::default()
    };
    let containers = docker.expect("Failed to connect to Docker")
        .list_containers(Some(container_options))
        .await
        .unwrap_or_default();

    containers.iter().any(|c| c.id.as_deref() == Some(id))
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
    let docker = get_docker_client().await;

    if !container_exists(&id).await {
        return Err("Container not found.".into());
    }

    docker?
        .stop_container(&id, None)
        .await
        .map(|_| format!("Stopped container: {}", id))
        .map_err(|e| format!("Failed to stop container {}: {}", id, e))
}

#[tauri::command]
async fn pause_container_command(id: String) -> Result<String, String> {
    let docker = get_docker_client().await;

    if !container_exists(&id).await {
        return Err("Container not found.".into());
    }

    docker?
        .pause_container(&id)
        .await
        .map(|_| format!("Paused container: {}", id))
        .map_err(|e| format!("Failed to pause container {}: {}", id, e))
}

#[tauri::command]
async fn unpause_container_command(id: String) -> Result<String, String> {
    let docker = get_docker_client().await;

    if !container_exists(&id).await {
        return Err("Container not found.".into());
    }

    docker?
        .unpause_container(&id)
        .await
        .map(|_| format!("Unpaused container: {}", id))
        .map_err(|e| format!("Failed to unpause container {}: {}", id, e))
}

#[tauri::command]
async fn delete_container_command(id: &str) -> Result<(), String> {
    let docker = get_docker_client().await;

    if !container_exists(id).await {
        return Err("Container not found.".into());
    }

    docker?
        .remove_container(
            id,
            Some(RemoveContainerOptions {
                force: true,
                ..Default::default()
            }),
        )
        .await
        .map(|_| ())
        .map_err(|e| format!("Failed to remove container {}: {}", id, e))
}

use futures::TryStreamExt;

#[tauri::command]
async fn get_container_logs(id: String) -> Result<String, String> {
    let docker = get_docker_client().await;

    let container_status = docker.clone()?
        .inspect_container(&id, None)
        .await
        .map_err(|e| format!("Error inspecting container: {}", e))?;
    if container_status.state.unwrap().running.unwrap() {
        let mut logs = docker?.logs(
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
    } else {
        println!("Container is not running.");
        let mut logs = docker?
            .logs(
                &id,
                Some(LogsOptions::<String> {
                    stdout: true,
                    stderr: true,
                    tail: String::from("all"),
                    ..Default::default()
                }),
            )
            .map_err(|e| format!("Error retrieving logs: {}", e));
        let mut output = String::new();
        // the logs are a single dump
        while let Some(log_result) = logs
            .try_next()
            .await
            .map_err(|e| format!("Error reading log stream: {}", e))?
        {
            use bollard::container::LogOutput::*;
            let chunk = match log_result {
                StdOut { message } | StdErr { message } | Console { message } => {
                    String::from_utf8_lossy(&message).to_string()
                }
                _ => continue,
            };
            output.push_str(&chunk);
        }
        Ok(output)
    }
}

fn start_docker_container(config: UserConfiguration) -> Result<String, String> {
    let rt = Runtime::new().map_err(|e| format!("Failed to create Tokio runtime: {}", e))?;

    rt.block_on(async {
        let docker = get_docker_client().await;
        if let Err(e) = fetch_docker_image().await {
            eprintln!("❌ Error pulling image: {}", e);
            return Err(format!("Failed to pull image {}: {}", IMAGE_NAME, e));
        }
        let volume_bindings = vec![format!(
            "{}:/app/ethereum_private_key.txt:ro",
            config.private_key_path
        )];
        let env_strings: Vec<String> = config
            .environment_vars
            .into_iter()
            .map(|(k, v)| format!("{}={}", k, v))
            .collect();

        let env_refs: Vec<&str> = env_strings.iter().map(|s| s.as_str()).collect();

        let container_config = Config {
            image: Some(IMAGE_NAME),
            host_config: Some(HostConfig {
                binds: Some(volume_bindings),
                ..Default::default()
            }),
            env: Some(env_refs),
            ..Default::default()
        };

        // We pull the image to ensure it's available

        let name = generate_agent_name();
        let create_options = CreateContainerOptions {
            name,
            platform: None,
        };

        let container = docker.clone()?
            .create_container(Some(create_options), container_config)
            .await
            .map_err(|e| format!("❌ Error creating container: {}", e))?;

        docker?
            .start_container(&container.id, None::<StartContainerOptions<String>>)
            .await
            .map_err(|e| format!("❌ Error starting container: {}", e))?;

        println!("🚀 Container started with ID: {}", container.id);
        Ok(container.id)
    })
}

#[tauri::command]
fn start_container_command(config: UserConfiguration) -> String {
    println!("🛠️ Starting container with config from user!");
    match start_docker_container(config) {
        Ok(id) => {
            println!("✅ Container started with ID: {}", id);
            format!("{}", id)
        }
        Err(e) => format!("❌ Failed to Start! Error: {}", e),
    }
}

// get the agent status
#[tauri::command]
async fn get_agent_state(id: String) -> StateResponse {
    // we make a request to the port 8889 of the container
    // We use the bollard client to temporarily forward the port
    // and then we make a request to the container
    let docker = get_docker_client().await;
    let container_info = docker.expect("DOCKER IS NOT CONNECTED").inspect_container(&id, None).await.unwrap();
    let ip = container_info.network_settings.unwrap().ip_address.unwrap();
    let url = format!("http://{}:8889/state", ip);
    let client = reqwest::Client::new();

    // we print
    println!("🛠️ Making request to: {}", url);

    let response = client
        .get(&url)
        .send()
        .await
        .expect("Failed to send request");
    // println!("🛠️ Response: {:?}", response.ser
    // we print the raw data
    let raw_data = response.text().await.unwrap();
    // println!("🛠️ Raw data: {:?}", raw_data);
    // we parse the data
    let parsed_data: StateResponse = serde_json::from_str(&raw_data).unwrap();
    // we print the parsed data
    // println!("🛠️ Parsed data: {:?}", parsed_data);
    // and finally, we return the parsed data
    parsed_data
}

fn get_app_data_dir(app: AppHandle) -> PathBuf {
    let path = app
        .path()
        .resolve("app_data", AppData)
        .expect("Failed to resolve app data directory");
    Some(path).expect("Failed to create app data directory")
}

#[tauri::command]
async fn save_logs_to_file(_app: AppHandle, file_path: String, logs: String) -> Result<(), String> {
    println!("🛠️ Saving logs to file: {}", file_path);
    println!("Logs content: {}", logs);
    fs::write(file_path, logs).map_err(|e| format!("Failed to write logs to file: {}", e))?;
    Ok(())
}


#[tauri::command]
async fn generate_key_file(app: AppHandle, key_name: &str, key_file: &str) -> Result<String, String> {
    let app_data_dir = get_app_data_dir(app);
    let key_dir = app_data_dir.join("keys");
    let key_path = key_dir.join(key_name);
    let full_key_file = key_path.join(key_file);

    // Check if the key file already exists
    if full_key_file.exists() {
        return Ok(full_key_file.display().to_string());
    }

    // Create the necessary directories
    if let Err(e) = fs::create_dir_all(full_key_file.parent().unwrap()) {
        return Err(format!("Failed to create directory: {}", e));
    }

    // Ensure the key path exists and is a directory
    if !key_path.exists() || !key_path.is_dir() {
        return Err(format!("Invalid key path: {}", key_path.display()));
    }

    // Initialize Docker client
    let docker = get_docker_client().await;

    if let Err(e) = fetch_docker_image().await {
        eprintln!("❌ Error pulling image: {}", e);
        return Err(format!("Failed to pull image {}: {}", IMAGE_NAME, e));
    }
    // Configure the container
    let container_config = Config {
        image: Some(IMAGE_NAME),
        host_config: Some(HostConfig {
            binds: Some(vec![format!("{}:/app/tmp", key_path.display())]),
            ..Default::default()
        }),
        cmd: Some(vec!["generate-key", "ethereum"]),
        entrypoint: Some(vec!["/app/.venv/bin/autonomy"]),
        working_dir: Some("/app/tmp"),
        ..Default::default()
    };


    let container = docker.clone()?
        .create_container(Some(CreateContainerOptions { name: "test-container" , platform: None}), container_config)
        .await
        .expect("Failed to create container");

    println!("Created container: {}", container.id);

    println!("Starting container with ID: {}", container.id);
    docker.clone()?
        .start_container(&container.id, None::<StartContainerOptions<String>>)
        .await
        .map_err(|e| format!("Failed to start container: {}", e))?;

    // Wait for the container to finish
    println!("Waiting for container to finish running: {}", container.id);
    while docker.clone()?
        .inspect_container(&container.id, None)
        .await
        .map_err(|e| format!("Failed to inspect container: {}", e))?
        .state
        .as_ref()
        .map(|state| state.running.unwrap_or(false))
        .unwrap_or(false)
    {
        sleep(Duration::from_secs(1)).await;
    }

    println!("Container finished running: {}", container.id);
    // Remove the container
    docker?
        .remove_container(
            &container.id,
            Some(RemoveContainerOptions {
                force: true,
                ..Default::default()
            }),
        )
        .await
        .map_err(|e| format!("Failed to remove container: {}", e))?;

    // Check if the key file was created
    if full_key_file.exists() {
        println!("✅ Key file generated at: {}", full_key_file.display());
        Ok(full_key_file.display().to_string())
    } else {
        println!("❌ Failed to generate key file at: {}", full_key_file.display());
        Err(format!("Failed to generate key file at: {}", full_key_file.display()))
    }
}

#[tauri::command]
async fn connect_to_docker() -> bool {    
    match get_docker_client().await {
        Ok(_client) => {
           return true
        }
        Err(e) => {
            eprintln!("❌ Failed to connect to Docker: {}", e);
        }
    }
    false
}


#[cfg_attr(mobile, tauri::mobile_entry_point)]
pub fn run() {
    tauri::Builder::default()
        .plugin(tauri_plugin_websocket::init())
        .plugin(tauri_plugin_http::init())
        .plugin(tauri_plugin_store::Builder::new().build())
        .plugin(tauri_plugin_dialog::init())
        .invoke_handler(tauri::generate_handler![
            start_container_command,
            stop_container_command,
            pause_container_command,
            unpause_container_command,
            delete_container_command,
            get_container_logs,
            list_agents,
            get_agent_state,
            get_container_status_command,
            generate_key_file,
            save_logs_to_file,
            connect_to_docker,
        ])
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}
