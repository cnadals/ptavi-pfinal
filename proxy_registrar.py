#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
Clase (y programa principal) para un servidor de eco en UDP simple
"""

import sys
import time
import json
import socket
import hashlib
import socketserver
from xml.sax import make_parser
from xml.sax.handler import ContentHandler

# Comprobación de argumentos
if not len(sys.argv) == 2:
    sys.exit('Usage: python3 proxy_registrar.py config')
_, config = sys.argv


#comparo passwords
def HashLib(dir_sip):

    nonce = 43558789
    FicheroSeleccionado = ''
    Fichero1 = open('ua1.xml', 'r')
    Fichero2 = open('ua2.xml', 'r')
    passwords = open('passwords', 'r')
    cont1 = 0
    cont2 = 0
    cont3 = 0
    for fila1 in Fichero1:
        if cont1 == 1:
            fila1 = fila1.split('"')
            if dir_sip == fila1[1]:
                FicheroSeleccionado = open('ua1.xml', 'r')
        cont1 = cont1 + 1
    for fila2 in Fichero2:
        if cont2 == 1:
            fila2 = fila2.split('"')
            if dir_sip == fila2[1]:
                FicheroSeleccionado = open('ua2.xml', 'r')
        cont2 = cont2 + 1
    for fila in FicheroSeleccionado:
        if cont3 == 1:
            fila = fila.split('"')
            contraseñaCliente = fila[3]
        cont3 = cont3 + 1
    for line in passwords:
        linea = line.split(' ')
        if linea[0] == dir_sip:
            line = line.split('=')
            line = line[1].split("\n")
            contraseña = line[0]
    passClient = hashlib.sha1()
    passClient.update(bytes(contraseñaCliente + str(nonce), 'utf-8'))
    Pass = hashlib.sha1()
    Pass.update(bytes(contraseña + str(nonce), 'utf-8'))
    if passClient.digest() == Pass.digest():
        registrate = 1
    else:
        registrate = 0
    return registrate


#log
def NuevoLog(Evento):

    fichero = open('LogProxy.txt', 'a+')
    HoraActual = time.gmtime(time.time())
    HoraActual = time.strftime('%Y%m%d%H%M%S', HoraActual)
    fichero.write(str(HoraActual) + ' ' + Evento + '\r\n')


class XMLHandler(ContentHandler):
    """
    Echo server class
    """
    def __init__(self):

        self.dicc = {}  # dicc donde defino las variables del archivo xml
        self.lista = []  # lista donde guardo los diccionarios

    def startElement(self, name, attrs):  # defino las etiquetas de mi archivo

        if name == 'server':
            self.dicc[name] = {(name + '_name'): attrs.get('name', ""), (name + '_ip'): attrs.get('ip', ""), (name + '_puerto'): attrs.get('puerto', "")}
            self.lista.append(self.dicc)
            self.dicc = {}
        elif name == 'database':
            self.dicc[name] = {(name + '_path'): attrs.get('path', ""), (name + '_passwdpath'): attrs.get('passwdpath', "")}
            self.lista.append(self.dicc)
            self.dicc = {}
        elif name == 'log':
            self.dicc[name] = {(name + '_path'): attrs.get('path', "")}
            self.lista.append(self.dicc)
            self.dicc = {}

    def get_tags(self):

        return self.lista

#definir algo para que el audio_file tenga un valor
#audio_file = mp32rtp


class SIPRegisterHandler(socketserver.DatagramRequestHandler):
    """
    Echo server class
    """
    # Creo un diccionario de clientes almacenados
    clientes_almacenados = {}

    def json2registered(self):
        """
        Comprobacion existencia fichero
        """
        try:
            with open('registered.json', 'r') as fichero:
                self.clientes_almacenados = json.load(fichero)
        except:
            print('No existe el fichero json. Creando..')
            pass

    def register2json(self):
        """
        Creo el fichero
        """
        with open('registered.json', 'w') as fichero:
            json.dump(self.clientes_almacenados, fichero)
            fichero.close()

    def TiempoExpiracion(self, datos, dir_sip, uaserver_puerto):
        """
        Comprueba si el cliente ha expirado y le elimina del diccionario de clientes.
        """
        if len(self.clientes_almacenados) == 0:
            self.json2registered()
        #print('IP del cliente: ' + self.client_address[0])
        #print('PUERTO del cliente: ' + str(self.client_address[1]))
        #print(datos)
        #print('Segundos para EXPIRAR: ' + datos[4])
        if datos[0] == 'REGISTER':
            #print('IMPRIMO DATOS:',datos)
            #puerto_servidor = datos[1].split(':')[2]
            #print('imprimo puerto servidor:', puerto_servidor)
            direccion = datos[1].split(':')[1]
            #print("tiempo de exp", datos[4])
            tiempo_exp = time.gmtime(time.time() + int(datos[4]))
            tiempo_exp = time.strftime('%Y-%m-%d %H:%M:%S', tiempo_exp)
            HoraActual = time.gmtime(time.time())
            HoraActual = time.strftime('%Y-%m-%d %H:%M:%S', HoraActual)
            #print("dirr: " + direccion + " client: " + self.client_address[0])
            self.clientes_almacenados[dir_sip] = [self.client_address[0], tiempo_exp, uaserver_puerto]
            #print('Address: ' + self.client_address[0])
            #print('Fecha y hora actual: ' + HoraActual)
            #print('Expires: ' + tiempo_exp)
            #print('clientes antes', self.clientes_almacenados)
            if (tiempo_exp <= HoraActual):
                del self.clientes_almacenados[dir_sip]
                print('Eliminada direccion: ' + dir_sip)
            self.wfile.write(b"SIP/2.0 200 OK\r\n\r\n")
            #print('clientes despues', self.clientes_almacenados)
            #if int(datos[4]) == 0:  # Compruebo si expires = 0.
            #    print('datos4:', datos[4])
            #    print('cliente:', clientes_almacenados[dir_sip])
            #    del self.clientes_almacenados[dir_sip]  # Si es = 0 --> fuera.
        self.register2json()
        self.json2registered()
        #print('Almacenado en mi diccionario: ', self.clientes_almacenados)

    def handle(self):

        autorizacion = 0
        # Escribe dirección y puerto del cliente (de tupla client_address)
        line = self.rfile.read()
        print('El cliente nos manda ', line.decode('utf-8'))
        datos = line.decode('utf-8').split()
        #print('imprimo datos para buscar el puerto', datos)
        dir_sip = datos[1].split(':')[1]
        #print('esta es mi direccion sip que saco arriba', dir_sip)
        uaserver_puerto = datos[1].split(':')[-1]
        #print('probando puerto:', uaserver_puerto)
        #print('buscando mi puerto', uaserver_puerto)
        #print('mi direccion sip:', dir_sip)
        Evento = 'Receieved from ' + str(self.client_address[0]) + ':' + str(self.client_address[1]) + ': ' + line.decode('utf-8')
        NuevoLog(Evento)
        usuarioRegistrado = 0
        #print('IP del cliente: ' + self.client_address[0])
        #print('PUERTO del cliente: ' + str(self.client_address[1]))
        #print('imprimo datos', datos)
        if datos[0] == 'INVITE':
            #print('yo soy datos', datos)
            print("USUARIO0", usuarioRegistrado)
            with open('registered.json', 'r') as fichero:
                self.clientes_almacenados = json.load(fichero)
                if self.clientes_almacenados != 0:
                    try:
                        PuertoClienteInvitado = self.clientes_almacenados[datos[1].split(":")[1]]
                        PuertoClienteInvitado = PuertoClienteInvitado[2]
                        print("PuertoClienteInvitado ", PuertoClienteInvitado)
                        for linea in self.clientes_almacenados:
                            if datos[1].split(":")[1] == linea:
                                #print(datos[1].split(":"))
                                #print('PCI:',PuertoClienteInvitado)
                                print('El cliente invitado está registrado.')
                                usuarioRegistrado = 1
                    except:
                        pass
            print("USUARIO1", usuarioRegistrado)
            if usuarioRegistrado == 0:
                print('SIP/2.0 404 User Not Found')
                self.wfile.write(b'SIP/2.0 404 User Not Found\r\n')
                Evento = 'Sent to ' + str(self.client_address[0]) + ':' + str(self.client_address[1]) + ': ' + line.decode('utf-8')
                NuevoLog(Evento)
            else:
                print('Enviamos a ' + datos[1].split(":")[1] + ' al puerto ' + PuertoClienteInvitado)
                my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                my_socket.connect(('127.0.0.1', int(PuertoClienteInvitado)))
                my_socket.send(line)
                data = my_socket.recv(1024)
                data_recibido = data.decode('utf-8').split()
                imprimir = data.decode('utf-8')
                print(imprimir)
                self.wfile.write(data)
                Evento = 'Sent to ' + str(self.client_address[0]) + ':' + str(self.client_address[1]) + ': ' + line.decode('utf-8')
                NuevoLog(Evento)
        elif datos[0] == 'BYE':
            with open('registered.json', 'r') as fichero:
                self.clientes_almacenados = json.load(fichero)
                if self.clientes_almacenados != 0:
                    PuertoClienteInvitado = self.clientes_almacenados[datos[1].split(":")[1]]
                    PuertoClienteInvitado = PuertoClienteInvitado[2]
                    print("PuertoClienteInvitado ", PuertoClienteInvitado)
                    for linea in self.clientes_almacenados:
                        if datos[1].split(":")[1] == linea:
                            #print(datos[1].split(":"))
                            #print('PCI:',PuertoClienteInvitado)
                            print('El cliente invitado está registrado.')
                            usuarioRegistrado = 1
            linea = datos[0] + ' sip:' + dir_sip + ' SIP/2.0\r\n'
            print('Enviando: ' + linea)
            print('Ha acabado la transmisión del audio. Cerrando conexión.')
            my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            my_socket.connect(('', int(PuertoClienteInvitado)))
            my_socket.send(bytes(linea, 'utf-8'))
            self.wfile.write(b'SIP/2.0 200 OK\r\n\r\n')
            Evento = 'Sent to ' + str(self.client_address[0]) + ':' + str(self.client_address[1]) + ': ' + line.decode('utf-8')
            NuevoLog(Evento)
        elif datos[0] == 'ACK':
            with open('registered.json', 'r') as fichero:
                self.clientes_almacenados = json.load(fichero)
                if self.clientes_almacenados != 0:
                    PuertoClienteInvitado = self.clientes_almacenados[datos[1].split(":")[1]]
                    PuertoClienteInvitado = PuertoClienteInvitado[2]
                    print("PuertoClienteInvitado ", PuertoClienteInvitado)
                    for linea in self.clientes_almacenados:
                        if datos[1].split(":")[1] == linea:
                            #print(datos[1].split(":"))
                            #print('PCI:',PuertoClienteInvitado)
                            print('El cliente invitado está registrado.')
                            usuarioRegistrado = 1
            my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            my_socket.connect(('127.0.0.1', int(PuertoClienteInvitado)))
            my_socket.send(line)
            Evento = 'Sent to ' + str(self.client_address[0]) + ':' + str(self.client_address[1]) + ': ' + line.decode('utf-8')
            NuevoLog(Evento)
        elif datos[0] == 'REGISTER':
            #dir_sip = datos[1].split(':')[1]
            registrate = HashLib(dir_sip)
            if registrate == 1:
                for info in datos:
                    #print(info)
                    if info == 'Authorization:':
                        autorizacion = 1
                #print(autorizacion)
                if autorizacion == 1:
                    self.TiempoExpiracion(datos, dir_sip, uaserver_puerto)
                    Evento = 'Sent to ' + str(self.client_address[0]) + ':' + str(self.client_address[1]) + ': ' + '200 OK'
                    NuevoLog(Evento)
                elif autorizacion == 0:
                    self.wfile.write(b'SIP/2.0 401 Unauthorized\r\n')
                    self.wfile.write(b'WWW Authenticate: Digest nonce="43558789"')
                    Evento = 'Sent to ' + str(self.client_address[0]) + ':' + str(self.client_address[1]) + ': ' + 'SIP/2.0 401 Unauthorized\r\n' + 'WWW Authenticate: Digest nonce="43558789"'
                    NuevoLog(Evento)
            else:
                self.wfile.write(b'SIP/2.0 401 Unauthorized\r\n')
        elif datos[0] != ('INVITE' and 'BYE' and 'REGISTER' and 'ACK'):
            #dir_sip = datos[1].split(':')[1]
            self.wfile.write(b'SIP/2.0 405 Method Not Allowed')
            Evento = 'Sent to ' + str(self.client_address[0]) + ':' + str(self.client_address[1]) + ': ' + line.decode('utf-8')
            NuevoLog(Evento)
        else:
            self.wfile.write(b'SIP/2.0 400 Bad Request')
            Evento = 'Sent to ' + str(self.client_address[0]) + ':' + str(self.client_address[1]) + ': ' + line.decode('utf-8')
            NuevoLog(Evento)

parser = make_parser()
cHandler = XMLHandler()
parser.setContentHandler(cHandler)
parser.parse(open(sys.argv[1]))
lista = cHandler.get_tags()

# Posicion de las variables del archivo xml
server_name = lista[0]['server']['server_name']
server_ip = lista[0]['server']['server_ip']
server_puerto = lista[0]['server']['server_puerto']
database_path = lista[1]['database']['database_path']
database_passwdpath = lista[1]['database']['database_passwdpath']
log_path = lista[2]['log']['log_path']

#tengo que poner a escuchar al proxy al cliente, recibir los datos y enviarlos al servidor
Evento = 'Starting...'
NuevoLog(Evento)
serv = socketserver.UDPServer(('127.0.0.1', 5062), SIPRegisterHandler)
print('Server MiServer listening at port ' + '5062' + '...')
try:
    serv.serve_forever()
except KeyboardInterrupt:
    Evento = 'Finishing'
    NuevoLog(Evento)
    print('Finalizado servidor.')
