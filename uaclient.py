#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from uaserver import XMLHandler
from uaserver import Log
import sys
import socket
import os
import time


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
    TO = UA['regproxy_ip'] + ':' + UA['regproxy_puerto']
    # Enviamos diferentes cosas según el método
    if METHOD == "REGISTER":
        try:
            OPTION = int(OPTION)
        except ValueError:
            sys.exit("Usage: int OPTION Required")
        LINE = UA['account_username'] + ":" + UA['uaserver_puerto']
        EXPIRES = "Expires: " + str(OPTION) + '\r\n\r\n'
        SEND = METHOD + " sip:" + LINE + " SIP/2.0\r\n" + EXPIRES
        print "Enviado:\r\n" + METHOD + " sip:" + LINE + " SIP/2.0\n" + EXPIRES
        my_socket.send(SEND)
        Log().Log(UA['log_path'], 'Init/end', TO, 'Starting...')
        Log().Log(UA['log_path'], 'send', TO, SEND)

    elif METHOD == "INVITE":
        print "Enviando:\r\n" + METHOD + " sip:" + OPTION + " SIP/2.0"
        print "Content-type: application/sdp\r\n\r\n"
        APPLICATION = "Content-type: application/sdp\r\n\r\n"
        HEAD = METHOD + " sip:" + OPTION + " SIP/2.0\r\n" + APPLICATION
        O = "o=" + UA['account_username'] + " " + UA['uaserver_ip'] + " \r\n"
        M = "m=audio " + UA['rtpaudio_puerto'] + " RTP\r\n"
        BODY = "v=0\r\n" + O + "s=mysession\r\n" + "t=0\r\n" + M
        print BODY
        SEND = HEAD + BODY
        my_socket.send(SEND)
        Log().Log(UA['log_path'], 'send', TO, SEND)

    elif METHOD == "BYE":
        SEND = METHOD + " sip:" + OPTION + " SIP/2.0\r\n\r\n"
        print "Enviando:\r\n" + METHOD + " sip:" + OPTION + " SIP/2.0"
        my_socket.send(SEND)
        Log().Log(UA['log_path'], 'send', TO, SEND)
    else:
        sys.exit('Usage: Method Not Allowed')

    try:
        data = my_socket.recv(1024)
    except socket.error:
        SOCKET_ERROR = UA['regproxy_ip'] + " PORT:" + UA['regproxy_puerto']
        sys.exit("Error: No server listening at " + SOCKET_ERROR)
        Log().Log(UA['log_path'], 'error', ' ', SOCKET_ERROR)

    print 'Recibido\r\n', data
    Log().Log(UA['log_path'], 'receive', TO, data)

    r400 = "SIP/2.0 400 Bad Request\r\n\r\n"
    r404 = "SIP/2.0 404 User Not Found\r\n\r\n"
    r_404 = "SIP/2.0 404 Not Found\r\n\r\n"
    r405 = "SIP/2.0 405 Method Not Allowed\r\n\r\n"
    if data == r400 or data == r404 or data == r405 or data == r_404:
        sys.exit()
    else:
        if METHOD == "INVITE":
            #He recibido los tres mensajes a la vez, en una misma línea
            METHOD = 'ACK'
            SEND = METHOD + " sip:" + OPTION + " SIP/2.0\r\n\r\n"
            print "Enviando: " + METHOD + " sip:" + OPTION + " SIP/2.0\r\n\r\n"
            my_socket.send(SEND)
            rcv_Ip = data.split("o=")[1].split(" ")[1].split("s")[0]
            rcv_Port = data.split("m=")[1].split(" ")[1]
            os.system("chmod 777 mp32rtp")
            aEjecutar = "./mp32rtp -i " + rcv_Ip + " -p " + rcv_Port
            aEjecutar += " < " + UA['audio_path']
            aEjecutar_cvlc = 'cvlc rtp://@' + rcv_Ip + ':' + rcv_Port
            aEjecutar_cvlc += " 2> /dev/null"
            print "Vamos a ejecutar", aEjecutar
            print "Vamos a ejecutar", aEjecutar_cvlc
            os.system(aEjecutar)
            os.system(aEjecutar + "&")
            print("Ha terminado la ejecución de fich de audio")
            Log().Log(UA['log_path'], 'send', TO, SEND)

        elif METHOD == 'BYE':
            Log().Log(UA['log_path'], 'Init/end', ' ', 'Finishing...\n')

# Cerramos todo
my_socket.close()
