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
        DESTINO = self.client_address[0] + ' ' + str(self.client_address[1])
        fich = open(PR['log_logpath'], 'a')
        while 1:
            line = self.rfile.read()
            if not line:
                break
            LINE = line.replace("\r\n", ' ') + '\n'
            METHODS = ['REGISTER', 'INVITE', 'ACK', 'BYE']
            line_partida = line.split(":")
            Method = line_partida[0].split(" ")[0]
            if not Method in METHODS:
                self.wfile.write("SIP/2.0 405 Method Not Allowed\r\n\r\n")
            #Si tenemos Register, procedemos a rellenar nuestro Registro
            if Method == "REGISTER":
                #Primero comprobamos los tiempos de expiración
                for Client in Registro.keys():
                    #Vamos comparando con el tiempo de cada clave-valor
                    Tiempo = Registro[Client][2]
                    if time.time() >= Tiempo:
                        print Client + " Borrado\r\n"
                        del Registro[Client]                        
                Clave = line_partida[1]
                Puerto_UA = line_partida[2].split(" ")[0]
                Expires = line_partida[3].split(" ")[1]
                Time = time.time() + int(Expires)
                Valores = [self.client_address[0], Puerto_UA, Time]
                Registro[Clave] = Valores
                print Clave + " Registrado\r\n"
                #Si entramos con un valor a 0, somos borrados
                if int(Expires) == 0:
                    del Registro[Clave]
                    print Client + " Borrado\r\n"
                self.register2file()
                self.wfile.write("SIP/2.0 200 OK\r\n\r\n")
                Time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
                fich.write(Time + ' Received from ' + DESTINO + ' ' + LINE)
                fich.write(Time + ' Sent to ' + DESTINO + " SIP/2.0 200 OK\n")
                                
            elif Method == "INVITE":
                Time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
                fich.write(Time + ' Received from ' + DESTINO + ' ' + LINE)
                To_name = line_partida[1].split(" ")[0]
                for Client in Registro:
                    if To_name == Client:
                        To_IP = Registro[Client][0]                        
                        To_Port = Registro[Client][1]
                        #Creamos socket, configuramos y lo atamos a un 
                        #servidor/puerto, sk es my_socket, por pep8 sk
                        sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                        sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        sk.connect((To_IP, int(To_Port)))
                        sk.send(line)
                        TO = To_IP + ' ' + To_Port
                        fich.write(Time + ' Sent to ' + TO + ' ' + LINE)
                        print "INVITE Enviado a " + To_name + '\r\n'
                        try:
                            data = sk.recv(1024)
                        except socket.error:
                            SOCKET_ERROR = To_IP + " PORT:" + To_Port
                            sys.exit("No server listening at " + SOCKET_ERROR)
                        print 'Respuesta recibida de ' + To_name + '\r\n'
                        #Tenemos directamente una conexión con el que nos abrió 
                        # el socket enviando el INVITE
                        self.wfile.write(data)
                        DATA = data.replace("\r\n", ' ') + '\n'
                        fich.write(Time + ' Received from ' + TO + ' ' + DATA)
                        fich.write(Time + ' Sent to ' + DESTINO + ' ' + DATA)
                    
                    elif Registro.has_key(To_name) == False:
                        self.wfile.write("SIP/2.0 404 User Not Found\r\n\r\n")
                               
            elif Method == "ACK":
                Time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
                fich.write(Time + ' Received from ' + DESTINO + ' ' + LINE)
                To_name = line_partida[1].split(" ")[0]
                print 'ACK recibido y reenviado a ' + To_name + '\r\n'
                for Client in Registro:
                    if Client == To_name:
                        To_IP = Registro[Client][0]                        
                        To_Port = Registro[Client][1]
                TO = To_IP + ' ' + To_Port
                fich.write(Time + ' Sent to ' + TO + ' ' + LINE)
                #Creamos socket, configuramos y lo atamos a un servidor/puerto
                sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sk.connect((To_IP, int(To_Port)))
                sk.send(line)
                
            elif Method == "BYE":
                Time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
                fich.write(Time + ' Received from ' + DESTINO + ' ' + LINE)
                To_name = line_partida[1].split(" ")[0]
                print 'BYE enviado a ' + To_name + '\r\n'
                for Client in Registro:
                    if Client == To_name:
                        To_IP = Registro[Client][0]                        
                        To_Port = Registro[Client][1]
                TO = To_IP + ' ' + To_Port
                fich.write(Time + ' Sent to ' + TO + ' ' + LINE)
                #Creamos socket, configuramos y lo atamos a un servidor/puerto
                sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                sk.connect((To_IP, int(To_Port)))
                sk.send(line)
                try:
                    data = sk.recv(1024)
                except socket.error:
                    SOCKET_ERROR = To_IP + " PORT:" + To_Port
                    sys.exit("No server listening at " + SOCKET_ERROR)
                print 'Respuesta recibida de ' + To_name + '\r\n'
                #Tenemos directamente una conexión con el que nos abrió 
                # el socket enviando el INVITE
                self.wfile.write(data)
                # cerramos el socket al final del todo, ya no lo utilizremos +
                sk.close()
                DATA = data.replace("\r\n", ' ') + '\n'
                fich.write(Time + ' Received from ' + TO + ' ' + DATA)
                fich.write(Time + ' Sent to ' + DESTINO + ' ' + DATA)
                               
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
    # Abrimos fichero log_proxy.txt
    fich = open(PR['log_logpath'], 'w')
    Time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
    fich.write(Time + ' Starting...\n')
    fich.close()
    print "Server " + PR['server_name'] + "listening at port " + LISTENING_PORT
    serv.serve_forever()
