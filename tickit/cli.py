import asyncio

import click
from click.core import Context

from tickit.core.components.component import create_simulations
from tickit.core.lifetime_runnable import run_all_forever
from tickit.core.management.event_router import InverseWiring
from tickit.core.management.schedulers.master import MasterScheduler
from tickit.core.state_interfaces.state_interface import get_interface, interfaces
from tickit.utils.configuration.loading import read_configs


@click.group(invoke_without_command=True)
@click.version_option()
@click.pass_context
def main(ctx: Context):

    if ctx.invoked_subcommand is None:
        click.echo(main.get_help(ctx))


@main.command(help="run a single simulated device")
@click.argument("device")
@click.argument("config_path")
@click.option("--backend", default="kafka", type=click.Choice(list(interfaces(True))))
def device(config_path, device, backend):
    configs = read_configs(config_path)
    config = next(config for config in configs if config.name == device)
    device_simulations = create_simulations([config], *get_interface(backend))
    asyncio.run(run_all_forever(device_simulations))


@main.command(help="run the simulation scheduler")
@click.argument("config_path")
@click.option("--backend", default="kafka", type=click.Choice(list(interfaces(True))))
def scheduler(config_path, backend):
    configs = read_configs(config_path)
    inverse_wiring = InverseWiring.from_component_configs(configs)
    scheduler = MasterScheduler(inverse_wiring, *get_interface(backend))
    asyncio.run(run_all_forever([scheduler]))


@main.command(help="run a collection of devices with a scheduler")
@click.argument("config_path")
@click.option(
    "--backend", default="internal", type=click.Choice(list(interfaces(False)))
)
def all(config_path, backend):
    configs = read_configs(config_path)
    inverse_wiring = InverseWiring.from_component_configs(configs)
    scheduler = MasterScheduler(inverse_wiring, *get_interface(backend))
    device_simulations = create_simulations(configs, *get_interface(backend))
    asyncio.run(run_all_forever([scheduler, *device_simulations]))
