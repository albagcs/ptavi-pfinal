#!/usr/bin/python
# -*- coding: iso-8859-15 -*-

from xml.sax import make_parser
from xml.sax.handler import ContentHandler
from uaserver import XMLHandler
import sys

try:
    CONFIG = sys.argv[1]
    METHOD = sys.argv[2].upper()
    OPTION = sys.argv[3]
except IndexError:
    sys.exit("Usage: python uaclient.py config method option")

if __name__ == "__main__":
    """
    Programa principal
    """
    parser = make_parser()
    cHandler = XMLHandler()
    parser.setContentHandler(cHandler)
    parser.parse(open(CONFIG))
    UA = cHandler.get_tags()
    print UA['account_username']
