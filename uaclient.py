#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from uaserver import XMLHandler
import sys
import socket

if __name__ == "__main__":
    """
    Programa principal
    """
    try:
        CONFIG = sys.argv[1]
        METHOD = sys.argv[2].upper()
        OPTION = sys.argv[3]
    except IndexError:
        sys.exit("Usage: python uaclient.py config method option")
    parser = make_parser()
    cHandler = XMLHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG))
    UA = cHandler.get_tags()
    # Creamos el socket, lo configuramos y lo atamos a un servidor/puerto
    my_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    my_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    my_socket.connect((UA['regproxy_ip'], int(UA['regproxy_puerto'])))
    # Enviamos diferentes cosas según el método
    if METHOD == "REGISTER":
        LINE = UA['account_username'] + ":" + UA['uaserver_puerto']
        print "Enviando:\r\n" + METHOD + " sip:" + LINE + " SIP/2.0"
        print "Enviando: " + "EXPIRES:" + str(OPTION) + '\r\n\r\n'
        LINE_EXPIRES = "Expires: " + str(OPTION) + '\r\n\r\n'
        my_socket.send(METHOD + " sip:" + LINE + " SIP/2.0\r\n" + LINE_EXPIRES)
        
    elif METHOD == "INVITE":
        print "Enviando:\r\n" + METHOD + " sip:" + OPTION + " SIP/2.0"
        print "Content type: application/sdp\r\n\r\n" 
        APPLICATION = "Content type:application/sdp" + "\r\n\r\n"
        CABECERAS = METHOD + " sip:" + OPTION + " SIP/2.0\r\n" + APPLICATION
        O = "o=" + UA['account_username'] + " " + UA['uaserver_ip'] + " \r\n"
        M = "m=audio " + UA['rtpaudio_puerto'] + " RTP\r\n"
        CUERPO = "v=0\r\n" + O + "s=mysession\r\n" + "t=0\r\n" + M
        print CUERPO
        my_socket.send(CABECERAS + CUERPO)
        
    elif METHOD == "BYE":
        print "Enviando:\r\n" + METHOD + " sip:" + OPTION + " SIP/2.0"
        my_socket.send(METHOD + " sip:" + OPTION + " SIP/2.0\r\n\r\n")
        
    else:
        my_socket.send(METHOD + " sip: Método no registrado")
   
    try:
        data = my_socket.recv(1024)
    except socket.error:
        SOCKET_ERROR = UA['regproxy_ip'] + " PORT:" + UA['regproxy_puerto']
        sys.exit("No server listening at " + SOCKET_ERROR)
    print 'Recibido\r\n', data
    
    if data == "SIP/2.0 404 User Not Found\r\n\r\n":
        sys.exit(" ")
    else:
        if METHOD == "INVITE":
            #He recibido los tres mensajes a la vez, en una misma línea
            METHOD = 'ACK'
            print "Enviando: " + METHOD + " sip:" + OPTION + " SIP/2.0\r\n\r\n"
            my_socket.send(METHOD + " sip:" + OPTION + " SIP/2.0\r\n\r\n")
            
print "Terminando socket..."
# Cerramos todo
my_socket.close()
print "Fin."        

