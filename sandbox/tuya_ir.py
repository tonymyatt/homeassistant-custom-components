# Example Usage of TinyTuya
import tinytuya
import logging
import sys

#logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)

d = tinytuya.Device('108117185002916e0653', '192.168.1.224', 'fd1f63df5ff2eeb9')
d.set_version(3.3)
data = d.status() 
print('Device status: %r' % data)
data = d.status_sub_device('108117185002916e0653', 'bf6c4faebf0cab6ec7gs5m') 
print('Device status: %r' % data)