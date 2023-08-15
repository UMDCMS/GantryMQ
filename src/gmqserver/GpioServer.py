import pika
import json

import modules.gpio as gpio

class GpioServer(RpcServer):
  def __init__(self, rpc_server):
    super().__init__()

    self.gpio = gpio(21, gpio.WRITE)

    self.rpc_commands = {}
    self.data_methods = {}

    self.register_commands()
    self.register_data_methods()

    self.rpc_server = rpc_server

  def register_commands(self):
    self.channel.exchange_declare(exchange="commands", exchange_type="direct")
    self.channel.queue_declare(queue="gpio_queue", exclusive=True)
    self.channel.queue_bind(
      exchange="commands",
      queue="gpio_queue",
      routing_key="gpio_queue",
    )

    self.channel.basic_qos(prefetch_count=1)
    self.channel.basic_consume(
      queue="gpio_queue",
      on_message_callback=self.on_request_command_aux,
    )

    self.rpc_commands.__setitem__("slow-write", self.gpio.slow_write)
    self.rpc_commands.__setitem__("pulse", self.gpio.pulse)


  def register_data_methods(self):
    self.channel.exchange_declare(exchange="data", exchange_type="direct")
    self.channel.queue_declare(queue="gpio_data", exclusive=True)
    self.channel.queue_bind(
      exchange="data", queue="gpio_data", routing_key="gpio_data"
    )

    self.channel.basic_qos(prefetch_count=1)
    self.channel.basic_consume(
      queue="gpio_data",
      on_message_callback=self.on_request_data_aux,
    )

    self.data_methods.__setitem__("slow-read", self.gpio.slow_read)
    self.data_methods.__setitem__("get-read", self.get_read)
    self.data_methods.__setitem__("get-write", self.get_write)



  def on_request_data_aux(self, ch, commamd, props, body):
    self.on_request_data(ch, commamd, props, body, self.data_methods)

  def on_request_command_aux(self, ch, command, props, body):
    self.on_request_command(ch, command, props, body, self.rpc_commands)

  def get_read(self):
    return self.gpio.READ

  def get_write(self):
    return self.gpio.WRITE
  