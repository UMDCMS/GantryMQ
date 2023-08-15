import random
from client import RpcClient


class GpioClient(RpcClient):
  def __init__(self):
    super().__init__()

  def slow_write(self, x):
      self.call(
        "slow-write",
        {"x": x},
        exchange="commands",
        routing_key="gpio_queue",
      )

  def pulse(self, n, wait):
    self.call(
      "pulse",
      {"n": n, "wait": wait},
      exchange="commands",
      routing_key="gpio_queue",
    )

  # Read-like data members (Should only be set via operation-functions)
  def slow_read(self):
    self.call(
      "slow-read",
      {},
      exchange="data",
      routing_key="gpio_data",
    )

  # Static methods - getterrs
  def get_read(self):
    self.call(
      "get-read",
      {},
      exchange="data",
      routing_key="gpio_data",
    )
  
  def get_write(self):
    self.call(
      "get-write",
      {},
      exchange="data",
      routing_key="gpio_data",
    )
  
  # create the following fuctions to return random values: adc_read, ntc_read, rtd_read, pwm, adc_setref, light_on, light_off
  def adc_read(self, x):
    return random.randint(0, 1023)
  
  def ntc_read(self, x):
    return random.randint(0, 1023)
  
  def rtd_read(self, x):
    return random.randint(0, 1023)

  def pwm_duty(self, x):
    return random.randint(0, 1023)
  
  def adc_setref(self, channel, x):
    return random.randint(0, 1023)

  def light_on(self):
    return random.randint(0, 1023)

  def light_off(self):
    return random.randint(0, 1023)
