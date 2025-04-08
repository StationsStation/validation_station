# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2025 eightballer
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#
# ------------------------------------------------------------------------------

"""Serialization module for shell_command protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
from typing import Any, Dict, cast

from aea.mail.base_pb2 import DialogueMessage  # type: ignore
from aea.mail.base_pb2 import Message as ProtobufMessage  # type: ignore
from aea.protocols.base import Message  # type: ignore
from aea.protocols.base import Serializer  # type: ignore

from packages.eightballer.protocols.shell_command import (  # type: ignore
    shell_command_pb2,
)
from packages.eightballer.protocols.shell_command.custom_types import (  # type: ignore
    ErrorCode,
)
from packages.eightballer.protocols.shell_command.message import (  # type: ignore
    ShellCommandMessage,
)


class ShellCommandSerializer(Serializer):
    """Serialization for the 'shell_command' protocol."""

    @staticmethod
    def encode(msg: Message) -> bytes:
        """
        Encode a 'ShellCommand' message into bytes.

        :param msg: the message object.
        :return: the bytes.
        """
        msg = cast(ShellCommandMessage, msg)
        message_pb = ProtobufMessage()
        dialogue_message_pb = DialogueMessage()
        shell_command_msg = shell_command_pb2.ShellCommandMessage()  # type: ignore

        dialogue_message_pb.message_id = msg.message_id
        dialogue_reference = msg.dialogue_reference
        dialogue_message_pb.dialogue_starter_reference = dialogue_reference[0]
        dialogue_message_pb.dialogue_responder_reference = dialogue_reference[1]
        dialogue_message_pb.target = msg.target

        performative_id = msg.performative
        if performative_id == ShellCommandMessage.Performative.EXECUTE_COMMAND:
            performative = shell_command_pb2.ShellCommandMessage.Execute_Command_Performative()  # type: ignore
            command = msg.command
            performative.command = command
            args = msg.args
            performative.args.extend(args)
            options = msg.options
            performative.options.update(options)
            if msg.is_set("timeout"):
                performative.timeout_is_set = True
                timeout = msg.timeout
                performative.timeout = timeout
            if msg.is_set("env_vars"):
                performative.env_vars_is_set = True
                env_vars = msg.env_vars
                performative.env_vars = env_vars
            shell_command_msg.execute_command.CopyFrom(performative)
        elif performative_id == ShellCommandMessage.Performative.COMMAND_RESULT:
            performative = shell_command_pb2.ShellCommandMessage.Command_Result_Performative()  # type: ignore
            stdout = msg.stdout
            performative.stdout = stdout
            stderr = msg.stderr
            performative.stderr = stderr
            exit_code = msg.exit_code
            performative.exit_code = exit_code
            shell_command_msg.command_result.CopyFrom(performative)
        elif performative_id == ShellCommandMessage.Performative.EXECUTION_ERROR:
            performative = shell_command_pb2.ShellCommandMessage.Execution_Error_Performative()  # type: ignore
            error = msg.error
            ErrorCode.encode(performative.error, error)
            if msg.is_set("message"):
                performative.message_is_set = True
                message = msg.message
                performative.message = message
            shell_command_msg.execution_error.CopyFrom(performative)
        else:
            raise ValueError("Performative not valid: {}".format(performative_id))

        dialogue_message_pb.content = shell_command_msg.SerializeToString()

        message_pb.dialogue_message.CopyFrom(dialogue_message_pb)
        message_bytes = message_pb.SerializeToString()
        return message_bytes

    @staticmethod
    def decode(obj: bytes) -> Message:
        """
        Decode bytes into a 'ShellCommand' message.

        :param obj: the bytes object.
        :return: the 'ShellCommand' message.
        """
        message_pb = ProtobufMessage()
        shell_command_pb = shell_command_pb2.ShellCommandMessage()  # type: ignore
        message_pb.ParseFromString(obj)
        message_id = message_pb.dialogue_message.message_id
        dialogue_reference = (
            message_pb.dialogue_message.dialogue_starter_reference,
            message_pb.dialogue_message.dialogue_responder_reference,
        )
        target = message_pb.dialogue_message.target

        shell_command_pb.ParseFromString(message_pb.dialogue_message.content)
        performative = shell_command_pb.WhichOneof("performative")
        performative_id = ShellCommandMessage.Performative(str(performative))
        performative_content = dict()  # type: Dict[str, Any]
        if performative_id == ShellCommandMessage.Performative.EXECUTE_COMMAND:
            command = shell_command_pb.execute_command.command
            performative_content["command"] = command
            args = shell_command_pb.execute_command.args
            args_tuple = tuple(args)
            performative_content["args"] = args_tuple
            options = shell_command_pb.execute_command.options
            options_dict = dict(options)
            performative_content["options"] = options_dict
            if shell_command_pb.execute_command.timeout_is_set:
                timeout = shell_command_pb.execute_command.timeout
                performative_content["timeout"] = timeout
            if shell_command_pb.execute_command.env_vars_is_set:
                env_vars = shell_command_pb.execute_command.env_vars
                performative_content["env_vars"] = env_vars
        elif performative_id == ShellCommandMessage.Performative.COMMAND_RESULT:
            stdout = shell_command_pb.command_result.stdout
            performative_content["stdout"] = stdout
            stderr = shell_command_pb.command_result.stderr
            performative_content["stderr"] = stderr
            exit_code = shell_command_pb.command_result.exit_code
            performative_content["exit_code"] = exit_code
        elif performative_id == ShellCommandMessage.Performative.EXECUTION_ERROR:
            pb2_error = shell_command_pb.execution_error.error
            error = ErrorCode.decode(pb2_error)
            performative_content["error"] = error
            if shell_command_pb.execution_error.message_is_set:
                message = shell_command_pb.execution_error.message
                performative_content["message"] = message
        else:
            raise ValueError("Performative not valid: {}.".format(performative_id))

        return ShellCommandMessage(
            message_id=message_id,
            dialogue_reference=dialogue_reference,
            target=target,
            performative=performative,
            **performative_content
        )
