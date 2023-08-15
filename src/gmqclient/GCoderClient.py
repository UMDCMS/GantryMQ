from client import RpcClient


class GpioClient(RpcClient):
    def __init__(self):
        super().__init__()

    def run_gcode(self, gcode, attempt, waitack):
        self.call(
            "run-gcode",
            {"gcode": gcode, "attempt": attempt, "waitack": waitack},
            exchange="commands",
            routing_key="gcoder_queue",
        )

    def set_speed_limit(self, x, y, z):
        self.call(
            "set-speed-limit",
            {"x": x, "y": y, "z": z},
            exchange="commands",
            routing_key="gcoder_queue",
        )

    def move_to(self, x, y, z):
        self.call(
            "move-to",
            {"x": x, "y": y, "z": z},
            exchange="commands",
            routing_key="gcoder_queue",
        )

    def enable_stepper(self, x, y, z):
        self.call(
            "enable-stepper",
            {"x": x, "y": y, "z": z},
            exchange="commands",
            routing_key="gcoder_queue",
        )

    def disable_stepper(self, x, y, z):
        self.call(
            "disable-stepper",
            {"x": x, "y": y, "z": z},
            exchange="commands",
            routing_key="gcoder_queue",
        )

    def send_home(self, x, y, z):
        self.call(
            "send-home",
            {"x": x, "y": y, "z": z},
            exchange="commands",
            routing_key="gcoder_queue",
        )

    # Read-like functions
    def get_settings(self):
        self.call("get-settings", {}, exchange="data", routing_key="gcoder_data")

    def in_motion(self, x, y, z):
        self.call(
            "in-motion",
            {"x": x, "y": y, "z": z},
            exchange="data",
            routing_key="gcoder_data",
        )

    # Read-like data members (Should only be set via operation-functions)
    def get_opx(self):
        self.call("get-opx", {}, exchange="data", routing_key="gcoder_data")
  
    def get_opy(self):
        self.call("get-opy", {}, exchange="data", routing_key="gcoder_data")

    def get_opz(self):
        self.call("get-opz", {}, exchange="data", routing_key="gcoder_data")

    def get_cx(self):
        self.call("get-cx", {}, exchange="data", routing_key="gcoder_data")

    def get_cy(self):
        self.call("get-cy", {}, exchange="data", routing_key="gcoder_data")

    def get_cz(self):
        self.call("get-cz", {}, exchange="data", routing_key="gcoder_data")

    def get_vx(self):
        self.call("get-vx", {}, exchange="data", routing_key="gcoder_data")

    def get_vy(self):
        self.call("get-vy", {}, exchange="data", routing_key="gcoder_data")

    def get_vz(self):
        self.call("get-vz", {}, exchange="data", routing_key="gcoder_data")

    # Static methods - getterrs
    def get_max_x(self):
        self.call(
            "get-max-x",
            {},
            exchange="data",
            routing_key="gcoder_data",
        )

    def get_max_y(self):
        self.call(
            "get-max-y",
            {},
            exchange="data",
            routing_key="gcoder_data",
        )

    def get_max_z(self):
        self.call(
            "get-max-z",
            {},
            exchange="data",
            routing_key="gcoder_data",
        )

    # Static methods - setters
    def set_max_x(self, x):
        self.call(
            "set-max-x",
            {"x": x},
            exchange="commands",
            routing_key="gcoder_queue",
        )

    def set_max_y(self, y):
        self.call(
            "set-max-y",
            {"y": y},
            exchange="commands",
            routing_key="gcoder_queue",
        )

    def set_max_z(self, z):
        self.call(
            "set-max-z",
            {"z": z},
            exchange="commands",
            routing_key="gcoder_queue",
        )
