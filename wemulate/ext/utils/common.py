import wemulate.core.database.utils as dbutils
import wemulate.utils.tcconfig as tcutils
from typing import Dict, Optional
from wemulate.core.database.models import (
    BANDWIDTH,
    INCOMING,
    JITTER,
    DELAY,
    OUTGOING,
    PACKET_LOSS,
    PARAMETERS,
    ConnectionModel,
)


def _set_specific_parameter(
    connection: ConnectionModel,
    parameter_name: str,
    parameters: Dict[str, int],
    current_parameters: Dict[str, Dict[str, int]],
    direction: str,
) -> None:
    current_parameters[direction][parameter_name] = parameters[parameter_name]
    dbutils.create_or_update_parameter(
        connection.connection_id,
        parameter_name,
        parameters[parameter_name],
        direction,
    )


def create_or_update_parameters_in_db(
    connection: ConnectionModel,
    parameters: Dict[str, int],
    direction: Optional[str],
    current_parameters=None,
) -> Dict[str, Dict[str, int]]:
    """
    Creates and updates parameters in the database.

    Args:
        connection: Connection object on which the updates should be made.
        parameters: Parameters which should be updated.
        direction: Direction on which the parameter should be applied (bidirectional if None)
        current_parameters: Current parameters which should be updated.

    Returns:
        Returns the current_parameters which are set in the database.
    """
    current_parameters: Dict[str, Dict[str, int]] = current_parameters or {
        OUTGOING: {},
        INCOMING: {},
    }
    for direction in [INCOMING, OUTGOING] if direction is None else [direction]:
        for parameter_name in PARAMETERS:
            if parameter_name in parameters:
                _set_specific_parameter(
                    connection,
                    parameter_name,
                    parameters,
                    current_parameters,
                    direction,
                )
    return current_parameters


def set_parameters_with_tc(
    connection: ConnectionModel, parameters: Dict[str, int], direction: Optional[str]
):
    """
    Set parameters on the host system on the given connection.

    Args:
        connection: Connection object on which the updates should be made.
        parameters: Parameters which should be configured.
        direction: Direction on which the parameter should be applied (bidirectional if None)

    Returns:
        None
    """
    tcutils.set_parameters(
        connection.connection_name,
        dbutils.get_physical_interface_by_logical_interface_id(
            connection.first_logical_interface_id
        ).physical_name,
        parameters,
        direction,
    )


def _delete_bandwidth(
    parameters: Dict[str, int],
    current_parameters: Dict[str, int],
    connection: ConnectionModel,
) -> None:
    if BANDWIDTH in parameters and BANDWIDTH in current_parameters:
        current_parameters.pop(BANDWIDTH)
        dbutils.delete_parameter_on_connection_id(
            connection.connection_id,
            BANDWIDTH,
        )


def _delete_jitter(
    parameters: Dict[str, int],
    current_parameters: Dict[str, int],
    connection: ConnectionModel,
) -> None:
    if JITTER in parameters and JITTER in current_parameters:
        current_parameters.pop(JITTER)
        dbutils.delete_parameter_on_connection_id(connection.connection_id, JITTER)


def _delete_delay(
    parameters: Dict[str, int],
    current_parameters: Dict[str, int],
    connection: ConnectionModel,
) -> None:
    if DELAY in parameters and DELAY in current_parameters:
        current_parameters.pop(DELAY)
        dbutils.delete_parameter_on_connection_id(connection.connection_id, DELAY)


def _delete_packet_loss(
    parameters: Dict[str, int],
    current_parameters: Dict[str, int],
    connection: ConnectionModel,
) -> None:
    if PACKET_LOSS in parameters and PACKET_LOSS in current_parameters:
        current_parameters.pop(PACKET_LOSS)
        dbutils.delete_parameter_on_connection_id(
            connection.connection_id,
            PACKET_LOSS,
        )


def delete_parameters_in_db(
    parameters: Dict[str, int],
    current_parameters: Dict[str, int],
    connection: ConnectionModel,
) -> Dict[str, int]:
    """
    Delete specific parameters in db.

    Args:
        parameters: Parameters which should be deleted.
        current_parameters: The current parameters on the connection.
        connection: Connection object on which the updates should be made.

    Returns:
        Returns the current parameters in the database.
    """
    _delete_bandwidth(parameters, current_parameters, connection)
    _delete_jitter(parameters, current_parameters, connection)
    _delete_delay(parameters, current_parameters, connection)
    _delete_packet_loss(parameters, current_parameters, connection)
    return current_parameters
