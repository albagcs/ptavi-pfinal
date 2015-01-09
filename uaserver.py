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
import time


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


class Log(ContentHandler):
    def Log(self, fichero, tipo, to, message):
        fich = open(fichero, 'a')
        Time = time.strftime('%Y%m%d%H%M%S', time.gmtime())
        message = message.replace('\r\n', ' ') + '\n'
        if tipo == 'send':
            fich.write(Time + ' Sent to ' + to + ': ' + message)
        elif tipo == 'receive':
            fich.write(Time + ' Received from ' + to + ': ' + message)
        elif tipo == 'error':
            fich.write(Time + "Error: No server listening at: " + message)
        elif tipo == 'Init/end':
            fich.write(Time + ' ' + message)
        fich.close()


class ServerHandler(SocketServer.DatagramRequestHandler):

    def handle(self):

        while 1:
            line = self.rfile.read()
            if not line:
                break
            FROM = self.client_address[0] + ' ' + str(self.client_address[1])
            METHODS = ['INVITE', 'ACK', 'BYE']
            Method = line.split(" ")[0]
            print "El cliente nos manda " + line
            if not Method in METHODS:
                response = "SIP/2.0 405 Method Not Allowed\r\n\r\n"
                self.wfile.write(response)
                Log().Log(UA['log_path'], 'receive', FROM, response)
            else:
                EOL = line.split('\r\n')[0].split(' ')[2]
                sip = line.split(":")[0].split(' ')[1]
                if  sip != 'sip' or EOL != 'SIP/2.0':
                    response = "SIP/2.0 400 Bad Request\r\n\r\n"
                    self.wfile.write(response)
                    Log().Log(UA['log_path'], 'receive', FROM, response)
                elif Method == 'INVITE':
                    Log().Log(UA['log_path'], 'receive', FROM, line)
                    # Las utilizaremos para el envío de rtp
                    rcv_Ip = line.split("o=")[1].split(" ")[1].split("s")[0]
                    rcv_Port = line.split("m=")[1].split(" ")[1]
                    Rtp['rcv_Ip'] = rcv_Ip
                    Rtp['rcv_Port'] = rcv_Port
                    #Respondemos al invite
                    response = "SIP/2.0 100 Trying\r\n\r\n"
                    response += "SIP/2.0 180 Ringing\r\n\r\n"
                    response += "SIP/2.0 200 OK\r\n"
                    response += "Content type:application/sdp" + "\r\n\r\n"
                    O = "o=" + UA['account_username'] + " " + UA['uaserver_ip']
                    # Colocamos nuestro RTP puerto para que nos manden ahí
                    M = "m=audio " + UA['rtpaudio_puerto'] + " RTP\r\n"
                    BODY = "v=0\r\n" + O + " \r\ns=mysession\r\n" + "t=0\r\n"
                    response += BODY + M
                    self.wfile.write(response)
                    Log().Log(UA['log_path'], 'send', FROM, response)

                elif Method == 'ACK':
                    Log().Log(UA['log_path'], 'receive', FROM, line)
                    os.system("chmod 777 mp32rtp")
                    aEjecutar = "./mp32rtp -i " + Rtp['rcv_Ip'] + " -p "
                    aEjecutar += Rtp['rcv_Port'] + " < " + UA['audio_path']
                    aEjecutar_cvlc = 'cvlc rtp://@' + Rtp['rcv_Ip'] + ':'
                    aEjecutar_cvlc += Rtp['rcv_Port'] + " 2> /dev/null"
                    print "Vamos a ejecutar", aEjecutar
                    print "Vamos a ejecutar", aEjecutar_cvlc
                    os.system(aEjecutar)
                    os.system(aEjecutar_cvlc + "&")
                    print("Ha terminado la ejecución de fich de audio")

                elif Method == 'BYE':
                    Log().Log(UA['log_path'], 'receive', FROM, line)
                    response = "SIP/2.0 200 OK\r\n\r\n"
                    self.wfile.write(response)
                    Log().Log(UA['log_path'], 'send', FROM, response)
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
    s = SocketServer.UDPServer(("", int(UA['uaserver_puerto'])), ServerHandler)
    print "Listening..."
    Log().Log(UA['log_path'], 'Init/end', ' ', 'Starting...')
    try:
        s.serve_forever()
    except KeyboardInterrupt:
        Log().Log(UA['log_path'], 'Init/end', ' ', 'Finishing...\n')
        print ('Servidor Interrumpido (Ctrl + C)')
