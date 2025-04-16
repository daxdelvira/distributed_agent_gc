import asyncio
import logging
import warnings

from _agents import BaseGroupChatAgent, export_metrics
from _types import AppConfig, GroupChatMessage, MessageChunk, RequestToSpeak
from _utils import get_serializers, load_config, set_all_log_levels, export_metrics_to_csv
from autogen_core import (
    TypeSubscription,
)
from autogen_ext.models.openai import OpenAIChatCompletionClient
from autogen_ext.runtimes.grpc import GrpcWorkerAgentRuntime
from rich.console import Console
from rich.markdown import Markdown
from agent_timeslices import save_metrics_to_csv_and_cdfs
from datetime import datetime
from experiment_context import ExperimentContext
import argparse
import json
from unified_state_config import ONE_VAR_STATE, FIVE_VAR_STATE, TEN_VAR_STATE, FIFTY_VAR_STATE, HUNDRED_VAR_STATE
from _tracking_utils import MemorySampler

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, default="experiment_config.json", help="Path to the configuration file")
    return parser.parse_args()   
args = parse_args()

with open(args.config, "r") as f:
    config_data = json.load(f)

state_vars = config_data["state_vars"]
experiment = ExperimentContext(config_data["experiment"])

async def main(config: AppConfig, state_vars: dict) -> None:
    set_all_log_levels(logging.ERROR)
    writer_agent_runtime = GrpcWorkerAgentRuntime(host_address=config.host.address)
    writer_agent_runtime.add_message_serializer(get_serializers([RequestToSpeak, GroupChatMessage, MessageChunk]))  # type: ignore[arg-type]
    await asyncio.sleep(3)
    Console().print(Markdown("Starting **`Writer Agent`**"))

    await writer_agent_runtime.start()
    if experiment.per_agent_memory:
        memory_sampler = MemorySampler(sample_interval=5.0)
        sampling_task = asyncio.create_task(memory_sampler.start_sampling())
    else:
        memory_sampler = None
        sampling_task = None
    writer_agent_type = await BaseGroupChatAgent.register(
        writer_agent_runtime,
        config.writer_agent.topic_type,
        lambda: BaseGroupChatAgent(
            description=config.writer_agent.description,
            group_chat_topic_type=config.group_chat_manager.topic_type,
            system_message=config.writer_agent.system_message,
            model_client=OpenAIChatCompletionClient(**config.client_config),
            state_vars=state_vars,
            experiment=experiment,
            ui_config=config.ui_agent,
        ),
    )
    await writer_agent_runtime.add_subscription(
        TypeSubscription(topic_type=config.writer_agent.topic_type, agent_type=writer_agent_type.type)
    )
    await writer_agent_runtime.add_subscription(
        TypeSubscription(topic_type=config.group_chat_manager.topic_type, agent_type=config.writer_agent.topic_type)
    )

    await writer_agent_runtime.stop_when_signal()
    now = datetime.now()
    timestamp = now.strftime( "%Y-%m-%d_%H-%M")

    if memory_sampler:
        await memory_sampler.stop_sampling()
        await sampling_task
        avg_rss = memory_sampler.average_rss()
        memory_sampler.export_to_csv(filename=f"writer_memory_trace{timestamp}.csv", agent_label="writer_agent")
    save_metrics_to_csv_and_cdfs(f"writer_metrics_state_traced_1var_{timestamp}")
    export_metrics_to_csv(export_metrics, f"writer_metrics_state_traced_export_1var_{timestamp}.csv")

if __name__ == "__main__":
    set_all_log_levels(logging.ERROR)
    warnings.filterwarnings("ignore", category=UserWarning, message="Resolved model mismatch.*")
    asyncio.run(main(load_config()))
