# ------------------------------------------------------------------------------
#
#   Copyright 2023 eightballer
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

"""This package contains a scaffold of a behaviour."""

import json
from subprocess import Popen
from pathlib import Path
import subprocess
import sys
from typing import cast

import psutil
from aea.skills.behaviours import TickerBehaviour

from packages.eightballer.skills.rust_broker.dialogues import PrometheusDialogues, ShellCommandDialogues
from packages.eightballer.protocols.prometheus.message import PrometheusMessage
from packages.eightballer.protocols.shell_command.message import ShellCommandMessage
from packages.eightballer.connections.prometheus.connection import (
    PUBLIC_ID as PROM_CONNECTION_ID,
)
from packages.eightballer.connections.shell_command.connection import (
    CONNECTION_ID as SHELL_CONNECTION_ID,
)


class PrometheusBehaviour(TickerBehaviour):
    """This class scaffolds a behaviour."""

    def setup(self) -> None:
        """Implement the setup."""
        self.context.logger.info("setting up AdvancedDataRequestBehaviour")

        prom_dialogues = cast(PrometheusDialogues, self.context.prometheus_dialogues)

        if prom_dialogues.enabled:
            for metric in prom_dialogues.metrics:
                metric_name = metric["name"]
                self.context.logger.info(f"Adding Prometheus metric: {metric_name}")
                self.add_prometheus_metric(
                    metric_name,
                    metric["type"],
                    metric["description"],
                    dict(metric["labels"]),
                )

        self.started = False
        self.error = None


    def act(self) -> None:
        """Implement the act."""


        if self.error is not None:
            self.context.logger.error(self.error)
            sys.exit(1)
            return
        if not self.started:
            self.create_rust_process_message()
            self.started = True

        memory_usage = psutil.Process().memory_info().rss / 1024**2
        # update prometheus metric
        self.update_prometheus_metric(
            metric_name="memory_usage",
            update_func="set",
            value=memory_usage,
            labels={"agent_address": self.context.agent_address},
        )

        # get cpu usage
        cpu_usage = psutil.cpu_percent()
        self.update_prometheus_metric(
            metric_name="cpu_usage",
            update_func="set",
            value=cpu_usage,
            labels={"agent_address": self.context.agent_address},
        )


    def __init__(self, **kwargs):
        """Initialize the behaviour."""
        tick_interval = kwargs.pop("tick_interval", 1.0)
        super().__init__(tick_interval=tick_interval, **kwargs)

    def teardown(self) -> None:
        """Implement the task teardown."""

    def add_prometheus_metric(
        self,
        metric_name: str,
        metric_type: str,
        description: str,
        labels: dict[str, str],
    ) -> None:
        """Add a prometheus metric."""

        prom_dialogues = cast(PrometheusDialogues, self.context.prometheus_dialogues)

        message, _ = prom_dialogues.create(
            counterparty=str(PROM_CONNECTION_ID),
            performative=PrometheusMessage.Performative.ADD_METRIC,
            type=metric_type,
            title=metric_name,
            description=description,
            labels=labels,
        )

        self.context.outbox.put_message(message=message)

    def update_prometheus_metric(
        self,
        metric_name: str,
        update_func: str,
        value: float,
        labels: dict[str, str],
    ) -> None:
        """Update a prometheus metric."""

        # context
        prom_dialogues = cast(PrometheusDialogues, self.context.prometheus_dialogues)

        # prometheus update message
        message, _ = prom_dialogues.create(
            counterparty=str(PROM_CONNECTION_ID),
            performative=PrometheusMessage.Performative.UPDATE_METRIC,
            title=metric_name,
            callable=update_func,
            value=value,
            labels=labels,
        )

        # send message
        self.context.outbox.put_message(message=message)


    def create_rust_process_message(self) -> None:
        """Create the rust process."""
        shell_dialogues = cast(ShellCommandDialogues, self.context.shell_command_dialogues)

        self.context.logger.info("Creating the rust process.")


        msg, _ = shell_dialogues.create(
            counterparty=str(SHELL_CONNECTION_ID),
            performative=ShellCommandMessage.Performative.EXECUTE_COMMAND,
            command="./broker",
            args=("--broker", "--port", "8080", "--host", "0.0.0.0"),
            options={},
            env_vars=json.dumps({
                "RUST_LOG": "DEBUG",
            }).encode("utf-8"),
        )
        self.context.outbox.put_message(message=msg)
