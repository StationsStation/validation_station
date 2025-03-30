pub const MAX_SIZE: usize = 5 * 1024 * 1024; // 5MB
pub const MAX_REQUEST_TIMEOUT: u64 = 10;     // 10 seconds

// CONSTANTS TO BE DEFINED ONCHAIN;
pub const MIN_ATTESTATIONS : usize = 1;       // Minimum number of attestations required for optimistic response
pub const MAX_BROADCAST_GROUP: usize = 50;            // Maximum number of brokers to connect to for consensus

pub const HEARTBEAT_TIMEOUT : u64 = 10;       // Timeout for consensus in seconds
pub const HEARTBEAT_INTERVAL : u64 = 2;       // Heartbeat interval in seconds

// pub const CONSENSUS_TIMEOUT: u64 = 10;        // Timeout for consensus in seconds
// pub const CONSENSUS_INTERVAL: u64 = 2;        // Consensus interval in seconds

pub const PENALTY_MISSED_HEARTBEAT: u64 = 1; // Penalty for missed heartbeat
pub const PENALTY_LATE_MESSAGE: u64 = 1;     // Penalty for late message
pub const PENALTY_MISMATCHED_DATA: u64 = 1;  // Penalty for mismatched data
// pub const PENALTY_OUTSTANDING_REQUEST: u64 = 1; // Penalty for outstanding request

// pub const REWARDS_HEARTBEAT: u64 = 1;         // Reward for first response
pub const REWARDS_CONSENSUS: u64 = 10;         // Reward for consensus
pub const REWARDS_OPTIMISTIC: u64 = 10;        // Reward for optimistic response
