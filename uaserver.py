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
                # Las utilizaremos para el envío de rtp
                receptor_Ip = line.split("o=")[1].split(" ")[1].split("s")[0]
                receptor_Puerto = line.split("m=")[1].split(" ")[1]
                Rtp['receptor_Ip'] = receptor_Ip
                Rtp['receptor_Puerto'] = receptor_Puerto
                #Respondemos al invite
                respuesta = "SIP/2.0 100 Trying\r\n\r\n"
                respuesta += "SIP/2.0 180 Ringing\r\n\r\n"
                respuesta += "SIP/2.0 200 OK\r\n"
                respuesta += "Content type:application/sdp" + "\r\n\r\n"
                O = "o=" + UA['account_username'] + " " + UA['uaserver_ip']
                # Colocamos nuestro RTP puerto para que nos manden ahí
                M = "m=audio " + UA['rtpaudio_puerto'] + " RTP\r\n"
                CUERPO = "v=0\r\n" + O + " \r\ns=mysession\r\n" + "t=0\r\n" + M
                respuesta += CUERPO
                self.wfile.write(respuesta)
               
            elif Method == 'ACK':
                os.system("chmod 777 mp32rtp")
                aEjecutar = './mp32rtp -i ' + Rtp['receptor_Ip'] + ' -p '
                aEjecutar += Rtp['receptor_Puerto'] + " < " + UA['audio_path']
                print "Vamos a ejecutar", aEjecutar
                os.system(aEjecutar)
                print("Ha terminado la ejecución de fich de audio")
                
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
    Rtp = {}
    parser = make_parser()
    cHandler = XMLHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG))
    UA = cHandler.get_tags()
    # Creamos servidor y escuchamos
    serv = SocketServer.UDPServer(("", int(UA['uaserver_puerto'])), ServerHandler)
    print "Listening..."
    serv.serve_forever()
