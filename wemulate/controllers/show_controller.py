from typing import List

import tabulate
import typer
from rich.console import Console
from rich.table import Table

import wemulate.controllers.common as common
import wemulate.ext.utils as utils
import wemulate.ext.settings as settings
from wemulate.core.database.models import ConnectionModel, ParameterModel
from wemulate.utils.rendering import rendering

console = Console()
err_console = Console(stderr=True)


CONNECTION_HEADERS: List[str] = [
    "NAME",
    "1. INTERFACE",
    "2. INTERFACE",
    "PARAMETERS",
]
SHOW_CONNECTION_TEMPLATE_FILE: str = "show_connection.jinja2"
INTERFACE_HEADER = ["NAME", "PHYSICAL", "IP", "MAC"]


def _get_parameters_to_render(parameters: List[ParameterModel]) -> List[ParameterModel]:
    parameters_to_render: List[ParameterModel] = parameters.copy()
    for i, current_parameter in enumerate(parameters):
        for parameter_to_check in parameters[i + 1 :]:
            if (
                parameter_to_check.parameter_name == current_parameter.parameter_name
                and parameter_to_check.value == current_parameter.value
            ):
                parameters_to_render[
                    parameters_to_render.index(current_parameter)
                ].direction = None
                parameters_to_render.remove(parameter_to_check)
                break
    return parameters_to_render


def _populate_connection_table(connection: ConnectionModel, table: Table) -> None:
    parameters: List[ParameterModel] = _get_parameters_to_render(connection.parameters)
    table.add_row(
        connection.connection_name,
        connection.first_logical_interface.logical_name,
        connection.second_logical_interface.logical_name,
        rendering(
            {"parameters": parameters},
            SHOW_CONNECTION_TEMPLATE_FILE,
        ),
    )


def _construct_interface_data_to_render(
    render_data: List, interface: str, is_mgmt_interface: bool = False
) -> None:
    data_to_append: List = []
    if not is_mgmt_interface:
        data_to_append.append(
            utils.get_logical_interface_by_physical_name(interface).logical_name,
        )
    data_to_append.extend(
        [
            interface,
            settings.get_interface_ip(interface),
            settings.get_interface_mac_address(interface),
        ]
    )
    render_data.append(data_to_append)


app = typer.Typer(help="show specific information")


@app.command(help="show specific connection information", no_args_is_help=True)
def connection(connection_name: str = common.CONNECTION_NAME_ARGUMENT):
    common.check_if_connection_exists_in_db(connection_name)
    connection: ConnectionModel = utils.get_connection_by_name(connection_name)
    table = Table(title="Connection Information")
    for header in CONNECTION_HEADERS:
        table.add_column(header)
    render_data: List[str] = []
    _populate_connection_table(connection, render_data)
    console.print(table)


@app.command(help="show overview about all connections")
def connections():
    connections: List[ConnectionModel] = utils.get_connection_list()
    if not connections:
        err_console.print("There are no connections")
        raise typer.Exit(1)
    else:
        render_data: List = []
        for connection in connections:
            _construct_connection_data_to_render(connection, render_data)
        console.print(
            tabulate.tabulate(render_data, headers=CONNECTION_HEADERS, tablefmt="grid")
        )
    raise typer.Exit()


@app.command(help="show specific interface information", no_args_is_help=True)
def interface(interface_name: str = typer.Argument(..., help="name of the interface")):
    if not interface_name in settings.get_non_mgmt_interfaces():
        err_console.print("The given interface is not available")
        raise typer.Exit(1)
    else:
        render_data: List = []
        _construct_interface_data_to_render(
            render_data,
            interface_name,
        )
        console.print(
            tabulate.tabulate(render_data, headers=INTERFACE_HEADER, tablefmt="grid")
        )
    raise typer.Exit()


@app.command(help="show overview about all interfaces")
def interfaces():
    render_data: List = []
    for interface in settings.get_non_mgmt_interfaces():
        _construct_interface_data_to_render(render_data, interface)
    console.print(
        tabulate.tabulate(render_data, headers=INTERFACE_HEADER, tablefmt="grid")
    )
    raise typer.Exit()


@app.command(help="show overview about all management interfaces")
def mgmt_interfaces():
    mgmt_interfaces: List[str] = settings.get_mgmt_interfaces()
    render_data: List = []
    for interface in mgmt_interfaces:
        _construct_interface_data_to_render(
            render_data, interface, is_mgmt_interface=True
        )
    console.print(
        tabulate.tabulate(render_data, headers=["NAME", "IP", "MAC"], tablefmt="grid")
    )
    raise typer.Exit()
