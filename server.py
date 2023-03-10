from socket import *
import argparse
import sys
import os
import datetime
from datetime import timezone
import csv

#wget http://192.168.56.1:12000/HelloWorld.html
#HTTP/1.1 200 OK\r\nContent-Length: 21\r\n\r\nHello World, I am foo

def HTTPdate():
    dt = datetime.datetime.now(datetime.timezone.utc)
    weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()]
    month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
            "Oct", "Nov", "Dec"][dt.month - 1]
    return "%s, %02d %s %04d %02d:%02d:%02d GMT" % (weekday, dt.day, month, dt.year, dt.hour, dt.minute, dt.second)

class myMSG:
    def __init__(self, fileName):
        self.fileName = fileName
        #self.fp = fp = open(fileName, "r")
        self.contentLength = os.stat(fileName).st_size
        self.contentType = self.type()
        self.Date = self.HTTPdate()
        self.lastModified = self.lastmDate()
    
    def HTTPdate(self):
        dt = datetime.datetime.now(datetime.timezone.utc)
        weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()]
        month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
                "Oct", "Nov", "Dec"][dt.month - 1]
        return "%s, %02d %s %04d %02d:%02d:%02d GMT" % (weekday, dt.day, month, dt.year, dt.hour, dt.minute, dt.second)
    
    def lastmDate(self):
        timestamp = os.path.getmtime(self.fileName)
        dt = datetime.datetime.fromtimestamp(timestamp, tz=timezone.utc)
        weekday = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][dt.weekday()]
        month = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep",
                "Oct", "Nov", "Dec"][dt.month - 1]
        return "%s, %02d %s %04d %02d:%02d:%02d GMT" % (weekday, dt.day, month, dt.year, dt.hour, dt.minute, dt.second)
    
    def HTTPheader(self):
        messages = ['200 OK', '404 FILE NOT FOUND', '501 NOT IMPLEMENTED', '505 HTTP VERSION NOT SUPPORTED']
        string = 'HTTP/1.1 '
        string = string + messages[0] + "\r\n"
        string = string + "Content-Length: " + str(self.contentLength) + "\r\n"
        string = string + "Content-Type:" + self.contentType + "\r\n"
        string = string + "Date: " + self.Date + "\r\n"
        string = string + "Last-Modified: " + self.lastModified + "\r\n"
        string = string + "\r\n"
        
        return string
    
    def type(self):
        expected_ft = [['.csv', 'text/csv'], ['.png', 'image/png'], ['.jpg', 'image/jpg'], ['.gif', 'image/gif'],
        ['.zip', 'application/zip'], ['.txt', 'text/txt'], ['.html', 'text/html'], ['.doc', 'application/msword'],
        ['.docx', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document' ]]
        name, ex = os.path.splitext(self.fileName)
        check = 0
        for pair in expected_ft:
            if ex == pair[0]:
                check = 1
                return pair[1]
        if check == 0:
            print("Invalid File Type") #################################
            serverError("Bad Extention")
    
    def dum(self):
        return self.contentLength


def serverError(error):
    print("Error with: " + error, file=sys.stderr)
    exit(1)

def checkArg(args=None):
    parser = argparse.ArgumentParser(description="Parse Input")
    parser.add_argument('-p', '--port', required=True, help="The port of the server.")
    parser.add_argument('-d', '--directory', required=True, help="Specify alternative directory")

    results = parser.parse_args(args)

    if (results.port.isdigit()):
        results.port = int(results.port)
    else:
        serverError("Bad Port")

    dir = os.path.abspath(results.directory)
    
    if (results.port < 1 or results.port > 65535):
        serverError("Bad Port")
    if (results.port < 1024):
        print("WARNING!!! Well Known Port")
    if (os.path.exists(dir) == False):
        serverError("Bad Directory")

    return (results.port, dir)

def buildSocket(server, port):
    serverSocket1 = socket(AF_INET,SOCK_STREAM)
    serverSocket1.setsockopt(SOL_SOCKET, SO_REUSEADDR, 1)
    serverSocket1.bind((server,port))
    serverSocket1.listen(1)
    return serverSocket1

def httpParse(msg):
    headers = msg.split("\r\n")
    headerDict = {}
    request = headers.pop(0)
    request = request.split(" ")
    return request + headers

def writeCSV(server, port, peerIP, peerPort, url, status, contentLen):
    csvfile = open("sgantneySocketOutput.csv", "a", newline="\n")
    writer = csv.writer(csvfile)
    string = ["Client request served", "4-tuple:", server, port, peerIP, peerPort, "Requested URL", url, status, "Bytes transmitted:", contentLen]
    writer.writerow(string)
    #print("writ")
    csvfile.close()

def writeTXT(headerstring):
    txtfile = open("sgantneySocketOutput.txt", "a", newline = "\n")
    txtfile.write(headerstring)
    txtfile.close()

def getResponse(connectionSocket, directory, parsedMSG, server, port, peerIP, peerPort):
    if (os.path.isfile(directory + parsedMSG[1])):
        fp = open(directory + parsedMSG[1], "rb")
        rd = fp.read()
        rmessage = myMSG(directory + parsedMSG[1])
        headerString = rmessage.HTTPheader()
        newMSG = bytes(headerString, 'utf-8') + rd
        number = connectionSocket.send(newMSG)
        writeCSV("127.0.0.1", port, peerIP, peerPort, directory + parsedMSG[1], "200 OK", rmessage.dum())
        writeTXT(headerString)

        fp.close()
    else:
        #print(directory + parsedMSG[1])
        string = "HTTP/1.1 404 Not Found\r\nContent-Length: 10\r\nDate: " + HTTPdate() + "\r\n\r\nNot Found\n"
        newMSG = bytes(string, 'utf-8')
        number = connectionSocket.send(newMSG)
    return number


if __name__ == "__main__":
    port, directory = checkArg(args=None)
    print("<Port>: %d <Directory> %s" % (port, directory))
    os.chdir(directory)
    buffer = 1024
    server = "127.0.0.1"
    serverSocket = buildSocket(server, port)
    #print(serverSocket.getsockname())
    print(f"Welcome socket created: {server}, {port}")

    while True:
        connectionSocket, addr = serverSocket.accept()
        peerIP, peerPort = connectionSocket.getpeername()
        msg = connectionSocket.recv(buffer).decode()
        print(f"Connection requested from {peerIP}, {peerPort}")
        if msg == None:
            serverError("Bad Connection")
            
        parsedMSG = httpParse(msg)
        if (parsedMSG[0] == 'GET'):
            number = getResponse(connectionSocket, directory, parsedMSG, server, port, peerIP, peerPort)
        else:
            string = "HTTP/1.1 505 Version Not Supported\r\nContent-Length: 22\r\nDate: " + HTTPdate() + "\r\n\r\nVersion Not Supported\n"
            newMSG = bytes(string, 'utf-8')
            number = connectionSocket.send(newMSG)

        print(number)
        connectionSocket.close()
        print(f"Connection to {peerIP}, {peerPort} is closed.")
