#!/usr/bin/env python
import pika
import json

from GCoderServer import GCoderServer
from GpioServer import GpioServer


class RpcServer:
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters("10.42.0.1")
        )

        self.channel = self.connection.channel()

        self.clients = set()
        self.queued_clients = []

        self.rpc_commands = {}

        self.register()
        print(" [x] Awaiting requests")
        self.channel.start_consuming()

        self.gcoder = GCoderServer(self)
        self.gpio = GpioServer(self)
        self.drs = DRSServer(self)

    def callback(self, ch, method, properties, body):
        if body == b"Connect":
            if not self.clients:
                self.clients.add(properties.reply_to)
                ch.basic_publish(
                    exchange="",
                    routing_key=properties.reply_to,
                    properties=pika.BasicProperties(
                        correlation_id=properties.correlation_id
                    ),
                    body=b"Connected",
                )
                print("Connection granted to:", properties.reply_to)
            elif properties.reply_to in self.clients:
                # connected client is attempting to connect again
                ch.basic_publish(
                    exchange="",
                    routing_key=properties.reply_to,
                    properties=pika.BasicProperties(
                        correlation_id=properties.correlation_id
                    ),
                    body=b"Already Connected",
                )
                print("Already connected:", properties.reply_to)
            else:
                # ch.basic_publish(
                #     exchange="",
                #     routing_key=properties.reply_to,
                #     properties=pika.BasicProperties(
                #         correlation_id=properties.correlation_id
                #     ),
                #     body=b"Queued",
                # )
                self.queued_clients.append(properties.reply_to)
                print("Client queued:", properties.reply_to)
        elif body == b"Release":
            if properties.reply_to in self.clients:
                self.clients.remove(properties.reply_to)
                print("Released connection for:", properties.reply_to)
                self.next_in_queue()
            else:
                print(
                    "Attempted to release an unconnected client:", properties.reply_to
                )

        ch.basic_ack(delivery_tag=method.delivery_tag)

    def next_in_queue(self):
        if len(self.queued_clients) > 0:
            if first_client := self.queued_clients.pop(0):
                print("First client in queue:", first_client)
                self.channel.basic_publish(
                    exchange="", routing_key=first_client, body="Connected"
                )
                print("Connection granted to queued client:", first_client)

    def fib(self, arg):
        n = int(arg)
        print("Calculating Fibonacci for", n)
        if n == 0:
            return 0
        elif n == 1:
            return 1
        else:
            return self.fib(n - 1) + self.fib(n - 2)

    def add(self, args):
        a, b = args
        print("Performing addition:", a, "+", b)
        return a + b

    def on_request_command(self, ch, method, props, body, rpc_commands={}):
        print("Received request from:", props.reply_to)
        if props.reply_to in self.clients:
            request = json.loads(body)
            command = request["command"]
            args = request["args"]

            if command in rpc_commands.keys():
              print("Received command:", command, "with args:", args)
              response = rpc_commands[command](args)
              response = response if callable(response) else "Command executed"
            else:
              response = "Unknown command"

            ch.basic_publish(
              exchange="",
              routing_key=props.reply_to,
              properties=pika.BasicProperties(correlation_id=props.correlation_id),
              body=json.dumps(response),
            )

        else:
            print("Unauthorized client:", props.reply_to)
            ch.basic_publish(
                exchange="",
                routing_key=props.reply_to,
                properties=pika.BasicProperties(correlation_id=props.correlation_id),
                body="Unauthorized Client",
            )

        ch.basic_ack(delivery_tag=method.delivery_tag)

    def register_commands(self):
        self.channel.exchange_declare(
            exchange="exclusive_exchange", exchange_type="direct"
        )
        self.channel.queue_declare(queue="exclusive_queue", exclusive=True)
        self.channel.queue_bind(
            exchange="exclusive_exchange",
            queue="exclusive_queue",
            routing_key="exclusive_key",
        )

        self.channel.basic_consume(
            queue="exclusive_queue", on_message_callback=self.callback
        )

        # for rpc command requests
        self.channel.queue_declare(queue="")
        # self.channel .exchange_declare(exchange="commands", exchange_type="direct")

        self.channel.exchange_declare(exchange="commands", exchange_type="direct")
        self.channel.queue_declare(queue="rpc_queue", exclusive=True)
        self.channel.queue_bind(
            exchange="commands", queue="rpc_queue", routing_key="rpc_queue"
        )

        self.channel.basic_qos(prefetch_count=1)
        self.channel.basic_consume(
            queue="rpc_queue", on_message_callback=self.on_request_rpc_command
        )

        # add commands here
        self.rpc_commands.__setitem__("get-fib", self.fib)
        self.rpc_commands.__setitem__("add", self.add)

    def register_data_methods(self):
        self.channel.exchange_declare(exchange="data", exchange_type="direct")
        self.channel.queue_declare(queue="telemetry_data_queue", exclusive=True)
        self.channel.queue_bind(
            exchange="data",
            queue="telemetry_data_queue",
            routing_key="telemetry_data_queue",
        )

    def register(self):
        self.register_commands()
        self.register_data_methods()

    def on_request_data(self, ch, method, props, body, data_methods={}):
        print(f" [x] {method.routing_key}:{body}")
        request = json.loads(body)
        command = request["command"]
        args = request["args"]

        if command in data_methods.keys():
          print("Received command:", command, "with args:", args)
          response = data_methods[command](args)
          response = response if callable(response) else "Command executed"
        else:
          response = "Unknown command"

        ch.basic_publish(
          exchange="",
          routing_key=props.reply_to,
          properties=pika.BasicProperties(correlation_id=props.correlation_id),
          body=json.dumps(response),
        )

        ch.basic_ack(delivery_tag=method.delivery_tag)


server = RpcServer()
