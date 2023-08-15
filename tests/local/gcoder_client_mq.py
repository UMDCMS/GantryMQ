from gmqclient.client import RpcClient

client = RpcClient()

client.send_request('Connect')
client.gcoder.move_to(100, 100, 100)
client.send_request('Release')
