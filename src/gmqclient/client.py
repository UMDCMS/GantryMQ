#!/usr/bin/env python
import pika
import uuid
import json
import sys

from .GCoderClient import GCoderClient
from .GpioClient import GpioClient
from .DRSClient import DRSClient


class RpcClient(object):
  def __init__(self):
    self.connection = pika.BlockingConnection(
        pika.ConnectionParameters(host="10.42.0.1")
    )

    self.channel = self.connection.channel()

    self.channel.exchange_declare(exchange="commands", exchange_type="direct")

    self.channel.exchange_declare(exchange="data", exchange_type="direct")

    # Set up the callback queue to receive responses. Using default to get a random queue name, so that each client has its own queue
    res = self.channel.queue_declare(queue="", exclusive=True, auto_delete=True)
    self.callback_queue = res.method.queue

    self.channel.basic_consume(
        queue=self.callback_queue,
        on_message_callback=self.on_response,
        auto_ack=True,
    )

    self.response = None
    self.corr_id = None

    self.gcoder = GCoderClient(self)
    self.gpio = GpioClient(self)
    self.drs = DRSClient(self)

    # Register a function to be called at exit to ensure "release" is sent
    # atexit.register(self.release_connection)
    # # Register a signal handler for SIGINT (Ctrl+C) to ensure "release" is sent on termination
    # signal.signal(signal.SIGINT, self.signal_handler)

  def handle_connection_response(self, response):
    if response == b"Connected":
      print(" [x] Connected to server")
    elif response == b"Queued":
      print(" [x] Queued")
    elif response == b"Released":
      print(" [x] Released")

  # This method is called whenever a response is received
  def on_response(self, ch, method, props, body):
    print(" [xx] Received response:", body)
    if self.corr_id == props.correlation_id:
        self.response = body

  def send_request(self, request):
    self.response = None
    self.corr_id = str(uuid.uuid4())
    self.channel.basic_publish(
      exchange="",
      routing_key="exclusive_queue",
      properties=pika.BasicProperties(
          reply_to=self.callback_queue, correlation_id=self.corr_id
      ),
      body=request,
    )
    # while self.response is None:
    #     self.connection.process_data_events()
    # return self.response
    print(" [x] Waiting for response...")
    self.connection.process_data_events(time_limit=None)
    print(" [x] Received response: ", self.response)
    self.handle_connection_response(self.response)
    return self.response


  def call(self, command, args, exchange="commands", routing_key="rpc_queue"):
    self.response = None
    self.corr_id = str(uuid.uuid4())
    request = {"command": command, "args": args}

    print(" [x] Sending request:", request)
    print(" [x] reply to:", self.callback_queue)
    # request the command with the params
    self.channel.basic_publish(
      exchange=exchange,
      routing_key=routing_key,
      properties=pika.BasicProperties(
          reply_to=self.callback_queue,
          correlation_id=self.corr_id,
      ),
      body=json.dumps(request),
    )

    # Wait
    self.connection.process_data_events(time_limit=None)
    self.handle_response(self.response)
    return self.response

  def release_connection(self):
    try:
      self.send_request("Release")
      print("[x] Connection Released.")
    except pika.exceptions.AMQPError:
      print(
          "Failed to send 'Release' message. Connection may not have been released."
      )

  def signal_handler(self, signal, frame):
    print("[x] Client interrupted.")
    self.release_connection()
    sys.exit(0)


# rpc = RpcClient()
# try:
#     print(" [x] Requesting connection")
#     response = rpc.send_request("Connect")
#     print(" [x] Received response:", response)
# except KeyboardInterrupt:
#     print("Connection Released due to interruption.")
#     # sys.exit(1)
# except Exception as e:
#     print("Error occurred:", e)
#     # sys.exit(1)
# finally:
#     # Ensure that the release message is sent on any error or interruption
#     rpc.release_connection()
