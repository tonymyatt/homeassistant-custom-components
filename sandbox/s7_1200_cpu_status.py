import snap7
client = snap7.client.Client()
client.connect("192.168.1.61", 0, 1, 102)
if client.get_connected():
  print(client.get_cpu_state())
else:
  print("Connection Failed")