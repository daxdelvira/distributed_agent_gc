import asyncio
import logging
import warnings

from _agents import GroupChatManager, publish_message_to_ui, publish_message_to_ui_and_backend
from _types import AppConfig, GroupChatMessage, MessageChunk, RequestToSpeak
from _utils import get_serializers, load_config, set_all_log_levels
from autogen_core import (
    TypeSubscription,
)
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntime
from rich.console import Console
from rich.markdown import Markdown

import argparse
import json
from experiment_context import ExperimentContext
from agent_experiment_logger import AgentExperimentLogger


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="experiment_config.json", help="Path to the configuration file")
    return parser.parse_args()


async def main(config: AppConfig, experiment: ExperimentContext, logger: AgentExperimentLogger):
    set_all_log_levels(logging.ERROR)
    group_chat_manager_runtime = GrpcWorkerAgentRuntime(host_address=config.host.address)

    group_chat_manager_runtime.add_message_serializer(get_serializers([RequestToSpeak, GroupChatMessage, MessageChunk]))  # type: ignore[arg-type]
    await asyncio.sleep(1)
    Console().print(Markdown("Starting **`Group Chat Manager`**"))
    await group_chat_manager_runtime.start()
    await logger.track_memory()
    set_all_log_levels(logging.ERROR)

    model_client = OpenAIChatCompletionClient(**config.client_config)

    group_chat_manager_type = await GroupChatManager.register(
        group_chat_manager_runtime,
        "group_chat_manager",
        lambda: GroupChatManager(
            model_client=model_client,
            participant_topic_types=[config.writer_agent.topic_type, config.editor_agent.topic_type],
            participant_descriptions=[config.writer_agent.description, config.editor_agent.description],
            max_rounds=config.group_chat_manager.max_rounds,
            ui_config=config.ui_agent,
        ),
    )

    await group_chat_manager_runtime.add_subscription(
        TypeSubscription(topic_type=config.group_chat_manager.topic_type, agent_type=group_chat_manager_type.type)
    )

    await asyncio.sleep(5)

    await publish_message_to_ui(
        runtime=group_chat_manager_runtime,
        source="System",
        user_message="[ **Due to responsible AI considerations of this sample, group chat manager is sending an initiator message on behalf of user** ]",
        ui_config=config.ui_agent,
    )
    await asyncio.sleep(3)

    user_message: str = "Please write a short story about the gingerbread in halloween!"
    Console().print(f"Simulating User input in group chat topic:\n\t'{user_message}'")

    await publish_message_to_ui_and_backend(
        runtime=group_chat_manager_runtime,
        source="User",
        user_message=user_message,
        ui_config=config.ui_agent,
        group_chat_topic_type=config.group_chat_manager.topic_type,
    )

    await group_chat_manager_runtime.stop_when_signal()
    await logger.stop_memory()
    logger.export_all()
    await model_client.close()
    
    Console().print("Manager left the chat!")
    


if __name__ == "__main__":
    set_all_log_levels(logging.ERROR)
    warnings.filterwarnings("ignore", category=UserWarning, message="Resolved model mismatch.*")
    args = parse_args()

    with open(args.config, "r") as f:
        config_data = json.load(f)

    experiment = ExperimentContext(config_data["experiment"])
    logger = AgentExperimentLogger(experiment, agent_label="group_chat_manager")
    asyncio.run(main(load_config(), experiment, logger))


