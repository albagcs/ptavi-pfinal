#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para un servidor SIP
en UDP simple
"""

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from uaserver import Log
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
    def Search_User(self, user_name):
        fichero = open(PR['database_path'], 'r')
        data = fichero.readlines()
        fichero.close()
        lines = data[1:]
        i = 0
        Found = False
        while not Found and i < len(lines):
            user = lines[i].split('\t')[0]
            if user_name == user:
                Uas['ip'] = lines[i].split('\t')[1]
                Uas['puerto'] = lines[i].split('\t')[2]
                Found = True
            i = i + 1
        return Found

    def handle(self):
        UAC = self.client_address[0] + ' ' + str(self.client_address[1])
        while 1:
            line = self.rfile.read()
            if not line:
                break
            METHODS = ['REGISTER', 'INVITE', 'ACK', 'BYE']
            line_partida = line.split(":")
            Method = line_partida[0].split(" ")[0]
            if not Method in METHODS:
                response = "SIP/2.0 405 Method Not Allowed\r\n\r\n"
                self.wfile.write(response)
                Log().Log(PR['log_logpath'], 'send', UAC, response)
            #Si tenemos Register, procedemos a rellenar nuestro Registro
            elif Method == "REGISTER":
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
                #Si entramos con un valor a 0, somos borrados
                if int(Expires) == 0:
                    del Registro[Clave]
                    print Client + " Borrado\r\n"
                else:
                    print Clave + " Registrado\r\n"
                self.register2file()
                response = "SIP/2.0 200 OK\r\n\r\n"
                self.wfile.write(response)
                Log().Log(PR['log_logpath'], 'receive', UAC, line)
                Log().Log(PR['log_logpath'], 'send', UAC, response)

            elif Method == "INVITE":
                Log().Log(PR['log_logpath'], 'receive', UAC, line)
                To_name = line_partida[1].split(" ")[0]
                Found = self.Search_User(To_name)
                if Found == False:
                    response = "SIP/2.0 404 User Not Found\r\n\r\n"
                    self.wfile.write(response)
                    Log().Log(PR['log_logpath'], 'send', UAC, response)
                else:
                    #Creamos socket, configuramos y lo atamos a un
                    #servidor/puerto, my_sk es my_socket, por pep8 my_sk
                    my_sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    my_sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    my_sk.connect((Uas['ip'], int(Uas['puerto'])))
                    my_sk.send(line)
                    UAS = Uas['ip'] + ' ' + Uas['puerto']
                    Log().Log(PR['log_logpath'], 'send', UAS, line)
                    print "INVITE Enviado a " + To_name + '\r\n'
                    error = False
                    try:
                        data = my_sk.recv(1024)
                    except socket.error:
                        response = "SIP/2.0 404 Not Found\r\n\r\n"
                        self.wfile.write(response)
                        Log().Log(PR['log_logpath'], 'send', UAC, response)
                        error = True
                    if not error:
                        print 'Respuesta recibida de ' + To_name + '\r\n'
                        #Tenemos directamente una conexión con el que nos abrió
                        # el socket enviando el INVITE
                        self.wfile.write(data)
                        Log().Log(PR['log_logpath'], 'receive', UAS, data)
                        Log().Log(PR['log_logpath'], 'send', UAC, data)

            elif Method == "ACK":
                Log().Log(PR['log_logpath'], 'receive', UAC, line)
                To_name = line_partida[1].split(" ")[0]
                self.Search_User(To_name)
                print 'ACK recibido y reenviado a ' + To_name + '\r\n'
                UAS = Uas['ip'] + ' ' + Uas['puerto']
                Log().Log(PR['log_logpath'], 'send', UAS, line)
                #Creamos socket, configuramos y lo atamos a un servidor/puerto
                my_sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                my_sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                my_sk.connect((Uas['ip'], int(Uas['puerto'])))
                my_sk.send(line)

            elif Method == "BYE":
                Log().Log(PR['log_logpath'], 'receive', UAC, line)
                To_name = line_partida[1].split(" ")[0]
                Found = self.Search_User(To_name)
                if Found == False:
                    response = "SIP/2.0 400 Bad Request\r\n\r\n"
                    self.wfile.write(response)
                    Log().Log(PR['log_logpath'], 'send', UAC, response)
                else:
                    UAS = Uas['ip'] + ' ' + Uas['puerto']
                    print 'BYE enviado a ' + To_name + '\r\n'
                    Log().Log(PR['log_logpath'], 'send', UAS, line)
                    #Creamos socket, configuramos y lo atamos a un servidor
                    my_sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                    my_sk.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                    my_sk.connect((Uas['ip'], int(Uas['puerto'])))
                    my_sk.send(line)
                    error = False
                    try:
                        data = my_sk.recv(1024)
                    except socket.error:
                        response = "SIP/2.0 404 Not Found\r\n\r\n"
                        self.wfile.write(response)
                        Log().Log(PR['log_logpath'], 'send', UAC, response)
                        error = True
                    if not error:
                        print 'Respuesta recibida de ' + To_name + '\r\n'
                        #Tenemos directamente una conexión con el que nos abrió
                        # el socket enviando el INVITE
                        self.wfile.write(data)
                        # cerramos el socket, no lo utilizremos +
                        my_sk.close()
                        Log().Log(PR['log_logpath'], 'receive', UAS, data)
                        Log().Log(PR['log_logpath'], 'send', UAC, data)

            else:
                response = "SIP/2.0 400 Bad Request\r\n\r\n"
                self.wfile.write(response)
                Log().Log(PR['log_logpath'], 'send', UAS, response)

    def register2file(self):
        """ Método que escribirá en nuestro fichero"""
        fich = open('database.txt', 'w')
        fich.write("User\tIP\tPuerto\tExpires\n")
        for Client in Registro:
            IP = Registro[Client][0]
            Port = Registro[Client][1]
            Tiempo = time.gmtime(Registro[Client][2])
            Time = time.strftime('%Y%m%d%H%M%S', Tiempo)
            fich.write(Client + '\t' + IP + '\t' + Port + '\t' + Time + '\n')
        fich.close()

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
    Uas = {}
    # Creamos servidor Registrar y escuchamos
    s = SocketServer.UDPServer(("", int(LISTENING_PORT)), SIPRegisterHandler)
    # Escribimos inicio log_proxy.txt
    Log().Log(PR['log_logpath'], 'Init/end', ' ', 'Starting...')
    print "Server " + PR['server_name'] + "listening at port " + LISTENING_PORT
    try:
        s.serve_forever()
    except KeyboardInterrupt:
        Log().Log(PR['log_logpath'], 'Init/end', Uas, 'Finishing...\n')
        print ('Servidor Interrumpido (Ctrl + C)')
