import _thread
import os
import shutil
import time

import Amazon
import FTPClient
import FaceNet
import FaceRecognition
from pyftpdlib.authorizers import DummyAuthorizer
from pyftpdlib.handlers import FTPHandler
from pyftpdlib.servers import FTPServer

import Microsoft

FTP_PORT = 2121  # Port koji FTP server slusa, Mora da bude veci od 1023, osim ako se skripta run-uje kao root
FTP_USER = "reolinkE1"  # FTP user za log in
FTP_PASSWORD = "reolink.123!"  # FTP user password.

FTP_DIRECTORY = os.getcwd() + "\\reolink_files\\"  # Fajl gde ce FTP user da imam read/write pristup


def main():
    authorizer = DummyAuthorizer()

    # Definise se user sa full r/w permissions.
    # authorizer.add_user(FTP_USER, FTP_PASSWORD, FTP_DIRECTORY, perm='elradfmw')
    authorizer.add_user('Kamera', '123', FTP_DIRECTORY, perm='elradfmw')
    handler = FTPHandler
    handler.authorizer = authorizer

    # Define a customized banner (string returned when client connects)
    handler.banner = "Reolink cliend connected."

    # Optionally specify range of ports to use for passive connections.
    # handler.passive_ports = range(60000, 65535)

    address = ('172.20.10.2', FTP_PORT)
    server = FTPServer(address, handler)

    server.max_cons = 256
    server.max_cons_per_ip = 5

    # server.serve_forever()
    _thread.start_new_thread(server.serve_forever, tuple())

    # file watcher
    beforeFiles = dict([(f, None) for f in os.listdir(FTP_DIRECTORY)])
    while True:
        time.sleep(5)
        afterFiles = dict([(f, None) for f in os.listdir(FTP_DIRECTORY)])
        addedFiles = [f for f in afterFiles if not f in beforeFiles]
        removedFiles = [f for f in beforeFiles if not f in afterFiles]
        if addedFiles: print("Added: ", ", ".join(addedFiles))
        if removedFiles: print("Removed: ", ", ".join(removedFiles))
        beforeFiles = afterFiles

        if addedFiles:
            for file in addedFiles:
                filename, file_extension = os.path.splitext(file)
                print('File extension ', file_extension)
                if file_extension in ['.mp4', '.avi']:
                    # valid, knownPersons, unknownPersons = FaceRecognition.process_video(FTP_DIRECTORY + '\\' + file)
                    # FaceNet.set_models()
                    # valid, knownPersons, unknownPersons = FaceNet.process_video(FTP_DIRECTORY + '\\' + file)
                    valid, knownPersons, unknownPersons = FaceRecognition.process_video(FTP_DIRECTORY + '\\' + file)
                    # valid, knownPersons, unknownPersons = Amazon.process_video(FTP_DIRECTORY + '\\' + file)
                    # valid, knownPersons, unknownPersons = Microsoft.process_video(FTP_DIRECTORY + '\\' + file)
                    print("Result is " + str(valid))
                    print("Known persons: " + str(knownPersons))
                    print("Unknown persons: " + str(unknownPersons))
                    if not valid:
                        data_sent = FTPClient.send_data_to_server(unknownPersons)
                        print(data_sent)
                else:
                    if os.path.isfile(FTP_DIRECTORY + file):
                        os.remove(os.getcwd() + "\\" + file)
                    shutil.move(FTP_DIRECTORY + file, os.getcwd() + "\\")


if __name__ == '__main__':
    print("FTP server started..")
    main()
    print("FTP server closed..")
