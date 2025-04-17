import asyncio
import logging
import warnings
import argparse
import json
import signal
import sys

from _agents import BaseGroupChatAgent
from _types import AppConfig, GroupChatMessage, MessageChunk, RequestToSpeak
from _utils import get_serializers, load_config, set_all_log_levels
from unified_state_config import ONE_VAR_STATE, FIVE_VAR_STATE, TEN_VAR_STATE, FIFTY_VAR_STATE, HUNDRED_VAR_STATE
from autogen_core import (
    TypeSubscription,
)
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntime
from rich.console import Console
from rich.markdown import Markdown

from datetime import datetime
from experiment_context import ExperimentContext
from agent_experiment_logger import AgentExperimentLogger

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="experiment_config.json", help="Path to the configuration file")
    return parser.parse_args()   

def handle_sigint(signum, frame):
    print("[Editor Agent] Caught Ctrl+C — exporting metrics before exit...")
    logger.export_all()
    sys.exit(0)

async def main(config: AppConfig, experiment: ExperimentContext, logger: AgentExperimentLogger, state_vars: dict, state_server_url: str):
    set_all_log_levels(logging.ERROR)
    editor_agent_runtime = GrpcWorkerAgentRuntime(host_address=config.host.address)
    editor_agent_runtime.add_message_serializer(get_serializers([RequestToSpeak, GroupChatMessage, MessageChunk]))  # type: ignore[arg-type]
    await asyncio.sleep(4)

    Console().print(Markdown("Starting **`Editor Agent`**"))

    await editor_agent_runtime.start()
    await logger.track_memory()

    model_client = OpenAIChatCompletionClient(**config.client_config)
    editor_agent_type = await BaseGroupChatAgent.register(
        editor_agent_runtime,
        config.editor_agent.topic_type,
        lambda: BaseGroupChatAgent(
            description=config.editor_agent.description,
            group_chat_topic_type=config.group_chat_manager.topic_type,
            system_message=config.editor_agent.system_message,
            model_client=model_client,
            state_vars=state_vars,
            experiment=experiment,
            state_server_url=state_server_url,
            ui_config=config.ui_agent,
        ),
    )
    await editor_agent_runtime.add_subscription(
        TypeSubscription(topic_type=config.editor_agent.topic_type, agent_type=editor_agent_type.type)
    )
    await editor_agent_runtime.add_subscription(
        TypeSubscription(topic_type=config.group_chat_manager.topic_type, agent_type=editor_agent_type.type)
    )

    await editor_agent_runtime.stop_when_signal()
    await logger.stop_memory()
    logger.export_all()
    await model_client.close()


if __name__ == "__main__":
    set_all_log_levels(logging.ERROR)
    warnings.filterwarnings("ignore", category=UserWarning, message="Resolved model mismatch.*")
    args = parse_args()

    with open(args.config, "r") as f:
        config_data = json.load(f)

    experiment = ExperimentContext(config_data["experiment"])
    state_vars = config_data["state_vars"]
    state_server_url = config_data["state_server_url"]
    logger = AgentExperimentLogger(experiment, agent_label="editor_agent")

    signal.signal(signal.SIGINT, handle_sigint)
    asyncio.run(main(load_config(), experiment, logger, state_vars, state_server_url))
