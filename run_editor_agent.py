import asyncio
import logging
import warnings
import argparse
import json

from _agents import BaseGroupChatAgent
from _types import AppConfig, GroupChatMessage, MessageChunk, RequestToSpeak
from _utils import get_serializers, load_config, set_all_log_levels, export_metrics_to_csv
from unified_state_config import ONE_VAR_STATE, FIVE_VAR_STATE, TEN_VAR_STATE, FIFTY_VAR_STATE, HUNDRED_VAR_STATE
from autogen_core import (
    TypeSubscription,
)
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntime
from rich.console import Console
from rich.markdown import Markdown
from agent_timeslices import save_metrics_to_csv_and_cdfs
from _agents import export_metrics
from datetime import datetime

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="experiment_config.json", help="Path to the configuration file")
    return parser.parse_args()   
args = parse_args()

with open(args.config, "r") as f:
    config_data = json.load(f)

state_vars = config_data["state_vars"]

async def main(config: AppConfig, state_vars: dict):
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
            state_vars=state_vars,
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
    now = datetime.now()
    timestamp = now.strftime( "%Y-%m-%d_%H-%M")
    save_metrics_to_csv_and_cdfs(f"editor_metrics_state_traced_1var_{timestamp}")
    export_metrics_to_csv(export_metrics, f"editor_metrics_state_traced_export_1var_{timestamp}.csv")


if __name__ == "__main__":
    set_all_log_levels(logging.ERROR)
    warnings.filterwarnings("ignore", category=UserWarning, message="Resolved model mismatch.*")
    asyncio.run(main(load_config(), state_vars))
