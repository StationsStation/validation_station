# Shell Command Protocol

## Description

...

## Specification

```yaml
name: shell_command
author: eightballer
version: 0.1.0
description: A protocol for executing command-line instructions between an agent and a CLI shell.
license: Apache-2.0
aea_version: '>=1.0.0, <2.0.0'
protocol_specification_id: eightballer/shell_command:0.1.0
speech_acts:
  execute_command:
    command: pt:str
    args: pt:list[pt:str]
    options: pt:dict[pt:str, pt:str]
    timeout: pt:optional[pt:int]
    env_vars: pt:optional[pt:bytes]
  command_result:
    stdout: pt:str
    stderr: pt:str
    exit_code: pt:int
  execution_error:
    error: ct:ErrorCode
    message: pt:optional[pt:str]
---
ct:ErrorCode: |
  enum ErrorCodeEnum {
      COMMAND_EXECUTION_FAILURE = 0;
      TIMEOUT_ERROR = 1;
      INVALID_COMMAND = 2;
    }
  ErrorCodeEnum error_code = 1;
---
initiation: [execute_command]
reply:
  execute_command: [command_result, execution_error]
  command_result: []
  execution_error: []
termination: [command_result, execution_error, ]
roles: { agent, cli_shell }
end_states: [  command_result, execution_error ]
keep_terminal_state_dialogues: false

```