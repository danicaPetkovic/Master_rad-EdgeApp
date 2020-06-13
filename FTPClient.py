import os
from ftplib import FTP_TLS, FTP

import cv2
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

FTP_PORT = 5000
FTP_USER = "call_server"
FTP_PASSWORD = "serverMashine12!"


def send_data_to_server(image_list):
    connection_status = True
    try:
        ftp = FTP()
        ftp.connect('172.20.10.2', FTP_PORT)
        ftp.login(FTP_USER, FTP_PASSWORD)
        print(ftp.getwelcome())

        image_file = 48624896
        for image in image_list:
            image_name = "48624896.jpg"
            cv2.imwrite(image_name, image)
            with open(image_name, 'rb') as image_file:
                ftp.storbinary('STOR ' + str(abs(hash(image_file))) + ".jpg", image_file)
            os.remove(image_name)
    except:
        connection_status = False

    return connection_status
