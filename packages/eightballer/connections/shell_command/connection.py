# -*- coding: utf-8 -*-
# ------------------------------------------------------------------------------
#
#   Copyright 2024 eightballer
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

# pylint: disable=too-many-instance-attributes, W0511, w0613
"""Shell Command connection and channel."""

import sys
import asyncio
import json
import logging
import os
import subprocess
from abc import abstractmethod
import sys
from typing import Any, Set, Dict, Callable, Optional, cast
from asyncio.events import AbstractEventLoop

from aea.common import Address
from aea.mail.base import Message, Envelope
from aea.connections.base import Connection, ConnectionStates
from aea.configurations.base import PublicId
from aea.protocols.dialogue.base import Dialogue
from packages.eightballer.protocols.shell_command.message import ShellCommandMessage
from packages.eightballer.protocols.shell_command.dialogues import (
    ShellCommandDialogue,
    BaseShellCommandDialogues,
)


sys.stdout.reconfigure(line_buffering=True) 
CONNECTION_ID = PublicId.from_str("eightballer/shell_command:0.1.0")


_default_logger = logging.getLogger("aea.packages.eightballer.connections.shell_command")


class ShellCommandDialogues(BaseShellCommandDialogues):
    """The dialogues class keeps track of all shell_command dialogues."""

    def __init__(self, self_address: Address, **kwargs) -> None:
        """
        Initialize dialogues.

        :param self_address: self address
        :param kwargs: keyword arguments
        """

        def role_from_first_message(  # pylint: disable=unused-argument
            message: Message, receiver_address: Address
        ) -> Dialogue.Role:
            """Infer the role of the agent from an incoming/outgoing first message

            :param message: an incoming/outgoing first message
            :param receiver_address: the address of the receiving agent
            :return: The role of the agent
            """
            assert message, receiver_address
            return ShellCommandDialogue.Role.AGENT

        BaseShellCommandDialogues.__init__(
            self,
            self_address=self_address,
            role_from_first_message=role_from_first_message,
            **kwargs,
        )


class BaseAsyncChannel:
    """BaseAsyncChannel."""

    def __init__(
        self,
        agent_address: Address,
        connection_id: PublicId,
        message_type: Message,
    ):
        """
        Initialize the BaseAsyncChannel channel.

        :param agent_address: the address of the agent.
        :param connection_id: the id of the connection.
        :param message_type: the associated message type.
        """

        self.agent_address = agent_address
        self.connection_id = connection_id
        self.message_type = message_type

        self.is_stopped = True
        self._connection = None
        self._tasks: Set[asyncio.Task] = set()
        self._in_queue: Optional[asyncio.Queue] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self.logger = _default_logger
        self.working_directory = "."

    @property
    @abstractmethod
    def performative_handlers(
        self,
    ) -> Dict[Message.Performative, Callable[[Message, Dialogue], Message]]:
        """Performative to message handler mapping."""

    @abstractmethod
    async def connect(self, loop: AbstractEventLoop) -> None:
        """Connect channel using loop."""

    @abstractmethod
    async def disconnect(self) -> None:
        """Disconnect channel."""

    async def send(self, envelope: Envelope) -> None:
        """
        Send an envelope with a protocol message.

        It sends the envelope, waits for and receives the result.
        The result is translated into a response envelope.
        Finally, the response envelope is sent to the in-queue.

        :param query_envelope: The envelope containing a protocol message.
        """

        if not self._loop:
            raise ConnectionError("{self.__class__.__name__} not connected, call connect first!")

        if not isinstance(envelope.message, self.message_type):
            raise TypeError(f"Message not of type {self.message_type}")

        message = envelope.message

        if message.performative not in self.performative_handlers:
            log_msg = "Message with unexpected performative `{message.performative}` received."
            self.logger.error(log_msg)
            return

        handler = self.performative_handlers[message.performative]

        dialogue = cast(Dialogue, self._dialogues.update(message))  # noqa
        if dialogue is None:
            self.logger.warning(f"Could not create dialogue for message={message}")
            return

        response_message = await handler(message, dialogue)
        self.logger.info(f"returning message: {response_message}")

        response_envelope = Envelope(
            to=str(envelope.sender),
            sender=str(self.connection_id),
            message=response_message,
            protocol_specification_id=self.message_type.protocol_specification_id,
        )

        await self._in_queue.put(response_envelope)

    async def get_message(self) -> Optional[Envelope]:
        """Check the in-queue for envelopes."""

        if self.is_stopped:
            return None
        try:
            envelope = self._in_queue.get_nowait()
            return envelope
        except asyncio.QueueEmpty:
            return None

    async def _cancel_tasks(self) -> None:
        """Cancel all requests tasks pending."""

        for task in list(self._tasks):
            if task.done():  # pragma: nocover
                continue
            task.cancel()

        for task in list(self._tasks):
            try:
                await task
            except KeyboardInterrupt:  # noqa
                raise
            except BaseException:  # noqa
                pass  # nosec

    async def _cancel_processes(self):
        """Forcefully cancel all running processes."""
        for process in list(self._running_processes):
            self.logger.info(f"Killing process {process.pid}")
            process.kill()
            process.wait()
            self._running_processes.remove(process)
            


class ShellCommandAsyncChannel(BaseAsyncChannel):  # pylint: disable=too-many-instance-attributes
    """A channel handling incomming communication from the Shell Command connection."""

    def __init__(
        self,
        agent_address: Address,
        connection_id: PublicId,
        **kwargs,
    ):
        """
        Initialize the Shell Command channel.

        :param agent_address: the address of the agent.
        :param connection_id: the id of the connection.
        """

        super().__init__(agent_address, connection_id, message_type=ShellCommandMessage)

        for key, value in kwargs.items():
            setattr(self, key, value)

        self._running_processes: Set[subprocess.Popen] = set()
        self._dialogues = ShellCommandDialogues(str(ShellCommandConnection.connection_id))
        self.logger.debug("Initialised the Shell Command channel")

    async def connect(self, loop: AbstractEventLoop) -> None:
        """
        Connect channel using loop.

        :param loop: asyncio event loop to use
        """

        if self.is_stopped:
            self._loop = loop
            self._in_queue = asyncio.Queue()
            self.is_stopped = False
            try:
                self.logger.info("Shell Command has connected.")
            except Exception as error:  # pragma: nocover # pylint: disable=broad-except
                self.is_stopped = True
                self._in_queue = None
                raise ConnectionError(f"Failed to start Shell Command: {error}") from error

    async def disconnect(self) -> None:
        """Disconnect channel."""

        if self.is_stopped:
            return

        await self._cancel_tasks()
        self.is_stopped = True
        self.logger.info("Shell Command has shutdown.")

    @property
    def performative_handlers(
        self,
    ) -> Dict[
        ShellCommandMessage.Performative,
        Callable[[ShellCommandMessage, ShellCommandDialogue], ShellCommandMessage],
    ]:
        """Map performative to handler."""
        return {
            ShellCommandMessage.Performative.EXECUTE_COMMAND: self.execute_command,
        }

    

    async def _stream_output(self, process, stream_output=True, fmt=""):
        """Stream both stdout and stderr in real-time with optimized async approach."""

        stdout_lines = []
        stderr_lines = []

        # Function to read stdout asynchronously
        async def read_stdout():
            while True:
                output = await process.stdout.readline()
                if process.returncode is not None:  # If the output is empty, the process is done
                    break
                if output:
                    output = output.decode("utf-8").strip()  # Manually decode bytes to string
                    stdout_lines.append(output)
                    if stream_output:
                        print(fmt + output)
                    sys.stdout.flush()

        # Function to read stderr asynchronously
        async def read_stderr():
            while True:
                error = await process.stderr.readline()
                if error == b'' and process.returncode is not None:  # If the output is empty, the process is done
                    break
                if error:
                    error = error.decode("utf-8").strip()  # Manually decode bytes to string
                    stderr_lines.append(error)
                    if stream_output:
                        print(fmt + error)
                    sys.stderr.flush()

        # Start both tasks concurrently
        await asyncio.gather(read_stdout(), read_stderr())

        return process, stdout_lines, stderr_lines


    async def _run_process(self, command, env_vars=None):
        """Run the command and return the process."""
        return await asyncio.create_subprocess_exec(
            *command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env_vars if env_vars else None,

        )

    async def execute_command(self, message: ShellCommandMessage, dialogue: ShellCommandDialogue) -> ShellCommandMessage:
        """Handle ShellCommandMessage with EXECUTE_COMMAND Perfomative"""

        command = message.command
        options = message.options

        command_list = [command] + list(message.args) + [f"{k}={v}" for k, v in options.items()]

        env_vars = os.environ.copy()
        if message.env_vars is not None:
            env_vars_json = message.env_vars.decode("utf-8")
            env_vars = json.loads(env_vars_json)
            env_vars.update(env_vars)

        stream_output = True
        timeout = 0

        async def execute_command(command):
            """Execute the command, stream output, and return the logs."""
            self.logger.info(f"Executing command: {command}")
            process = await self._run_process(command, env_vars=env_vars)
            self.logger.info("Process started: %s", process)
            self._running_processes.add(process)
            future = self._stream_output(process, fmt="", stream_output=stream_output)
            self._tasks.add(asyncio.ensure_future(future))
            proc, stdout_lines, stderr_lines = process, [], []
            return proc, stdout_lines, stderr_lines

        proc, stdout_lines, stderr_lines = await execute_command(command_list)

        if proc.returncode is None:
            self.logger.info(f"Command started successfully: {command_list}")
            return dialogue.reply(
                performative=ShellCommandMessage.Performative.COMMAND_RESULT,
                stderr=stderr_lines,
                stdout=stdout_lines,
                exit_code=-1,
            )

        error = f"command failed with exit code {proc.returncode}"
        return dialogue.reply(
            performative=ShellCommandMessage.Performative.EXECUTION_ERROR,
            error=error,
            stderr=stderr_lines,
            stdout=stdout_lines,
            exit_code=proc.returncode
        )


class ShellCommandConnection(Connection):
    """Proxy to the functionality of a Shell Command connection."""

    connection_id = CONNECTION_ID

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize a Shell Command connection.

        :param kwargs: keyword arguments
        """

        keys = []
        config = kwargs["configuration"].config
        custom_kwargs = {key: config.pop(key) for key in keys}
        super().__init__(**kwargs)

        self.channel = ShellCommandAsyncChannel(
            self.address,
            connection_id=self.connection_id,
            **custom_kwargs,
        )

    async def connect(self) -> None:
        """Connect to a Shell Command."""

        if self.is_connected:  # pragma: nocover
            return

        with self._connect_context():
            self.channel.logger = self.logger
            await self.channel.connect(self.loop)

    async def disconnect(self) -> None:
        """Disconnect from a Shell Command."""

        if self.is_disconnected:
            return  # pragma: nocover
        self.state = ConnectionStates.disconnecting
        await self.channel.disconnect()
        self.state = ConnectionStates.disconnected

    async def send(self, envelope: Envelope) -> None:
        """
        Send an envelope.

        :param envelope: the envelope to send.
        """

        self._ensure_connected()
        return await self.channel.send(envelope)

    async def receive(self, *args: Any, **kwargs: Any) -> Optional[Envelope]:
        """
        Receive an envelope. Blocking.

        :param args: arguments to receive
        :param kwargs: keyword arguments to receive
        :return: the envelope received, if present.  # noqa: DAR202
        """
        del args, kwargs

        self._ensure_connected()
        try:
            result = await self.channel.get_message()
            return result
        except Exception as e:  # noqa
            self.logger.info(f"Exception on receive {e}")
            return None
