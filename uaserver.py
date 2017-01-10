#!/usr/bin/python3
# -*- coding: utf-8 -*-
"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import os
import sys
import time
import socketserver
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

# Comprobación argumentos
if not len(sys.argv) == 2:
    sys.exit('Usage: python3 uaserver.py config')
_, config = sys.argv
#port = int(port)


#log
def NuevoLog(Evento):

    fichero = open('LogUaServer.txt', 'a+')
    HoraActual = time.gmtime(time.time())
    HoraActual = time.strftime('%Y%m%d%H%M%S', HoraActual)
    fichero.write(str(HoraActual) + ' ' + Evento + '\r\n')


class EchoHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    ListaRTP = []

    def handle(self):

        # Escribe dirección y puerto del cliente (de tupla client_address)
        line = self.rfile.read()
        print('El cliente nos manda ', line.decode('utf-8'))
        datos = line.decode('utf-8').split()
        #print('QUIERO BUSCAR MI PUERTO:', datos)
        #print('PUERTO QUE TENGO QUE COMPROBAR:',rtpaudio_puerto)
        if datos[0] == 'INVITE':
            method = datos[1].split(':')[1]
            #print(datos)
            self.wfile.write(b'SIP/2.0 100 Trying \r\n\r\n')
            self.wfile.write(b'SIP/2.0 180 Ring \r\n\r\n')
            self.wfile.write(b'SIP/2.0 200 OK \r\n\r\n')
            #line = method + ' sip:' + direccion + ':' + uaserver_puerto + ' SIP/2.0\r\n'
            #line += ('Enviando: ' + line)
            line = ('Content-Type: application/sdp' + '\r\n')
            line += ('\n')
            line += ('v=0' + '\r\n')
            line += ('o=' + account_username + ' 127.0.0.1' + '\r\n')
            line += ('s=NombreSesion' + '\r\n')
            line += ('t=0' + '\r\n')
            line += ('m=' + 'audio ' + rtpaudio_puerto + ' RTP' + '\r\n')
            self.wfile.write(bytes(line, 'utf-8'))
            puerto_rtpaudio_puerto = datos[11]
            self.ListaRTP.append(puerto_rtpaudio_puerto)
            #print('listaRTP', self.ListaRTP[0])
            Evento = 'Received from ' + regproxy_ip + ':' + puerto_rtpaudio_puerto + ': ' + line
            NuevoLog(Evento)
        elif datos[0] == 'BYE':
            method = datos[1].split(':')[1]
            self.wfile.write(b'SIP/2.0 200 OK \r\n\r\n')
            Evento = 'Received from ' + regproxy_ip + ':' + regproxy_puerto + ': ' + line.decode('utf-8')
            NuevoLog(Evento)
        elif datos[0] == 'ACK':
            method = datos[1].split(':')[1]
            self.wfile.write(b'ACK')
            #print('listaRTP', self.ListaRTP[0])
            # aEjecutar es un string con lo que se ha de ejecutar en la shell
            aEjecutar = './mp32rtp -i 127.0.0.1 -p ' + self.ListaRTP[0] + ' < '  + audio_path
            print('Vamos a ejecutar', aEjecutar)
            os.system(aEjecutar)
            print('Ha acabado la cancion')
            Evento = 'Sent to ' + regproxy_ip + ':' + regproxy_puerto + ': ' + 'cancion.mp3'
            NuevoLog(Evento)
        elif datos[0] != ('INVITE' and 'BYE' and 'ACK'):
            method = datos[1].split(':')[1]
            self.wfile.write(b'SIP/2.0 405 Method Not Allowed')
            Evento = 'Received from ' + regproxy_ip + ':' + regproxy_puerto + ': ' + line.decode('utf-8')
            NuevoLog(Evento)
        else:
            self.wfile.write(b'SIP/2.0 400 Bad Request')
            Evento = 'Received from ' + str(regproxy_ip) + ':' + str(regproxy_puerto) + ': ' + line.decode('utf-8')
            NuevoLog(Evento)


class XMLHandler(ContentHandler):

    def __init__(self):

        self.lista = []  # lista donde defino las variables del archivo xml
        self.dicc = {}  # lista donde guardo los diccionarios

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
cHandler = XMLHandler()
parser.setContentHandler(cHandler)
parser.parse(open(sys.argv[1]))
lista = cHandler.get_tags()

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

# Excepción archivo de audio
if not os.path.exists(audio_path):
    sys.exit('El archivo ' + audio_path + ' no existe')
#print('llega hasta aqui')

# Creamos servidor de eco y escuchamos
serv = socketserver.UDPServer((uaserver_ip, int(uaserver_puerto)), EchoHandler)
print('Listening...')
try:
    serv.serve_forever()
    Evento = 'Finishing'
    NuevoLog(Evento)
except KeyboardInterrupt:
    print('Servidor cerrado.')
