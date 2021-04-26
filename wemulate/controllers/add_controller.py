from wemulate.core.database.models import DEFAULT_PARAMETERS, PARAMETERS
from wemulate.utils.tcconfig import add_connection, set_parameters
from wemulate.core.exc import WEmulateExecutionError, WEmulateValidationError
from wemulate.core.database.utils import (
    connection_exists,
    create_connection,
    create_or_update_parameter,
    get_connection,
    get_logical_interface_by_name,
    get_active_profile,
    get_device,
    get_physical_interface_for_logical_name,
    get_physical_interface_for_logical_id,
    get_specific_parameter_value_for_connection_id,
)
from cement import Controller, ex


class AddController(Controller):
    class Meta:
        label = "add"
        help = "add a new connection or parameter"
        stacked_on = "base"
        stacked_type = "nested"

    @ex(
        help="add a new conneciton",
        arguments=[
            (
                ["-n", "--connection-name"],
                {
                    "help": "name of the connection which should be created",
                    "action": "store",
                    "dest": "connection_name",
                },
            ),
            (
                ["-i", "--interfaces"],
                {
                    "help": "list of two interfaces which should be added to the connection (LAN-A,LAN-B)",
                    "action": "store",
                    "dest": "interfaces_list",
                },
            ),
        ],
    )
    def connection(self):
        if not self.app.pargs.connection_name:
            self.app.log.info("please define a connection name | -n name")
            self.app.close()
        if self.app.pargs.interfaces_list:
            interfaces_list = self.app.pargs.interfaces_list.split(",")
            if len(interfaces_list) != 2:
                self.app.log.info("you have to define two interfaces | -i LAN-A,LAN-B")
                self.app.close()
            else:
                try:
                    physical_interface1_name = get_physical_interface_for_logical_name(
                        interfaces_list[0]
                    ).physical_name
                    physical_interface2_name = get_physical_interface_for_logical_name(
                        interfaces_list[1]
                    ).physical_name

                    add_connection(
                        self.app.pargs.connection_name,
                        physical_interface1_name,
                        physical_interface2_name,
                    )
                    create_connection(
                        self.app.pargs.connection_name,
                        get_logical_interface_by_name(interfaces_list[0]),
                        get_logical_interface_by_name(interfaces_list[1]),
                        get_active_profile(get_device(1)),
                    )
                    self.app.log.info("successfully added a new connection")
                except WEmulateValidationError as e:
                    self.app.log.error(f"The {e} already exists in a connection")
                except WEmulateExecutionError as e:
                    self.app.log.error("Exec error")
        else:
            self.app.log.info("please define the interfaces | -i LAN-A,LAN-B")
            self.app.close()

    @ex(
        help="add parameter on a specific connection, previously added parameters will not be changed",
        arguments=[
            (
                ["-n", "--connection-name"],
                {
                    "help": "name of the connection on which the parameters should be applied",
                    "action": "store",
                    "dest": "connection_name",
                },
            ),
            (
                ["-b", "--bandwidth"],
                {
                    "help": "bandwidth parameter in mbps",
                    "action": "store",
                    "dest": "bandwidth",
                },
            ),
            (
                ["-j", "--jitter"],
                {"help": "jitter parameter", "action": "store", "dest": "jitter"},
            ),
            (
                ["-d", "--delay"],
                {"help": "delay parameter in ms", "action": "store", "dest": "delay"},
            ),
            (
                ["-l", "--packet-loss"],
                {
                    "help": "packet loss parameter in percentage",
                    "action": "store",
                    "dest": "packet_loss",
                },
            ),
            # TODO specify parameter description (e.g in ms. in percent etc.)
        ],
    )
    def parameter(self):
        if not self.app.pargs.connection_name:
            self.app.log.info("please define a connection name | -n name")
            self.app.close()
        if (
            not self.app.pargs.bandwidth
            and not self.app.pargs.jitter
            and not self.app.pargs.delay
            and not self.app.pargs.packet_loss
        ):
            self.app.log.info(
                "please specifiy at least one parameter to set on the connection"
            )
            self.app.close()
        if connection_exists(self.app.pargs.connection_name):
            connection = get_connection(self.app.pargs.connection_name)
            parameters = {}
            for param in PARAMETERS:
                parameter_value = get_specific_parameter_value_for_connection_id(
                    connection.connection_id, param
                )
                if parameter_value:
                    parameters[param] = parameter_value
            if self.app.pargs.bandwidth:
                parameters["bandwidth"] = self.app.pargs.bandwidth
                create_or_update_parameter(
                    connection.connection_id, "bandwidth", self.app.pargs.bandwidth
                )
            if self.app.pargs.jitter:
                parameters["jitter"] = self.app.pargs.jitter
                create_or_update_parameter(
                    connection.connection_id, "jitter", self.app.pargs.jitter
                )
            if self.app.pargs.delay:
                parameters["delay"] = self.app.pargs.delay
                create_or_update_parameter(
                    connection.connection_id, "delay", self.app.pargs.delay
                )
            if self.app.pargs.packet_loss:
                parameters["packet_loss"] = self.app.pargs.packet_loss
                create_or_update_parameter(
                    connection.connection_id, "packet_loss", self.app.pargs.packet_loss
                )
            set_parameters(
                get_physical_interface_for_logical_id(
                    get_connection(
                        self.app.pargs.connection_name
                    ).first_logical_interface_id
                ).physical_name,
                parameters,
            )
            self.app.log.info(
                f"successfully added parameters to connection {self.app.pargs.connection_name}"
            )
        else:
            self.app.log.info(
                f"there is no connection {self.app.pargs.connection_name} please create one first"
            )
            self.app.close()
