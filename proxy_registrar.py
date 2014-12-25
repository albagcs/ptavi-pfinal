#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para un servidor SIP
en UDP simple
"""

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import SocketServer
import socket
import sys
import time


class XMLHandler(ContentHandler):

    def __init__(self):
        """
        Constructor. Inicializamos las variables
        """
        self.XML = {
            'server': ['name', 'ip', 'puerto'],
            'database': ['path', 'passwdpath'],
            'log': ['logpath']
        }

        self.config = {}

    def startElement(self, name, attrs):
        """
        Método que se llama cuando se abre una etiqueta

        """
        if name in self.XML:
            for attr in self.XML[name]:
                self.config[name + "_" + attr] = attrs.get(attr, "")
                if name + "_" + attr == 'server_ip':
                    if self.config['server_ip'] == "":
                        self.config['server_ip'] = '127.0.0.1'

    def get_tags(self):
        return self.config

class SIPRegisterHandler(SocketServer.DatagramRequestHandler):
    """
    SIP server class
    """

    def handle(self):
        print self.client_address
        while 1:
            line = self.rfile.read()
            if not line:
                break
            METHODS = ['REGISTER', 'INVITE', 'ACK', 'BYE']
            line_partida = line.split(":")
            Method = line_partida[0].split(" ")[0]
            if not Method in METHODS:
                self.wfile.write("SIP/2.0 405 Method Not Allowed\r\n\r\n")
            #Si tenemos Register, procedemos a rellenar nuestro Registro
            if Method == "REGISTER":
                #Primero comprobamos los tiempos de expiracion
                for Client in Registro.keys():
                    #Vamos comparando con el tiempo de cada clave-valor
                    Tiempo = Registro[Client][2]
                    if time.time() >= Tiempo:
                        print Client + " Borrado"
                        del Registro[Client]                        
                Clave = line_partida[1]
                Puerto_UA = line_partida[2].split(" ")[0]
                Expires = line_partida[3].split(" ")[1]
                Time = time.time() + int(Expires)
                Valores = [self.client_address[0], Puerto_UA, Time]
                Registro[Clave] = Valores
                print Clave + " Registrado"
                #Si entramos con un valor a 0, somos borrados
                if int(Expires) == 0:
                    del Registro[Clave]
                    print Client + " Borrado"
                self.register2file()
                self.wfile.write("SIP/2.0 200 OK\r\n\r\n")
                
            elif Method == "INVITE":
                To_name = line_partida[1].split(" ")[0]
                print Registro
                for Client in Registro:
                    if Client == To_name:
                        To_IP = Registro[Client][0]                        
                        To_Port = Registro[Client][1]
                        print To_IP + To_Port
                #Creamos socket, configuramos y lo atamos a un servidor/puerto
                my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                my_socket.connect((To_IP, int(To_Port)))
                my_socket.send(line)
                print "INVITE Enviado a " + To_name
                try:
                    data = my_socket.recv(1024)
                except socket.error:
                    SOCKET_ERROR = To_IP + " PORT:" + To_Port
                    sys.exit("No server listening at " + SOCKET_ERROR)
                print 'Recibido\r\n', data + 'from ' + To_name
                #Tenemos directamente una conexión con el que nos abrió 
                # el socket enviando el INVITE
                self.wfile.write(data)
                my_socket.close()
                #else:
                #print "NO REGISTRADO"
                #self.wfile.write("SIP/2.0 404 User Not Found\r\n\r\n")
            elif Method == "ACK":
                To_name = line_partida[1].split(" ")[0]
                for Client in Registro:
                    if Client == To_name:
                        To_IP = Registro[Client][0]                        
                        To_Port = Registro[Client][1]
                        print To_IP + To_Port
                #Creamos socket, configuramos y lo atamos a un servidor/puerto
                my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                my_socket.connect((To_IP, int(To_Port)))
                my_socket.send(line)
                my_socket.close()
                
            else:
                self.wfile.write("SIP/2.0 400 Bad Request\r\n\r\n")
                 
    def register2file(self):
        """ Método que escribirá en nuestro fichero"""
        fichero = open('database.txt', 'w')
        fichero.write("User\tIP\tPuerto\tExpires\n")
        for Client in Registro:
            IP = Registro[Client][0]
            Port = Registro[Client][1]
            Tiempo = time.gmtime(Registro[Client][2])
            Time = time.strftime('%Y-%m-%d %H:%M:%S', Tiempo)
            fichero.write(Client + '\t' + IP + '\t' + Port + '\t' + Time + '\n')
        fichero.close()

if __name__ == "__main__":
    try:
        CONFIG = sys.argv[1]
    except IndexError:
        sys.exit("Usage: python proxy_registrar.py config")
    parser = make_parser()
    cHandler = XMLHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG))
    PR = cHandler.get_tags()
    LISTENING_PORT = PR['server_puerto']
    Registro = {}
    # Creamos servidor Registrar y escuchamos
    serv = SocketServer.UDPServer(("", int(LISTENING_PORT)), SIPRegisterHandler)
    print "Server " + PR['server_name'] + "listening at port " + LISTENING_PORT
    serv.serve_forever()
