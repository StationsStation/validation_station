// src/shared.rs

use serde::Serialize;
use typeshare::typeshare;


// We define an enum for the status of the agent


#[typeshare]
#[derive(serde::Serialize)]
pub enum AgentStatus {
    Started,
    Running,
    Stopped,
    Stopping,
    Paused,
    Exited,
}


#[typeshare]
#[derive(serde::Serialize)]
#[serde(rename_all = "camelCase")]
pub struct Agent{
    pub id: String,
    pub name: String,
    pub status: AgentStatus,
    pub address: String,
    pub last_seen_timestamp: String,
}

// We have a configuration struct for the agent auth
#[typeshare]
#[derive(serde::Serialize, serde::Deserialize, Debug)]
#[serde(rename_all = "camelCase")]
pub struct UserConfiguration {
    pub private_key_path: String,
    pub environment_path: String,
}


#[typeshare]
#[derive(serde::Serialize, serde::Deserialize, Debug)]
#[serde(rename_all = "camelCase")]
pub struct AgentTemplate {
    pub name: String,
    pub description: String,
    pub version: String,
    pub author: String,
}
