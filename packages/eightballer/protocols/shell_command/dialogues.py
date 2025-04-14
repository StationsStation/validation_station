"""
This module contains the classes required for shell_command dialogue management.

- ShellCommandDialogue: The dialogue class maintains state of a dialogue and manages it.
- ShellCommandDialogues: The dialogues class keeps track of all dialogues.
"""

from abc import ABC
from typing import Dict, Type, Callable, FrozenSet, cast

from aea.common import Address
from aea.skills.base import Model
from aea.protocols.base import Message
from aea.protocols.dialogue.base import Dialogue, Dialogues, DialogueLabel
from packages.eightballer.protocols.shell_command.message import ShellCommandMessage


def _role_from_first_message(message: Message, sender: Address) -> Dialogue.Role:
    """Infer the role of the agent from an incoming/outgoing first message"""
    del sender, message
    return ShellCommandDialogue.Role.AGENT


class ShellCommandDialogue(Dialogue):
    """The shell_command dialogue class maintains state of a dialogue and manages it."""

    INITIAL_PERFORMATIVES: FrozenSet[Message.Performative] = frozenset(
        {ShellCommandMessage.Performative.EXECUTE_COMMAND}
    )
    TERMINAL_PERFORMATIVES: FrozenSet[Message.Performative] = frozenset(
        {ShellCommandMessage.Performative.COMMAND_RESULT, ShellCommandMessage.Performative.EXECUTION_ERROR}
    )
    VALID_REPLIES: Dict[Message.Performative, FrozenSet[Message.Performative]] = {
        ShellCommandMessage.Performative.COMMAND_RESULT: frozenset(),
        ShellCommandMessage.Performative.EXECUTE_COMMAND: frozenset(
            {ShellCommandMessage.Performative.COMMAND_RESULT, ShellCommandMessage.Performative.EXECUTION_ERROR}
        ),
        ShellCommandMessage.Performative.EXECUTION_ERROR: frozenset(),
    }

    class Role(Dialogue.Role):
        """This class defines the agent's role in a shell_command dialogue."""

        AGENT = "agent"
        CLI_SHELL = "cli_shell"

    class EndState(Dialogue.EndState):
        """This class defines the end states of a shell_command dialogue."""

        COMMAND_RESULT = 0
        EXECUTION_ERROR = 1

    def __init__(
        self,
        dialogue_label: DialogueLabel,
        self_address: Address,
        role: Dialogue.Role,
        message_class: Type[ShellCommandMessage] = ShellCommandMessage,
    ) -> None:
        """
        Initialize a dialogue.



        Args:
               dialogue_label:  the identifier of the dialogue
               self_address:  the address of the entity for whom this dialogue is maintained
               role:  the role of the agent this dialogue is maintained for
               message_class:  the message class used

        """
        Dialogue.__init__(
            self, dialogue_label=dialogue_label, message_class=message_class, self_address=self_address, role=role
        )


class BaseShellCommandDialogues(Dialogues, ABC):
    """This class keeps track of all shell_command dialogues."""

    END_STATES = frozenset(
        {ShellCommandDialogue.EndState.COMMAND_RESULT, ShellCommandDialogue.EndState.EXECUTION_ERROR}
    )
    _keep_terminal_state_dialogues = False

    def __init__(
        self,
        self_address: Address,
        role_from_first_message: Callable[[Message, Address], Dialogue.Role] = _role_from_first_message,
        dialogue_class: Type[ShellCommandDialogue] = ShellCommandDialogue,
    ) -> None:
        """
        Initialize dialogues.



        Args:
               self_address:  the address of the entity for whom dialogues are maintained
               dialogue_class:  the dialogue class used
               role_from_first_message:  the callable determining role from first message

        """
        Dialogues.__init__(
            self,
            self_address=self_address,
            end_states=cast(FrozenSet[Dialogue.EndState], self.END_STATES),
            message_class=ShellCommandMessage,
            dialogue_class=dialogue_class,
            role_from_first_message=role_from_first_message,
        )


class ShellCommandDialogues(BaseShellCommandDialogues, Model):
    """This class defines the dialogues used in Shell_command."""

    def __init__(self, **kwargs):
        """Initialize dialogues."""
        Model.__init__(self, keep_terminal_state_dialogues=False, **kwargs)
        BaseShellCommandDialogues.__init__(
            self, self_address=str(self.context.skill_id), role_from_first_message=_role_from_first_message
        )
