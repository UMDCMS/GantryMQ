class GpioClient():
    def __init__(self, rpc_client):
        super().__init__()

        self.rpc_client = rpc_client


    def run_gcode(self, gcode, attempt, waitack):
        self.rpc_client.call(
            "run-gcode",
            {"gcode": gcode, "attempt": attempt, "waitack": waitack},
            exchange="commands",
            routing_key="gcoder_queue",
        )

    def set_speed_limit(self, x, y, z):
        self.rpc_client.call(
            "set-speed-limit",
            {"x": x, "y": y, "z": z},
            exchange="commands",
            routing_key="gcoder_queue",
        )

    def move_to(self, x, y, z):
        self.rpc_client.call(
            "move-to",
            {"x": x, "y": y, "z": z},
            exchange="commands",
            routing_key="gcoder_queue",
        )

    def enable_stepper(self, x, y, z):
        self.rpc_client.call(
            "enable-stepper",
            {"x": x, "y": y, "z": z},
            exchange="commands",
            routing_key="gcoder_queue",
        )

    def disable_stepper(self, x, y, z):
        self.rpc_client.call(
            "disable-stepper",
            {"x": x, "y": y, "z": z},
            exchange="commands",
            routing_key="gcoder_queue",
        )

    def send_home(self, x, y, z):
        self.rpc_client.call(
            "send-home",
            {"x": x, "y": y, "z": z},
            exchange="commands",
            routing_key="gcoder_queue",
        )

    # Read-like functions
    def get_settings(self):
        self.rpc_client.call("get-settings", {}, exchange="data", routing_key="gcoder_data")

    def in_motion(self, x, y, z):
        self.rpc_client.call(
            "in-motion",
            {"x": x, "y": y, "z": z},
            exchange="data",
            routing_key="gcoder_data",
        )

    # Read-like data members (Should only be set via operation-functions)
    def get_opx(self):
        self.rpc_client.call("get-opx", {}, exchange="data", routing_key="gcoder_data")
  
    def get_opy(self):
        self.rpc_client.call("get-opy", {}, exchange="data", routing_key="gcoder_data")

    def get_opz(self):
        self.rpc_client.call("get-opz", {}, exchange="data", routing_key="gcoder_data")

    def get_cx(self):
        self.rpc_client.call("get-cx", {}, exchange="data", routing_key="gcoder_data")

    def get_cy(self):
        self.rpc_client.call("get-cy", {}, exchange="data", routing_key="gcoder_data")

    def get_cz(self):
        self.rpc_client.call("get-cz", {}, exchange="data", routing_key="gcoder_data")

    def get_vx(self):
        self.rpc_client.call("get-vx", {}, exchange="data", routing_key="gcoder_data")

    def get_vy(self):
        self.rpc_client.call("get-vy", {}, exchange="data", routing_key="gcoder_data")

    def get_vz(self):
        self.rpc_client.call("get-vz", {}, exchange="data", routing_key="gcoder_data")

    # Static methods - getterrs
    def get_max_x(self):
        self.rpc_client.call(
            "get-max-x",
            {},
            exchange="data",
            routing_key="gcoder_data",
        )

    def get_max_y(self):
        self.rpc_client.call(
            "get-max-y",
            {},
            exchange="data",
            routing_key="gcoder_data",
        )

    def get_max_z(self):
        self.rpc_client.call(
            "get-max-z",
            {},
            exchange="data",
            routing_key="gcoder_data",
        )

    # Static methods - setters
    def set_max_x(self, x):
        self.rpc_client.call(
            "set-max-x",
            {"x": x},
            exchange="commands",
            routing_key="gcoder_queue",
        )

    def set_max_y(self, y):
        self.rpc_client.call(
            "set-max-y",
            {"y": y},
            exchange="commands",
            routing_key="gcoder_queue",
        )

    def set_max_z(self, z):
        self.rpc_client.call(
            "set-max-z",
            {"z": z},
            exchange="commands",
            routing_key="gcoder_queue",
        )
