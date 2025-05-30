import asyncio
import logging
import warnings

from _agents import BaseGroupChatAgent
from _types import AppConfig, GroupChatMessage, MessageChunk, RequestToSpeak
from _utils import get_serializers, load_config, set_all_log_levels
from autogen_core import (
    TypeSubscription,
)
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntime
from rich.console import Console
from rich.markdown import Markdown
from agent_timeslices import save_metrics_to_csv_and_cdfs


async def main(config: AppConfig):
    set_all_log_levels(logging.ERROR)
    editor_agent_runtime = GrpcWorkerAgentRuntime(host_address=config.host.address)
    editor_agent_runtime.add_message_serializer(get_serializers([RequestToSpeak, GroupChatMessage, MessageChunk]))  # type: ignore[arg-type]
    await asyncio.sleep(4)
    Console().print(Markdown("Starting **`Editor Agent`**"))
    await editor_agent_runtime.start()
    model_client = OpenAIChatCompletionClient(**config.client_config)
    editor_agent_type = await BaseGroupChatAgent.register(
        editor_agent_runtime,
        config.editor_agent.topic_type,
        lambda: BaseGroupChatAgent(
            description=config.editor_agent.description,
            group_chat_topic_type=config.group_chat_manager.topic_type,
            system_message=config.editor_agent.system_message,
            model_client=model_client,
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
    await model_client.close()
    save_metrics_to_csv_and_cdfs("editor_metrics")


if __name__ == "__main__":
    set_all_log_levels(logging.ERROR)
    warnings.filterwarnings("ignore", category=UserWarning, message="Resolved model mismatch.*")
    asyncio.run(main(load_config()))