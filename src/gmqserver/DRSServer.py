import json

import modules.drs as drs

class DRSServer():
  def __init__(self, rpc_server):
    super().__init__()

    self.drs = drs()

    self.rpc_commands = {}
    self.data_methods = {}

    self.register_commands()
    self.register_data_methods()

    self.rpc_server = rpc_server

  def register_commands(self):
    self.channel.exchange_declare(exchange="commands", exchange_type="direct")
    self.channel.queue_declare(queue="drs_queue", exclusive=True)
    self.channel.queue_bind(
      exchange="commands",
      queue="drs_queue",
      routing_key="drs_queue",
    )

    self.channel.basic_qos(prefetch_count=1)
    self.channel.basic_consume(
      queue="drs_queue",
      on_message_callback=self.on_request_command_aux,
    )

    self.rpc_commands.__setitem__("force-stop", self.drs.force_stop)
    self.rpc_commands.__setitem__("start-collect", self.drs.start_collect)
    self.rpc_commands.__setitem__("run-calibration", self.drs.run_calibration)
    self.rpc_commands.__setitem__("set-trigger", self.drs.set_trigger)
    self.rpc_commands.__setitem__("set-samples", self.drs.set_samples)
    self.rpc_commands.__setitem__("set-rate", self.drs.set_rate)

  def register_data_methods(self):
    self.channel.exchange_declare(exchange="data", exchange_type="direct")
    self.channel.queue_declare(queue="drs_data", exclusive=True)
    self.channel.queue_bind(
      exchange="data", queue="drs_data", routing_key="drs_data"
    )

    self.channel.basic_qos(prefetch_count=1)
    self.channel.basic_consume(
      queue="drs_data",
      on_message_callback=self.on_request_data_aux,
    )

    self.data_methods.__setitem__("get-time-slice", self.drs.get_time_slice)
    self.data_methods.__setitem__("get-waveform", self.drs.get_waveform)
    self.data_methods.__setitem__("get-waveformsum", self.drs.get_waveformsum)
    self.data_methods.__setitem__("get-trigger-channel", self.drs.get_trigger_channel)
    self.data_methods.__setitem__("get-trigger-direction", self.drs.get_trigger_direction)
    self.data_methods.__setitem__("get-trigger-level", self.drs.get_trigger_level)
    self.data_methods.__setitem__("get-trigger-delay", self.drs.get_trigger_delay)
    self.data_methods.__setitem__("get-samples", self.drs.get_samples)
    self.data_methods.__setitem__("get-rate", self.drs.get_rate)
    self.data_methods.__setitem__("is-available", self.drs.is_available)
    self.data_methods.__setitem__("is-ready", self.drs.is_ready)

  def on_request_data_aux(self, ch, commamd, props, body):
    self.rpc_server.on_request_data(ch, commamd, props, body, self.data_methods)

  def on_request_command_aux(self, ch, command, props, body):
    self.rpc_server.on_request_command(ch, command, props, body, self.rpc_commands)
