/*
 Generated by typeshare 1.11.0
*/


export enum AgentStatus {
	Started = "Started",
	Running = "Running",
	Stopped = "Stopped",
	Stopping = "Stopping",
	Paused = "Paused",
	Exited = "Exited",
}

export interface Agent {
	id: string;
	status: AgentStatus;
	address: string;
	lastSeenTimestamp: string;
}

export interface UserConfiguration {
	privateKeyPath: string;
	environmentPath: string;
}

