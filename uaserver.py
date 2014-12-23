#!/usr/bin/python
# -*- coding: iso-8859-15 -*-
"""
Clase (y programa principal) para un servidor SIP
"""

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
import SocketServer
import sys
import os

class XMLHandler(ContentHandler):

    def __init__(self):
        """
        Constructor. Inicializamos las variables
        """
        self.XML = {
            'account': ['username', 'passwd'],
            'uaserver': ['ip', 'puerto'],
            'rtpaudio': ['puerto'],
            'regproxy': ['ip', 'puerto'],
            'log': ['path'],
            'audio': ['path']
        }

        self.config = {}

    def startElement(self, name, attrs):
        """
        Método que se llama cuando se abre una etiqueta

        """
        if name in self.XML:
            for attr in self.XML[name]:
                self.config[name + "_" + attr] = attrs.get(attr, "")
                if name + "_" + attr == 'uaserver_ip':
                    if self.config['uaserver_ip'] == "":
                        self.config['uaserver_ip'] = '127.0.0.1'

    def get_tags(self):
        return self.config

class ServerHandler(SocketServer.DatagramRequestHandler):
  
    def handle(self):
        while 1:
            line = self.rfile.read()
            if not line:
                break
            METHODS = ['INVITE', 'ACK', 'BYE']
            Method = line.split(" ")[0]
            print "El cliente nos manda " + line
            if not Method in METHODS:
                self.wfile.write("SIP/2.0 405 Method Not Allowed\r\n\r\n")
            if Method == 'INVITE':
                respuesta = "SIP/2.0 100 Trying\r\n\r\n"
                respuesta += "SIP/2.0 180 Ringing\r\n\r\n"
                respuesta += "SIP/2.0 200 OK\r\n\r\n"
                self.wfile.write(respuesta)
            elif Method == 'ACK':
                aEjecutar = './mp32rtp -i 127.0.0.1 -p 23032 < ' + sys.argv[3]
                print "Vamos a ejecutar", aEjecutar
                os.system(aEjecutar)
                print(" Ha terminado la ejecución de fich de audio")
            elif Method == 'BYE':
                respuesta = "SIP/2.0 200 OK\r\n\r\n"
                self.wfile.write(respuesta)
            else:
                self.wfile.write("SIP/2.0 400 Bad Request\r\n\r\n")

if __name__ == "__main__":
    try:
        CONFIG = sys.argv[1]
    except IndexError:
        sys.exit("Usage: python server.py config")
    parser = make_parser()
    cHandler = XMLHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG))
    UA = cHandler.get_tags()
    # Creamos servidor y escuchamos
    serv = SocketServer.UDPServer(("", int(UA['uaserver_puerto'])), ServerHandler)
    print "Listening..."
    serv.serve_forever()
