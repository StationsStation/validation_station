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

"""Test dialogues module for shell_command protocol."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,redefined-builtin
import os

import yaml
from aea.test_tools.test_protocol import BaseProtocolDialoguesTestCase
from packages.eightballer.protocols.shell_command.message import ShellCommandMessage
from packages.eightballer.protocols.shell_command.dialogues import (
    ShellCommandDialogue,
    BaseShellCommandDialogues,
)
from packages.eightballer.protocols.shell_command.custom_types import ErrorCode


def load_data(custom_type):
    """Load test data."""
    with open(f"{os.path.dirname(__file__)}/dummy_data.yaml", "r", encoding="utf-8") as f:
        return yaml.safe_load(f)[custom_type]


class TestDialoguesShellCommand(BaseProtocolDialoguesTestCase):
    """Test for the 'shell_command' protocol dialogues."""

    MESSAGE_CLASS = ShellCommandMessage

    DIALOGUE_CLASS = ShellCommandDialogue

    DIALOGUES_CLASS = BaseShellCommandDialogues

    ROLE_FOR_THE_FIRST_MESSAGE = ShellCommandDialogue.Role.AGENT  # CHECK

    def make_message_content(self) -> dict:
        """Make a dict with message contruction content for dialogues.create."""
        return dict(
            performative=ShellCommandMessage.Performative.EXECUTE_COMMAND,
            command="some str",
            args=("some str",),
            options={"some str": "some str"},
            timeout=12,
            env_vars=b"some_bytes",
        )
