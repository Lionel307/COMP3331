# Python 3.7.3
from fileinput import filename
import json
from socket import *
import sys
import os
import pickle
import re
def authenticate(credentials):
    with open('credentials.txt', 'r') as file:
        line = file.readline()
        while line != '':
            check = line.split()
            if credentials[0] == check[0]:
                if credentials[1] != '' and credentials[1] != check[1]:
                    return 'Incorrect password'
                else:
                    return 'success'
            line = file.readline()
        return 'new username'

# return true if thread exist
# false if thread doesn't
def checkThread(threadTitle, threadList):
    if threadTitle in threadList:
        return True
    else:
        return False

def checkOwner(threadTitle, username):
    with open(threadTitle, 'r') as thread:
        if thread.readline().strip() == (f"Owner: {username}"):
            return True
        else:
            return False

def checkMsgOwner(threadTitle, username, msgNum):
    with open(threadTitle, 'r') as thread:
        lines = thread.readline()
        while lines != '':
            line = lines.split()
            if line[0].isdigit and msgNum == line[0]:
                owner = line[1][:-1]
                if owner == username:
                    return "success"
                else:
                    return "does not own"
            lines = thread.readline()
            
        return "does not exist"

def checkFile(threadTitle, fileName):
    with open(threadTitle, 'r') as thread:
        lines = thread.readline()
        while lines != '':
            line = lines.split()
            if "uploaded" in line and line[-1] == fileName:
                return "exists"
            lines = thread.readline()
        return "does not exist"


serverPort = int(sys.argv[1])
serverSocket = socket(AF_INET, SOCK_DGRAM)
serverSocket.bind(('localhost', serverPort))
tcpServer = socket(AF_INET, SOCK_STREAM)
tcpServer.bind(('localhost', serverPort))


threadList = []
activeUsers= []

try:
    while 1:
        if len(activeUsers) == 0:
            print('Waiting for Clients')
        
        clientMessage, clientAddress = serverSocket.recvfrom(2048)
        clientMessage = clientMessage.decode()
        clientMessage = json.loads(clientMessage)
        username = clientMessage["username"]
        command = clientMessage["command"]
        # authenticate first
        if command == "Username":
            # check username with no password
            print('Client authenticating')
            
            if username in activeUsers:
                print(f"{username} has already logged in")
                serverSocket.sendto("Already logged in".encode(), clientAddress)
            else:
                password = ''
                credentials = [username, password]
                authMessage = authenticate(credentials)
                if authMessage == 'new username':
                    serverMessage = 'new user'
                    serverSocket.sendto(serverMessage.encode(), clientAddress)
                    print('New user')
                else:
                    serverMessage = 'existing user'
                    serverSocket.sendto(serverMessage.encode(), clientAddress)
                
        # register new user
        if command == "Register":
            print(f"{username} successfully registered")
            password = clientMessage["password"]
            credentials = '\n' + username + ' ' + password
            openFile = open("credentials.txt", "a")
            openFile.write(credentials)
            openFile.close()
            activeUsers.append(username)

        elif command == "Login attempt":
            password = clientMessage["password"]
            credentials = [username, password]
            authMessage = authenticate(credentials)
            if authMessage == 'success':
                print(f"{username} has logged in")
                activeUsers.append(username)
                serverSocket.sendto(authMessage.encode(), clientAddress)

            else:
                print("Incorrect password")
                serverSocket.sendto(authMessage.encode(), clientAddress)

        # Create thread
        if command == "CRT":
            threadTitle = clientMessage["threadTitle"]
            print(f"{username} issued CRT command")
            if not checkThread(threadTitle, threadList):
                with open(threadTitle, 'w') as thread:
                    thread.write(f"Owner: {username}")
                threadList.append(threadTitle)
                print(f"Thread {threadTitle} created")
                serverSocket.sendto("success".encode(), clientAddress)
            else:
                print(f"Thread {threadTitle} already exists")
                serverSocket.sendto("fail".encode(), clientAddress)
            
        # List thread
        elif command == 'LST':
            print(f"{username} issued LST command")
            # no threads in list
            if not len(threadList):
                serverSocket.sendto("fail".encode(), clientAddress)
            else:
                # used pickle to send list
                serverSocket.sendto("success".encode(), clientAddress)
                message = pickle.dumps(threadList)
                serverSocket.sendto(message, clientAddress)

        # Remove thread
        elif command == "RMV":
            print(f"{username} issued RMV command")
            threadTitle = clientMessage["threadTitle"]

            if checkThread(threadTitle, threadList):
                if checkOwner(threadTitle, username):
                    print(f"Thread {threadTitle} removed")
                    serverSocket.sendto("success".encode(), clientAddress)
                    # remove thread from directory
                    os.remove(threadTitle)
                    # remove thread from list
                    threadList.remove(threadTitle)
                    # remove files from directory
                    # TODO
                else:
                    serverSocket.sendto("Not Owner".encode(), clientAddress)
                    print(f"Thread {threadTitle} cannot be removed")
            else:
                serverSocket.sendto("fail".encode(), clientAddress)

        # Read thread
        elif command == "RDT":
            print(f"{username} issued RDT command")
            threadTitle = clientMessage["threadTitle"]
            if checkThread(threadTitle, threadList):
                serverSocket.sendto("success".encode(), clientAddress)
                file = []
                with open(threadTitle, 'r') as thread:
                    next(thread)
                    for line in thread:
                        file.append(line.strip())
                message = pickle.dumps(file)
                serverSocket.sendto(message, clientAddress)
                print(f"Thread {threadTitle} read")
            else:
                serverSocket.sendto("fail".encode(), clientAddress)
                print("Incorrect thread specified")


        # Post message
        elif command == "MSG":
            print(f"{username} issued MSG command")
            threadTitle = clientMessage["threadTitle"]
            msg = clientMessage["message"]

            if checkThread(threadTitle, threadList):
                count = 1
                # count num messages
                with open(threadTitle, 'r') as thread:
                    thread = thread.read()
                    lines = thread.split("\n")
                    for line in lines:
                        if re.match("^[0-9]", line):
                            count += 1
                with open(threadTitle, 'a+') as thread:
                    finalMsg = "\n" + str(count) + " " + username + ": " + msg
                    thread.write(finalMsg)
                serverSocket.sendto("success".encode(), clientAddress)

                print(f"Message posted to {threadTitle} thread")
            else:
                serverSocket.sendto("fail".encode(), clientAddress)

        # Delete message
        elif command == "DLT":
            print(f"{username} issued DLT command")
            threadTitle = clientMessage["threadTitle"]
            msgNum = clientMessage["messageNumber"]

            if checkThread(threadTitle, threadList):
                check = checkMsgOwner(threadTitle, username, msgNum)
                serverSocket.sendto(check.encode(), clientAddress)

                if check == "success":
                    print("Message has been deleted")
                    with open(threadTitle, "r") as thread:
                        lines = thread.readlines()
                    with open(threadTitle, "w") as thread:
                        for line in lines:
                            num = line.split(" ", 1)
                            if num[0] != msgNum:
                                # update all messages after deleted one
                                if num[0].isdigit() and num[0] > msgNum:
                                    newNum = int(num[0]) - 1
                                    line = str(newNum) + " " + num[1]
                                thread.write(line)
                elif check == "does not own":
                    print("Message cannot be deleted")
                else:
                    print("Message number does not exist")
            else:
                print("Thread does not exist")
                serverSocket.sendto("Thread does not exist".encode(), clientAddress)

        # Edit message
        elif command == "EDT":
            print(f"{username} issued EDT command")
            threadTitle = clientMessage["threadTitle"]
            msgNum = clientMessage["messageNumber"]
            msg = clientMessage["message"]
            
            if checkThread(threadTitle, threadList):
                check = checkMsgOwner(threadTitle, username, msgNum)
                serverSocket.sendto(check.encode(), clientAddress)
                if check == "success":
                    print("Message has been edited")
                    with open(threadTitle, "r") as thread:
                        lines = thread.readlines()
                    with open(threadTitle, "w") as thread:
                        for line in lines:
                            num = line.split(" ", 1)
                            if num[0] == msgNum:
                                line = msgNum + " " + username + ": " + msg
                            thread.write(line)
                elif check == "does not own":
                        print("Message cannot be edited")
                else:
                        print("Message number does not exist")
            else:
                print("Thread does not exist")
                serverSocket.sendto("Thread does not exist".encode(), clientAddress)   

        # Upload file
        elif command == "UPD" or command == "DWN":
            username = clientMessage["username"]
            threadTitle = clientMessage["threadTitle"]
            fileName = clientMessage["fileName"]

            if checkThread(threadTitle, threadList):
                # Upload file
                if command == "UPD":
                    print(f"{username} issued UPD command")
                    if checkFile(threadTitle, fileName) == "exists":
                        serverSocket.sendto("Already exist".encode(), clientAddress)
                        print(f"file {fileName} already exists in {threadTitle} thread")
                    else:
                        serverSocket.sendto("success".encode(), clientAddress)
                        with open(threadTitle, 'a+') as thread:
                            thread.write("\n" + f"{username} uploaded {fileName}")

                        tcpServer.listen(1)
                        print(f"{username} uploaded file {fileName} to {threadTitle} thread")

                        with open(f"{threadTitle}-{fileName}", "wb") as file:
                            connectionSocket, tcpAddress = tcpServer.accept()
                            data = connectionSocket.recv(2048)
                            while data:
                                file.write(data)
                                data = connectionSocket.recv(2048)
                            connectionSocket.close()
                # Download file
                else:
                    print(f"{username} issued DWN command")
                    if checkFile(threadTitle, fileName) == "exists":
                        serverSocket.sendto("success".encode(), clientAddress)
                        tcpServer.listen(1)

                        file = open(f"{threadTitle}-{fileName}", "rb")
                        connectionSocket, tcpAddress = tcpServer.accept()

                        fileContent = file.read(2048)
                        while fileContent:
                            connectionSocket.send(fileContent)

                            fileContent = file.read(2048)
                        file.close()
                        connectionSocket.close()
                        
                        print(f"{fileName} downloaded from thread {threadTitle}")
                    else:
                        serverSocket.sendto("Does not exist".encode(), clientAddress)
                        print(f"{fileName} does not exist in thread {threadTitle}")

            else:
                print(f"Thread {threadTitle} does not exist")
                serverSocket.sendto("fail".encode(), clientAddress)

        # Exit command
        elif command == "XIT":
            print(f"{username} exited")
            activeUsers.remove(username)
            serverSocket.sendto("success".encode(), clientAddress)   
            
except KeyboardInterrupt:
    print("Closing server")
    serverSocket.close()
    tcpServer.close()



