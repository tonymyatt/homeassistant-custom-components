# Example Usage of TinyTuya
import tinytuya
import logging
import sys

#logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

d = tinytuya.Device('10811653', '192', 'fff2eeb9')
d.set_version(3.3)
data = d.status() 
print('Device status: %r' % data)
data = d.status_sub_device('108117183', 'bf6c4fags5m') 
print('Device status: %r' % data)
