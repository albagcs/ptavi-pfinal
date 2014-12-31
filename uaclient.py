#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from uaserver import XMLHandler
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
    TO = UA['regproxy_ip'] + ':' + UA['regproxy_puerto'] + ': '
    # Enviamos diferentes cosas según el método
    if METHOD == "REGISTER":
        LINE = UA['account_username'] + ":" + UA['uaserver_puerto']
        EXPIRES = "Expires: " + str(OPTION) + '\r\n\r\n'
        SEND =  METHOD + " sip:" + LINE + " SIP/2.0\r\n" + EXPIRES
        print "Enviado:\r\n" + METHOD + " sip:" + LINE + " SIP/2.0\n" + EXPIRES
        my_socket.send(SEND)
        fich = open(UA['log_path'], 'w')
        Time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
        START = 'Starting...\n'
        fich.write(START + Time + ' Sent to ' + TO + SEND.replace('\r\n',' ')
        fich.close()
        
    elif METHOD == "INVITE":
        print "Enviando:\r\n" + METHOD + " sip:" + OPTION + " SIP/2.0"
        print "Content type: application/sdp\r\n\r\n" 
        APPLICATION = "Content type:application/sdp" + "\r\n\r\n"
        HEAD = METHOD + " sip:" + OPTION + " SIP/2.0\r\n" + APPLICATION
        O = "o=" + UA['account_username'] + " " + UA['uaserver_ip'] + " \r\n"
        M = "m=audio " + UA['rtpaudio_puerto'] + " RTP\r\n"
        BODY = "v=0\r\n" + O + "s=mysession\r\n" + "t=0\r\n" + M
        print BODY
        my_socket.send(HEAD + BODY)
        BODY = BODY.replace('\r\n', ' ') + '\n'
        fich = open(UA['log_path'], 'a')
        Time = time.strftime('%Y%m%d%H%M%S', time.gmtime())
        fich.write(Time + ' Sent to ' + TO + HEAD.replace("\r\n", " ") + BODY)
        fich.close()
        
    elif METHOD == "BYE":
        LINE = METHOD + " sip:" + OPTION + " SIP/2.0\r\n\r\n"
        print "Enviando:\r\n" + METHOD + " sip:" + OPTION + " SIP/2.0"
        my_socket.send(LINE)
        fich = open(UA['log_path'], 'a')
        Time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
        fich.write(Time + ' Sent to ' + TO + LINE.replace('\r\n', ' ') + '\n'
        fich.close()
        
    else:
        my_socket.send(METHOD + " sip: Método no registrado")
   
    try:
        data = my_socket.recv(1024)
    except socket.error:
        SOCKET_ERROR = UA['regproxy_ip'] + " PORT:" + UA['regproxy_puerto']
        sys.exit("Error: No server listening at " + SOCKET_ERROR)
        fich = open(UA['log_path'], 'a')
        Time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
        fich.write(Time + "Error: No server listening at " + SOCKET_ERROR)
        
    print 'Recibido\r\n', data
    DATA = data.replace("\r\n", " ") + '\n'
    fich = open(UA['log_path'], 'a')
    Time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
    fich.write(Time + ' Received from ' + TO + DATA)
    fich.close()
    
    if data == "SIP/2.0 404 User Not Found\r\n\r\n":
        sys.exit(" ")
    else:
        if METHOD == "INVITE":
            #He recibido los tres mensajes a la vez, en una misma línea
            METHOD = 'ACK'
            print "Enviando: " + METHOD + " sip:" + OPTION + " SIP/2.0\r\n\r\n"
            my_socket.send(METHOD + " sip:" + OPTION + " SIP/2.0\r\n\r\n")
            receptor_Ip = data.split("o=")[1].split(" ")[1].split("s")[0]
            receptor_Puerto = data.split("m=")[1].split(" ")[1]
            os.system("chmod 777 mp32rtp")
            aEjecutar = './mp32rtp -i ' + receptor_Ip + ' -p '
            aEjecutar += receptor_Puerto + " < " + UA['audio_path']
            print "Vamos a ejecutar", aEjecutar
            os.system(aEjecutar)
            print("Ha terminado la ejecución de fich de audio")
            fich = open(UA['log_path'], 'a')
            Time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
            fich.write(Time + METHOD + " sip:" + OPTION + " SIP/2.0\n")
            fich.close()
        
        elif METHOD == 'BYE':
            fich = open(UA['log_path'], 'a')
            Time = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
            fich.write(Time + ' Finishing...')               
            fich.close()
# Cerramos todo
my_socket.close()
