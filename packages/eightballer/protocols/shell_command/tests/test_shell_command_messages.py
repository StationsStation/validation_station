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

"""Test messages module for shell_command protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
import os
from typing import Any, List

import yaml
from aea.test_tools.test_protocol import BaseProtocolMessagesTestCase
from packages.eightballer.protocols.shell_command.message import ShellCommandMessage
from packages.eightballer.protocols.shell_command.custom_types import ErrorCode


def load_data(custom_type):
    """Load test data."""
    with open(f"{os.path.dirname(__file__)}/dummy_data.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)[custom_type]


class TestMessageShellCommand(BaseProtocolMessagesTestCase):
    """Test for the 'shell_command' protocol message."""

    MESSAGE_CLASS = ShellCommandMessage

    def build_messages(self) -> List[ShellCommandMessage]:  # type: ignore[override]
        """Build the messages to be used for testing."""
        return [
            ShellCommandMessage(
                performative=ShellCommandMessage.Performative.EXECUTE_COMMAND,
                command="some str",
                args=("some str",),
                options={"some str": "some str"},
                timeout=12,
            ),
            ShellCommandMessage(
                performative=ShellCommandMessage.Performative.COMMAND_RESULT,
                stdout="some str",
                stderr="some str",
                exit_code=12,
            ),
            ShellCommandMessage(
                performative=ShellCommandMessage.Performative.EXECUTION_ERROR,
                error=ErrorCode(0),  # check it please!
                message="some str",
            ),
        ]

    def build_inconsistent(self) -> List[ShellCommandMessage]:  # type: ignore[override]
        """Build inconsistent messages to be used for testing."""
        return [
            ShellCommandMessage(
                performative=ShellCommandMessage.Performative.EXECUTE_COMMAND,
                # skip content: command
                args=("some str",),
                options={"some str": "some str"},
                timeout=12,
            ),
            ShellCommandMessage(
                performative=ShellCommandMessage.Performative.COMMAND_RESULT,
                # skip content: stdout
                stderr="some str",
                exit_code=12,
            ),
            ShellCommandMessage(
                performative=ShellCommandMessage.Performative.EXECUTION_ERROR,
                # skip content: error
                message="some str",
            ),
        ]
