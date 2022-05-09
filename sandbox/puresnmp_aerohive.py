import datetime
import pprint
from datetime import timedelta, datetime
from typing import List
from numpy import empty, integer
from puresnmp import get, walk
from puresnmp.snmp import VarBind

IP1 = "192.168.1.4"
IP2 = "192.168.1.5"
COMMUNITY = 'public'

OID_MGMT_SYS = '1.3.6.1.2.1.1'

OID_sysDescr = '1.3.6.1.2.1.1.1.0'
OID_sysDescr = '1.3.6.1.2.1.1.2.0'
OID_sysUpTime = '1.3.6.1.2.1.1.3.0'

MGMT_SYS = {
    1: ['sysDescr', str],
    #2: ['sysObjectID', str],
    3: ['sysUpTime', 'native'],
    #4: ['sysContact', str],
    5: ['sysName', str],
    #6: ['sysLocation', str],
    #7: ['sysORLastChange', datetime]
}

#enterprises.26928.1.1.1.2.1.2.1
OID_AEROHIVE_IFA = '1.3.6.1.4.1.26928.1.1.1.2.1.1.1'
OID_AEROHIVE_IFB = '1.3.6.1.4.1.26928.1.1.1.2.1.2.1'

AH_IF_ENTRY:dict = {
    1: ['name', str],
    2: ['ssid', str],
    3: ['promiscuous', int],
    4: ['type', int],
    5: ['mode', int],
    6: ['confMode', int]
}

AH_IF_WIFI:dict = {
    'wifi0': '2.4Ghz',
    'wifi1': '5Ghz'
}

AH_ASSOC_ENTRY:dict = {
	1: ['ahClientMac', 'macaddr'],
	2: ['ahClientIP', 'ipaddr'],
	3: ['ahClientHostname', str],
	4: ['ahClientRSSI', int],
	5: ['ahClientLinkUptime', timedelta],
	#6: ['ahClientCWPUsed', int],
   	#7: ['ahClientAuthMethod', int],
  	#8: ['ahClientEncryptionMethod', int],
  	#9: ['ahClientMACProtocol', int],
  	#10: ['ahClientSSID', str],
  	#11: ['ahClientVLAN', int],
  	#12: ['ahClientUserProfId', int],
  	#13: ['ahClientChannel', int],
 	#14: ['ahClientLastTxRate', int],
	#15: ['ahClientUsername', str],
 	#16: ['ahClientRxDataFrames', int],
 	#17: ['ahClientRxDataOctets', int],
 	#18: ['ahClientRxMgtFrames', int],
  	#19: ['ahClientRxUnicastFrames', int],
    #20: ['ahClientRxMulticastFrames', int],
    #21: ['ahClientRxBroadcastFrames', int],
  	#22: ['ahClientRxMICFailures', int],
  	#23: ['ahClientLastRxRate', int],
  	#24: ['ahClientTxDataFrames', int],
  	#25: ['ahClientTxBeDataFrames', int],
  	#26: ['ahClientTxBgDataFrames', int],
  	#27: ['ahClientTxViDataFrames', int],
  	#28: ['ahClientTxVoDataFrames', int],
  	#29: ['ahClientTxMgtFrames', int],
  	#30: ['ahClientTxDataOctets', int],
  	#31: ['ahClientTxUnicastFrames', int],
  	#32: ['ahClientTxMulticastFrames', int],
  	#33: ['ahClientTxBroadcastFrames', int],
  	#34: ['ahClientTxAirtime', int],
  	#35: ['ahClientRxAirtime', int],
  	36: ['ahClientAssociationTime', datetime],
  	#37: ['ahClientBSSID', 'macaddr']
}

IP_TOK_LEN = 4
MAC_TOK_LEN = 6

def ipBytesToString(b:bytes):
    if len(b) != IP_TOK_LEN:
        return "Unknown IP"
    
    ip = []
    for i in range(IP_TOK_LEN):
        ip.append(str(int(b[i])))

    return ".".join(ip)

def macBytesToString(b:bytes):
    if len(b) != MAC_TOK_LEN:
        return "Unknown MAC"
    
    mac = []
    for i in range(MAC_TOK_LEN):
        mac.append(str(hex(b[i])[2:]).zfill(2))

    return ":".join(mac)

def format_field(value, data_type):

    if data_type == str:
        return value.decode("utf-8")
    if data_type == int:
        return int(value)
    if data_type == datetime:
        return datetime.fromtimestamp(value).strftime('%m/%d/%Y %H:%M:%S')
    if data_type == timedelta:
        return str(timedelta(seconds=value))
    if data_type == 'ipaddr':
        return ipBytesToString(value)
    if data_type == 'macaddr':
        return macBytesToString(value)
    if data_type == 'native':
        return value

    return None

def ahWifiInterfaces(ip:str):

    for row in walk(ip, COMMUNITY, OID_MGMT_SYS):
        strOid:str = str(row.oid).replace(OID_MGMT_SYS+'.', '')
        toks = strOid.split(".")
        field = int(toks[0])

        if field in MGMT_SYS:

            data = format_field(row.value, MGMT_SYS[field][1])
            if data is not None:
                print(f'{MGMT_SYS[field][0]} {data}')    

    ahIfTable:dict = {}

    for row in walk(ip, COMMUNITY, OID_AEROHIVE_IFA):
        strOid:str = str(row.oid).replace(OID_AEROHIVE_IFA+".", "")
        toks = strOid.split(".")
        field = int(toks[0])
        id = int(toks[1])
        
        if ahIfTable.get(id) is None:
            ahIfTable[id] = {}

        if field in AH_IF_ENTRY:
            data = format_field(row.value, AH_IF_ENTRY[field][1])
            ahIfTable[id][AH_IF_ENTRY[field][0]] = data

    for row in walk(ip, COMMUNITY, OID_AEROHIVE_IFB):
        strOid:str = str(row.oid).replace(OID_AEROHIVE_IFB+".", "")
        toks = strOid.split(".", 3)
        field = int(toks[0])
        id = int(toks[1])
        always6 = toks[2]
        dev = toks[3]

        if ahIfTable.get(id) is None:
            ahIfTable[id] = {}

        if ahIfTable[id].get('wifi.data') is None:
            ahIfTable[id]['wifi.data'] = {}
        
        if ahIfTable[id]['wifi.data'].get(dev) is None:
            ahIfTable[id]['wifi.data'][dev] = {}

        if field in AH_ASSOC_ENTRY:
            data = format_field(row.value, AH_ASSOC_ENTRY[field][1])            
            ahIfTable[id]['wifi.data'][dev][AH_ASSOC_ENTRY[field][0]] = data

    #pprint.pprint(ahIfTable)

    for ahid, ahif in ahIfTable.items():
        if 'wifi' in ahif['name'] and ahif['ssid'] != 'N/A' and 'wifi.data' in ahif:
            wifiSpeed = "Unknown"
            if len(ahif['name']) > 5:
                wifi_channel = ahif['name'][0:5]
                if wifi_channel in AH_IF_WIFI:
                    wifiSpeed = AH_IF_WIFI[wifi_channel]
            
            print(f"{wifiSpeed} SSID {ahif['ssid']} connected clients: {len(ahif['wifi.data'])}")
            for index, row in ahif['wifi.data'].items():
                print(f"- Client {row['ahClientHostname']}  {row['ahClientMac']} {row['ahClientIP']} {row['ahClientRSSI']}dBm")

ahWifiInterfaces(IP1)
ahWifiInterfaces(IP2)