#!/usr/bin/python3
# -*- coding: utf-8 -*-

import os
import sys
import socket
import time
import json
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

# Comprobación argumentos
if not len(sys.argv) == 4:
    sys.exit('Usage: python3 uaclient.py config method option')
_, config, method, option = sys.argv


#log
def NuevoLog(Evento):

    fichero = open('LogUaClient.txt', 'a+')
    HoraActual = time.gmtime(time.time())
    HoraActual = time.strftime('%Y%m%d%H%M%S', HoraActual)
    fichero.write(str(HoraActual) + ' ' + Evento + '\r\n')


class XMLHandler(ContentHandler):

    def __init__(self):

        self.lista = []  # lista donde defino las variables del archivo xml
        self.dicc = {}  # diccionario donde guardo los datos

    def startElement(self, name, attrs):

        if name == 'account':
            self.dicc[name] = {(name + '_username'): attrs.get('username', ""), (name + '_passwd'): attrs.get('passwd', "")}
            self.lista.append(self.dicc)
            self.dicc = {}
        elif name == 'uaserver':
            self.dicc[name] = {(name + '_ip'): attrs.get('ip', ""), (name + '_puerto'): attrs.get('puerto', "")}
            self.lista.append(self.dicc)
            self.dicc = {}
        elif name == 'rtpaudio':
            self.dicc[name] = {(name + '_puerto'): attrs.get('puerto', "")}
            self.lista.append(self.dicc)
            self.dicc = {}
        elif name == 'regproxy':
            self.dicc[name] = {(name + '_ip'): attrs.get('ip', ""), (name + '_puerto'): attrs.get('puerto', "")}
            self.lista.append(self.dicc)
            self.dicc = {}
        elif name == 'log':
            self.dicc[name] = {(name + '_path'): attrs.get('path', "")}
            self.lista.append(self.dicc)
            self.dicc = {}
        elif name == 'audio':
            self.dicc[name] = {(name + '_path'): attrs.get('path', "")}
            self.lista.append(self.dicc)
            self.dicc = {}

    def get_tags(self):

        return self.lista

parser = make_parser()
XMLH = XMLHandler()
parser.setContentHandler(XMLH)
parser.parse(open(sys.argv[1]))
lista = XMLH.get_tags()
# print(lista)

# Datos del archivo xml
account_username = lista[0]['account']['account_username']
account_password = lista[0]['account']['account_passwd']
uaserver_ip = lista[1]['uaserver']['uaserver_ip']
uaserver_puerto = lista[1]['uaserver']['uaserver_puerto']
rtpaudio_puerto = lista[2]['rtpaudio']['rtpaudio_puerto']
regproxy_ip = lista[3]['regproxy']['regproxy_ip']
regproxy_puerto = lista[3]['regproxy']['regproxy_puerto']
log_path = lista[4]['log']['log_path']
audio_path = lista[5]['audio']['audio_path']

# Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
my_socket.connect((regproxy_ip, int(regproxy_puerto)))

if method == 'INVITE' or method == 'BYE':
    direccion = sys.argv[3]
elif method == 'REGISTER':
    expires = sys.argv[3]
#print('AUDIO QUE ME IMPRIMO:', rtpaudio_puerto)
if method == 'INVITE':
    line = method + ' sip:' + direccion + ':' + uaserver_puerto + ' SIP/2.0\r\n'
    #line += ('Enviando: ' + line)
    line += ('Content-Type: application/sdp' + '\r\n')
    line += ('\n')
    line += ('v=0' + '\r\n')
    line += ('o=' + account_username + ' 127.0.0.1' + '\r\n')
    line += ('s=NombreSesion' + '\r\n')
    line += ('t=0' + '\r\n')
    line += ('m=' + 'audio ' + rtpaudio_puerto + ' RTP' + '\r\n')
    print('Enviando: ' + line)
    Evento = 'Sent to ' + str(regproxy_ip) + ':' + str(regproxy_puerto) + ': ' + line
    NuevoLog(Evento)
elif method == 'BYE':
    line = method + ' sip:' + direccion + ':' + uaserver_puerto + ' SIP/2.0\r\n'
    print('Enviando: ' + line)
    Evento = 'Sent to ' + regproxy_ip + ':' + regproxy_puerto + ': ' + line
    NuevoLog(Evento)
elif method == 'REGISTER':
    line = method + ' sip:' + account_username + ':' + uaserver_puerto + ' SIP/2.0' + '\r\n'
    line += 'Expires: ' + expires
    print('Enviando: ' + line)
    Evento = 'Sent to ' + regproxy_ip + ':' + regproxy_puerto + ': ' + line
    NuevoLog(Evento)
else:
    print('Usage: python uaclient.py config method option')
    Evento = 'Sent to ' + regproxy_ip + ':' + regproxy_puerto + ': ' + line
    NuevoLog(Evento)

# Envio de informacion
#print('Enviando: ' + line)
my_socket.send(bytes(line, 'utf-8') + b'\r\n')
data = my_socket.recv(1024)
data_recibido = data.decode('utf-8').split()
imprimir = data.decode('utf-8')
print('recibiendo', imprimir)
# Envio  de autorizacion... y ACK
data = data.decode('utf-8').split(' ')
#if method == "REGISTER":
#print('IMPRIMO DATA', data)
auto = data[2].split("\r\n")
#print('RECIBO ESTE PUERTO:', data)
if(data[2] == 'Trying' and data[5] == 'Ring' and data[8] == 'OK'):
    line = 'ACK sip:' + direccion + ":" + uaserver_puerto + ' SIP/2.0'
    my_socket.send(bytes(line, 'utf-8') + b'\r\n\r\n')
    # aEjecutar es un string con lo que se ha de ejecutar en la shell
    puerto_rtpaudio_puerto = data[12]
    aEjecutar = './mp32rtp -i 127.0.0.1 -p ' + puerto_rtpaudio_puerto + ' < ' + audio_path
    print('Vamos a ejecutar', aEjecutar)
    os.system(aEjecutar)
    print('Ha acabado la cancion')
    Evento = 'Receieved from ' + regproxy_ip + ':' + uaserver_puerto + ': ' + line
    NuevoLog(Evento)
    Evento = 'Sent to: ' + rtpaudio_puerto + ': ' + 'cancion.mp3'
    NuevoLog(Evento)
elif (auto[0] == 'Unauthorized'):
    Evento = 'Receieved from ' + regproxy_ip + ':' + regproxy_puerto + ': ' + imprimir
    NuevoLog(Evento)
    line = method + ' sip:' + account_username + ':' + uaserver_puerto + ' SIP/2.0' + '\r\n'
    line += 'Expires: ' + expires + '\r\n'
    line += 'Authorization: Digest response="777777777777"'
    Evento = 'Sent to ' + regproxy_ip + ':' + regproxy_puerto + ': ' + line
    NuevoLog(Evento)
    my_socket.send(bytes(line, 'utf-8') + b'\r\n\r\n')
    line = my_socket.recv(1024)
    data_recibido = line.decode('utf-8')
    print(line.decode('utf-8'))
    Evento = 'Receieved from ' + regproxy_ip + ':' + regproxy_puerto + ': Authorized'
    NuevoLog(Evento)
print('Terminando socket...')
Evento = 'Finishing'
NuevoLog(Evento)

# Cerramos todo
print('Fin.')
