#---------------------------------------------------------------------------
# gprs_dtu_server
# -- A python service to accept GPRS DTU connection and read data from connected modbus device 
#
# BSD 3-clause license is applied to this code
# Copyright(c) 2015 by Aixi Wang <aixi.wang@hotmail.com>
#---------------------------------------------------------------------------
#!/usr/bin/python
import socket
import threading               # Import socket module
import time
import os,sys
from tcpcam2cloud import *

status = 0
#socket.setdefaulttimeout(1)
ALL_CLIENT = []
GRANT_HEADER_LIST = ['LOGIN:1001',
                     'LOGIN:1002']


CAPTURE_INTERVAL = 3600
BASE_FOLDER = '/usr/share/nginx/www/img/'

MODBUS_CMD_LIST = ['\x01\x03\x00\x02\x00\x01\x25\xca']

#-------------------
# writefile2
#-------------------
def writefile2(filename,content):
    f = file(filename,'ab')
    fs = f.write(content)
    f.close()
    return 
    
# Define tcp handler for a thread...
def myHandler(client, addr, header):
    global status
    global resp_bin

    client.setblocking(0)

    ALL_CLIENT.append({
        'fd': client,
        'addr': addr,
        'closed': False
    });

    print 'thread started for ', addr
    c1 = ''
    while True:
        # avoid cpu loading too hight
        time.sleep(0.1)
        try:
            msg = client.recv(1024*64)
            print 'recv msg(hex):',msg.encode('hex')
            c1 += msg   
            

        except socket.error as e:
            if c1 != '':
                print 'step 2...'
                # process income data
                if len(c1) == 7:
                    if c1[0:3] == '\x01\x03\x02':
                        t = ord(c1[3])*256 + ord(c1[4])
                        print 't: %f \'C' % (t/10.0)
                        s = '%s %s %s %f\r\n' % (str(format_time_from_linuxtime(time.time())), header, str(ord(c1[0])),t/10.0)
                        writefile2(BASE_FOLDER + 'data.txt',s)
                    else:
                        print 'invalid modbus response data'
                else:
                    print 'abnormal response'

                status = 1
                c1 = ''
                
            continue
        
        except Exception as e:
            print 'Server get a error fd: ', e
            status = -1
            client.close()            
            break

#-----------------------------
# myPollTask
#-----------------------------
def myPollTask(client, addr):
    global status
    global resp_bin
    global MODBUS_CMD_LIST
    print 'start myPollTask for addr:',addr
    while True:
        try:
            time.sleep(1)
            status = 0
            resp_bin = ''
            
            for cmd in MODBUS_CMD_LIST:
                s = cmd 
                print 'send modbus command(hex):',s.encode('hex')
                client.sendall(s)
                time.sleep(CAPTURE_INTERVAL)

        except:
            print 'myPollTask exception, exit'
            return


#----------------------
# main
#----------------------
if __name__ == "__main__":
    # To launch Socket Server
    
    while True:
        try:
            server = socket.socket()
            host = socket.gethostname()
            port = 8877
            server.bind(('', port))
            server.listen(5)
            print 'Server FD No: ', server.fileno()
            break
            
        except:
            time.sleep(3)
    
    while True:
        try:
            client, addr = server.accept()
            print 'Got connection from', addr, ' time:', format_time_from_linuxtime(time.time())
            header = client.recv(32)
            h_s = header.encode('hex')
            # LOGIN:1001
            print 'header:', header,' header(hex):',h_s
            s = 'new connection from %s, time: %s\r\n' % (str(addr),str(format_time_from_linuxtime(time.time())))
            writefile2('log.txt',s)
            
            #if (header in GRANT_MAC_LIST):
            #    print 'new thread created! for addr:',addr
            threading.Thread(target=myHandler, args=(client, addr, header[6:])).start()
            threading.Thread(target=myPollTask, args=(client, addr)).start()
        
        except KeyboardInterrupt:
            print 'ctl+c is pressed'
            break

        except:
            print 'except, try again.'
            time.sleep(3)

