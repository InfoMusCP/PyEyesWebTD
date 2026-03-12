import os
import sys

from TDStoreTools import StorageManager
import TDFunctions as TDF


class XIMUExt:
    """
    Clean & organized XIMU extension
    """

    def __init__(self, ownerComp):
        self.ownerComp = ownerComp

        # --- PARAM REFERENCES ---
        self.params = op("parameter1")
        self.venv = self.params["Venv", 1].val
        self.device_number = int(self.params["Devicenumber", 1].val)

        # --- RUNTIME STATE ---
        self._connections = []
        # self._ping_response = None
        self.messages = None

        # Exposed dependency
        self._linear_acceleration = tdu.Dependency((0, 0, 0))

        # --- Environment setup (safe) ---
        self._ensure_python_env()

    # ----------------------------------------------------------------------
    # ENVIRONMENT
    # ----------------------------------------------------------------------

    def _ensure_python_env(self):
        """Add virtualenv site-packages to sys.path."""
        lib_dir = os.path.join(project.folder, self.venv, "Lib", "site-packages")
        lib_dir = os.path.normpath(lib_dir)

        if lib_dir not in sys.path:
            sys.path.insert(0, lib_dir)

    # ----------------------------------------------------------------------
    # PUBLIC PROPERTIES
    # ----------------------------------------------------------------------

    @property
    def LinearAcceleration(self):
        return self._linear_acceleration

    # ----------------------------------------------------------------------
    # CONNECTION MANAGEMENT
    # ----------------------------------------------------------------------

    def _connect(self):
        import ximu3

        self._close()  # Avoid duplicated connections

        announcer = ximu3.NetworkAnnouncement()
        self.messages = announcer.get_messages_after_short_delay()
        self._connections = []

        for message in self.messages:
            # print("Found device:", message.to_string())

            if int(str(message.ip_address).split(".")[3]) != self.device_number:
                continue

            info = message.to_udp_connection_info()
            connection = ximu3.Connection(info)

            if connection.open() != ximu3.RESULT_OK:
                raise Exception("Failed to open connection for " + info.to_string())

            # Ping to initialize device output
            ping_response = connection.ping()

            if ping_response.result != ximu3.RESULT_OK:
                raise Exception("Ping failed for " + info.to_string())

            # Register callback
            connection.add_linear_acceleration_callback(
                self._linear_acceleration_callback
            )

            # Device configuration
            self._send_command(connection, "ahrsMessageType", 3)
            self._send_command(connection, "ahrsMessageRateDivisor", 4)
            self._send_command(connection, "inertialMessageRateDivisor", 4)
            self._send_command(connection, "highGAccelerometerMessageRateDivisor", 32)

            self._connections.append(connection)

    def _close(self):
        for connection in self._connections:
            try:
                connection.close()
            except:
                pass
        self._connections = []

    # ----------------------------------------------------------------------
    # CALLBACKS
    # ----------------------------------------------------------------------

    def _linear_acceleration_callback(self, message):
        self._linear_acceleration.setVal(
            (message.acceleration_x,
             message.acceleration_y,
             message.acceleration_z)
        )

    # ----------------------------------------------------------------------
    # COMMAND SENDING
    # ----------------------------------------------------------------------

    def _send_command(self, connection, key, value=None):
        if value is None:
            value = "null"
        elif isinstance(value, bool):
            value = str(value).lower()
        elif isinstance(value, str):
            value = f"\"{value}\""
        else:
            value = str(value)

        command = f"{{\"{key}\":{value}}}"

        responses = connection.send_commands([command], 2, 500)

        if not responses:
            raise Exception(f"Unable to confirm command {command}")

        # prefix = f"{self._ping_response.device_name} {self._ping_response.serial_number}"
        # print(prefix, responses[0])

    # ----------------------------------------------------------------------
    # TOUCHDESIGNER PARAMETER CALLBACKS
    # ----------------------------------------------------------------------

    def par_exec_onValueChange(self, par):
        name = par.name
        value = par.eval()

        if name == "Devicenumber":
            self.device_number = int(value)

    def par_exec_onPulse(self, par):
        if par.name == "Connect":
            self._connect()
        elif par.name == "Close":
            self._close()
