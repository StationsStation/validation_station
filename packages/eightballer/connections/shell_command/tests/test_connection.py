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


"""This module contains the tests of the Shell Command connection module."""
# pylint: skip-file

import asyncio
from unittest.mock import MagicMock

import pytest
from aea.mail.base import Envelope
from aea.identity.base import Identity
from aea.configurations.base import ConnectionConfig

from packages.eightballer.protocols.shell_command.message import ShellCommandMessage
from packages.eightballer.protocols.shell_command.dialogues import (
    BaseShellCommandDialogues,
)
from packages.eightballer.connections.shell_command.connection import (
    CONNECTION_ID as CONNECTION_PUBLIC_ID,
    ShellCommandConnection,
)


def envelope_it(message: ShellCommandMessage):
    """Envelope the message."""

    return Envelope(
        to=message.to,
        sender=message.sender,
        message=message,
    )


class TestShellCommandConnection:
    """Test the Shell Command connection."""

    def setup(self):
        """Initialise the test case."""

        self.identity = Identity("dummy_name", address="dummy_address", public_key="dummy_public_key")
        self.agent_address = self.identity.address

        self.connection_id = ShellCommandConnection.connection_id
        self.protocol_id = ShellCommandMessage.protocol_id
        self.target_skill_id = "dummy_author/dummy_skill:0.1.0"

        kwargs = {}

        self.configuration = ConnectionConfig(
            target_skill_id=self.target_skill_id,
            connection_id=ShellCommandConnection.connection_id,
            restricted_to_protocols={ShellCommandMessage.protocol_id},
            **kwargs,
        )

        self.shell_command_connection = ShellCommandConnection(
            configuration=self.configuration,
            data_dir=MagicMock(),
            identity=self.identity,
        )

        self.loop = asyncio.get_event_loop()
        self.loop.run_until_complete(self.shell_command_connection.connect())
        self.connection_address = str(ShellCommandConnection.connection_id)
        self._dialogues = BaseShellCommandDialogues(
            self_address=self.target_skill_id,
        )

    @pytest.mark.asyncio
    async def test_shell_command_connection_connect(self):
        """Test the connect."""
        await self.shell_command_connection.connect()
        assert not self.shell_command_connection.channel.is_stopped

    @pytest.mark.asyncio
    async def test_shell_command_connection_disconnect(self):
        """Test the disconnect."""
        await self.shell_command_connection.disconnect()
        assert self.shell_command_connection.channel.is_stopped

    @pytest.mark.asyncio
    async def test_handles_inbound_query(self):
        """Test the connect."""
        await self.shell_command_connection.connect()

        msg, _dialogue = self._dialogues.create(
            counterparty=str(CONNECTION_PUBLIC_ID),
            performative=ShellCommandMessage.Performative.EXECUTE_COMMAND,
            command="ls",
            args=(),
            options={},
        )

        await self.shell_command_connection.send(envelope_it(msg))
