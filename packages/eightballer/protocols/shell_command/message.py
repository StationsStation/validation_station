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

"""This module contains shell_command's message definition."""

# pylint: disable=too-many-statements,too-many-locals,no-member,too-few-public-methods,too-many-branches,not-an-iterable,unidiomatic-typecheck,unsubscriptable-object
import logging
from typing import Any, Dict, Optional, Set, Tuple, cast

from aea.configurations.base import PublicId
from aea.exceptions import AEAEnforceError, enforce
from aea.protocols.base import Message  # type: ignore

from packages.eightballer.protocols.shell_command.custom_types import (
    ErrorCode as CustomErrorCode,
)


_default_logger = logging.getLogger(
    "aea.packages.eightballer.protocols.shell_command.message"
)

DEFAULT_BODY_SIZE = 4


class ShellCommandMessage(Message):
    """A protocol for executing command-line instructions between an agent and a CLI shell."""

    protocol_id = PublicId.from_str("eightballer/shell_command:0.1.0")
    protocol_specification_id = PublicId.from_str("eightballer/shell_command:0.1.0")

    ErrorCode = CustomErrorCode

    class Performative(Message.Performative):
        """Performatives for the shell_command protocol."""

        COMMAND_RESULT = "command_result"
        EXECUTE_COMMAND = "execute_command"
        EXECUTION_ERROR = "execution_error"

        def __str__(self) -> str:
            """Get the string representation."""
            return str(self.value)

    _performatives = {"command_result", "execute_command", "execution_error"}
    __slots__: Tuple[str, ...] = tuple()

    class _SlotsCls:
        __slots__ = (
            "args",
            "command",
            "dialogue_reference",
            "env_vars",
            "error",
            "exit_code",
            "message",
            "message_id",
            "options",
            "performative",
            "stderr",
            "stdout",
            "target",
            "timeout",
        )

    def __init__(
        self,
        performative: Performative,
        dialogue_reference: Tuple[str, str] = ("", ""),
        message_id: int = 1,
        target: int = 0,
        **kwargs: Any,
    ):
        """
        Initialise an instance of ShellCommandMessage.

        :param message_id: the message id.
        :param dialogue_reference: the dialogue reference.
        :param target: the message target.
        :param performative: the message performative.
        :param **kwargs: extra options.
        """
        super().__init__(
            dialogue_reference=dialogue_reference,
            message_id=message_id,
            target=target,
            performative=ShellCommandMessage.Performative(performative),
            **kwargs,
        )

    @property
    def valid_performatives(self) -> Set[str]:
        """Get valid performatives."""
        return self._performatives

    @property
    def dialogue_reference(self) -> Tuple[str, str]:
        """Get the dialogue_reference of the message."""
        enforce(self.is_set("dialogue_reference"), "dialogue_reference is not set.")
        return cast(Tuple[str, str], self.get("dialogue_reference"))

    @property
    def message_id(self) -> int:
        """Get the message_id of the message."""
        enforce(self.is_set("message_id"), "message_id is not set.")
        return cast(int, self.get("message_id"))

    @property
    def performative(self) -> Performative:  # type: ignore # noqa: F821
        """Get the performative of the message."""
        enforce(self.is_set("performative"), "performative is not set.")
        return cast(ShellCommandMessage.Performative, self.get("performative"))

    @property
    def target(self) -> int:
        """Get the target of the message."""
        enforce(self.is_set("target"), "target is not set.")
        return cast(int, self.get("target"))

    @property
    def args(self) -> Tuple[str, ...]:
        """Get the 'args' content from the message."""
        enforce(self.is_set("args"), "'args' content is not set.")
        return cast(Tuple[str, ...], self.get("args"))

    @property
    def command(self) -> str:
        """Get the 'command' content from the message."""
        enforce(self.is_set("command"), "'command' content is not set.")
        return cast(str, self.get("command"))

    @property
    def env_vars(self) -> Optional[bytes]:
        """Get the 'env_vars' content from the message."""
        return cast(Optional[bytes], self.get("env_vars"))

    @property
    def error(self) -> CustomErrorCode:
        """Get the 'error' content from the message."""
        enforce(self.is_set("error"), "'error' content is not set.")
        return cast(CustomErrorCode, self.get("error"))

    @property
    def exit_code(self) -> int:
        """Get the 'exit_code' content from the message."""
        enforce(self.is_set("exit_code"), "'exit_code' content is not set.")
        return cast(int, self.get("exit_code"))

    @property
    def message(self) -> Optional[str]:
        """Get the 'message' content from the message."""
        return cast(Optional[str], self.get("message"))

    @property
    def options(self) -> Dict[str, str]:
        """Get the 'options' content from the message."""
        enforce(self.is_set("options"), "'options' content is not set.")
        return cast(Dict[str, str], self.get("options"))

    @property
    def stderr(self) -> str:
        """Get the 'stderr' content from the message."""
        enforce(self.is_set("stderr"), "'stderr' content is not set.")
        return cast(str, self.get("stderr"))

    @property
    def stdout(self) -> str:
        """Get the 'stdout' content from the message."""
        enforce(self.is_set("stdout"), "'stdout' content is not set.")
        return cast(str, self.get("stdout"))

    @property
    def timeout(self) -> Optional[int]:
        """Get the 'timeout' content from the message."""
        return cast(Optional[int], self.get("timeout"))

    def _is_consistent(self) -> bool:
        """Check that the message follows the shell_command protocol."""
        try:
            enforce(
                isinstance(self.dialogue_reference, tuple),
                "Invalid type for 'dialogue_reference'. Expected 'tuple'. Found '{}'.".format(
                    type(self.dialogue_reference)
                ),
            )
            enforce(
                isinstance(self.dialogue_reference[0], str),
                "Invalid type for 'dialogue_reference[0]'. Expected 'str'. Found '{}'.".format(
                    type(self.dialogue_reference[0])
                ),
            )
            enforce(
                isinstance(self.dialogue_reference[1], str),
                "Invalid type for 'dialogue_reference[1]'. Expected 'str'. Found '{}'.".format(
                    type(self.dialogue_reference[1])
                ),
            )
            enforce(
                type(self.message_id) is int,
                "Invalid type for 'message_id'. Expected 'int'. Found '{}'.".format(
                    type(self.message_id)
                ),
            )
            enforce(
                type(self.target) is int,
                "Invalid type for 'target'. Expected 'int'. Found '{}'.".format(
                    type(self.target)
                ),
            )

            # Light Protocol Rule 2
            # Check correct performative
            enforce(
                isinstance(self.performative, ShellCommandMessage.Performative),
                "Invalid 'performative'. Expected either of '{}'. Found '{}'.".format(
                    self.valid_performatives, self.performative
                ),
            )

            # Check correct contents
            actual_nb_of_contents = len(self._body) - DEFAULT_BODY_SIZE
            expected_nb_of_contents = 0
            if self.performative == ShellCommandMessage.Performative.EXECUTE_COMMAND:
                expected_nb_of_contents = 3
                enforce(
                    isinstance(self.command, str),
                    "Invalid type for content 'command'. Expected 'str'. Found '{}'.".format(
                        type(self.command)
                    ),
                )
                enforce(
                    isinstance(self.args, tuple),
                    "Invalid type for content 'args'. Expected 'tuple'. Found '{}'.".format(
                        type(self.args)
                    ),
                )
                enforce(
                    all(isinstance(element, str) for element in self.args),
                    "Invalid type for tuple elements in content 'args'. Expected 'str'.",
                )
                enforce(
                    isinstance(self.options, dict),
                    "Invalid type for content 'options'. Expected 'dict'. Found '{}'.".format(
                        type(self.options)
                    ),
                )
                for key_of_options, value_of_options in self.options.items():
                    enforce(
                        isinstance(key_of_options, str),
                        "Invalid type for dictionary keys in content 'options'. Expected 'str'. Found '{}'.".format(
                            type(key_of_options)
                        ),
                    )
                    enforce(
                        isinstance(value_of_options, str),
                        "Invalid type for dictionary values in content 'options'. Expected 'str'. Found '{}'.".format(
                            type(value_of_options)
                        ),
                    )
                if self.is_set("timeout"):
                    expected_nb_of_contents += 1
                    timeout = cast(int, self.timeout)
                    enforce(
                        type(timeout) is int,
                        "Invalid type for content 'timeout'. Expected 'int'. Found '{}'.".format(
                            type(timeout)
                        ),
                    )
                if self.is_set("env_vars"):
                    expected_nb_of_contents += 1
                    env_vars = cast(bytes, self.env_vars)
                    enforce(
                        isinstance(env_vars, bytes),
                        "Invalid type for content 'env_vars'. Expected 'bytes'. Found '{}'.".format(
                            type(env_vars)
                        ),
                    )
            elif self.performative == ShellCommandMessage.Performative.COMMAND_RESULT:
                expected_nb_of_contents = 3
                enforce(
                    isinstance(self.stdout, str),
                    "Invalid type for content 'stdout'. Expected 'str'. Found '{}'.".format(
                        type(self.stdout)
                    ),
                )
                enforce(
                    isinstance(self.stderr, str),
                    "Invalid type for content 'stderr'. Expected 'str'. Found '{}'.".format(
                        type(self.stderr)
                    ),
                )
                enforce(
                    type(self.exit_code) is int,
                    "Invalid type for content 'exit_code'. Expected 'int'. Found '{}'.".format(
                        type(self.exit_code)
                    ),
                )
            elif self.performative == ShellCommandMessage.Performative.EXECUTION_ERROR:
                expected_nb_of_contents = 1
                enforce(
                    isinstance(self.error, CustomErrorCode),
                    "Invalid type for content 'error'. Expected 'ErrorCode'. Found '{}'.".format(
                        type(self.error)
                    ),
                )
                if self.is_set("message"):
                    expected_nb_of_contents += 1
                    message = cast(str, self.message)
                    enforce(
                        isinstance(message, str),
                        "Invalid type for content 'message'. Expected 'str'. Found '{}'.".format(
                            type(message)
                        ),
                    )

            # Check correct content count
            enforce(
                expected_nb_of_contents == actual_nb_of_contents,
                "Incorrect number of contents. Expected {}. Found {}".format(
                    expected_nb_of_contents, actual_nb_of_contents
                ),
            )

            # Light Protocol Rule 3
            if self.message_id == 1:
                enforce(
                    self.target == 0,
                    "Invalid 'target'. Expected 0 (because 'message_id' is 1). Found {}.".format(
                        self.target
                    ),
                )
        except (AEAEnforceError, ValueError, KeyError) as e:
            _default_logger.error(str(e))
            return False

        return True
