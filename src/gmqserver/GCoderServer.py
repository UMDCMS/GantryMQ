# TODO:
# - Add logging add a way to return values for all commands
# - have getters relate to the data exchange
# -  have setters relate to the commands exchange

import pika
import json

from server import RpcServer
import cmod.gcoder as gcoder

class GCoderServer(RpcServer):
  def __init__(self):
    super().__init__()

    self.gcoder = gcoder.GCoder.instance()

    self.rpc_commands = {}
    self.data_methods = {}

    self.register_commands()
    self.register_data_methods()

  def register_commands(self):
    self.channel.exchange_declare(exchange="commands", exchange_type="direct")
    self.channel.queue_declare(queue="gcoder_queue", exclusive=True)
    self.channel.queue_bind(
      exchange="commands",
      queue="gcoder_queue",
      routing_key="gcoder_queue",
    )

    self.channel.basic_qos(prefetch_count=1)
    self.channel.basic_consume(
      queue="gcoder_queue",
      on_message_callback=self.on_request_command_aux,
    )

    self.rpc_commands.__setitem__("run-gcode", self.gcoder.run_gcode)
    self.rpc_commands.__setitem__(
      "set-speed-limit", self.gcoder.set_speed_limit
    )
    self.rpc_commands.__setitem__("move-to", self.gcoder.moveto)
    self.rpc_commands.__setitem__(
      "enable-stepper", self.gcoder.enablestepper
    )
    self.rpc_commands.__setitem__(
      "disable-stepper", self.gcoder.disablestepper
    )
    self.rpc_commands.__setitem__("send-home", self.gcoder.sendhome)
    self.rpc_commands.__setitem__("set-max-x", self.gcoder.set_max_x)
    self.rpc_commands.__setitem__("set-max-y", self.gcoder.set_max_y)
    self.rpc_commands.__setitem__("set-max-z", self.gcoder.set_max_z)

  def register_data_methods(self):
    self.channel.exchange_declare(exchange="data", exchange_type="direct")
    self.channel.queue_declare(queue="gcoder_data", exclusive=True)
    self.channel.queue_bind(
      exchange="data", queue="gcoder_data", routing_key="gcoder_data"
    )

    self.channel.basic_qos(prefetch_count=1)
    self.channel.basic_consume(
      queue="gcoder_data",
      on_message_callback=self.on_request_data_aux,
    )

    self.data_methods.__setitem__(
      "get-settings", self.gcoder.getsettings
    )
    self.data_methods.__setitem__("in-motion", self.gcoder.inmotion)
    self.data_methods.__setitem__("get-opx", self.get_opx)
    self.data_methods.__setitem__("get-opy", self.get_opy)
    self.data_methods.__setitem__("get-opz", self.get_opz)
    self.data_methods.__setitem__("get-cx", self.get_cx)
    self.data_methods.__setitem__("get-cy", self.get_cy)
    self.data_methods.__setitem__("get-cz", self.get_cz)
    self.data_methods.__setitem__("get-vx", self.get_vx)
    self.data_methods.__setitem__("get-vy", self.get_vy)
    self.data_methods.__setitem__("get-vz", self.get_vz)
    self.data_methods.__setitem__("get-max-x", self.gcoder.get_max_x)
    self.data_methods.__setitem__("get-max-y", self.gcoder.get_max_y)
    self.data_methods.__setitem__("get-max-z", self.gcoder.get_max_z)

  def on_request_data_aux(self, ch, commamd, props, body):
    self.on_request_data(ch, commamd, props, body, self.data_methods)

  def on_request_command_aux(self, ch, command, props, body):
    self.on_request_command(ch, command, props, body, self.rpc_commands)

  
  def get_opx(self):
    return self.gcoder.opx
  
  def get_opy(self):
    return self.gcoder.opy
  
  def get_opz(self):
    return self.gcoder.opz
  
  def get_cx(self):
    return self.gcoder.cx

  def get_cy(self):
    return self.gcoder.cy
  
  def get_cz(self):
    return self.gcoder.cz

  def get_vx(self):
    return self.gcoder.vx
  
  def get_vy(self):
    return self.gcoder.vy
  
  def get_vz(self):
    return self.gcoder.vz