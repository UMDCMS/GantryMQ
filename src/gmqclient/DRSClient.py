
class DRSClient(RpcClient):
  def __init__(self, rpc_client):
    super().__init__()

    self.rpc_client = rpc_client

  def force_stop(self):
      self.rpc_client.call(
        "force-stop",
        {},
        exchange="commands",
        routing_key="drs_queue",
      )

  def start_collect(self):
    self.rpc_client.call(
      "start-collect",
      {},
      exchange="commands",
      routing_key="drs_queue",
    )
  
  def run_calibrations(self):
    self.rpc_client.call(
      "run-calibration",
      {},
      exchange="commands",
      routing_key="drs_queue",
    )
  
  def set_trigger(self, channel, level, direction, delay):
    self.rpc_client.call(
      "set-trigger",
      {"channel": channel, "level": level, "direction": direction, "delay": delay},
      exchange="commands",
      routing_key="drs_queue",
    )
  
  def set_samples(self, x):
    self.rpc_client.call(
      "set-samples",
      {"x": x},
      exchange="commands",
      routing_key="drs_queue",
    )

  def set_rate(self, x):
    self.rpc_client.call(
      "set-rate",
      {"x": x},
      exchange="commands",
      routing_key="drs_queue",
    )

  # Read-like data members (Should only be set via operation-functions)
  def get_time_slice(self):
    self.rpc_client.call(
      "get-time-slice",
      {},
      exchange="data",
      routing_key="drs_data",
    )
  
  def get_waveform(self, channel):
    self.rpc_client.call(
      "get-waveform",
      {"channel": channel},
      exchange="data",
      routing_key="drs_data",
    )
  
  def get_waveformsum(self):
    self.rpc_client.call(
      "get-waveformsum",
      {},
      exchange="data",
      routing_key="drs_data",
    )

  # Static methods - getterrs
  def get_trigger_channel(self):
    self.rpc_client.call(
      "get-trigger-channel",
      {},
      exchange="data",
      routing_key="drs_data",
    )
  
  def get_trigger_direction(self):
    self.rpc_client.call(
      "get-trigger-direction",
      {},
      exchange="data",
      routing_key="drs_data",
    )

  def get_trigger_level(self):
    self.rpc_client.call(
      "get-trigger-level",
      {},
      exchange="data",
      routing_key="drs_data",
    )
  
  def get_trigger_delay(self):
    self.rpc_client.call(
      "get-trigger-delay",
      {},
      exchange="data",
      routing_key="drs_data",
    )

  def get_samples(self):
    self.rpc_client.call(
      "get-samples",
      {},
      exchange="data",
      routing_key="drs_data",
    )

  def get_rate(self):
    self.rpc_client.call(
      "get-rate",
      {},
      exchange="data",
      routing_key="drs_data",
    )

  def is_available(self):
    self.rpc_client.call(
      "is-available",
      {},
      exchange="data",
      routing_key="drs_data",
    )

  def is_ready(self):
    self.rpc_client.call(
      "is-ready",
      {},
      exchange="data",
      routing_key="drs_data",
    )
