# Python 3.7.3
import json
from socket import *
import sys
import pickle
import time

def errorMessage(command):
    print(f"Incorrect syntax for {command[0]}")

serverPort = int(sys.argv[1])

clientSocket = socket(AF_INET, SOCK_DGRAM)



loggedIn = False
status = "logged out"
while 1:
    ##### Start authentication #####
    status = "logged out"
    
    username = input('Enter username:')
    message = json.dumps({
                    "command": "Username",
                    "username": username,
                })
    clientSocket.sendto(message.encode(), ('localhost', serverPort))
    serverMessage = clientSocket.recv(2048)
    serverMessage = serverMessage.decode('utf-8')
    # check if user exists
    if serverMessage == 'new user':
        password = input('New user, enter password:')
        # add username and password to credentials
        message = json.dumps({
                "command": "Register",
                "username": username,
                "password": password
            })
        clientSocket.sendto(message.encode(), ('localhost', serverPort))
        
        status = "logged in"
    elif serverMessage == 'Already logged in':
        status = "already logged in"
        print(f'{username} has already logged in')

    while status == "logged out":
        
        password = input('Enter password:')
        # check if username and password is correct
        message = json.dumps({
                "command": "Login attempt",
                "username": username,
                "password": password
            })
        clientSocket.sendto(message.encode(), ('localhost', serverPort))
        serverMessage = clientSocket.recv(2048)
        serverMessage = serverMessage.decode('utf-8')
        # check what the server replies with and print appropiate message
        if serverMessage == 'success':
            print('Welcome to the forum ')
            status = "logged in"

        elif serverMessage == 'Incorrect password':
            print('Incorrect password')
    

    ##### End authentication #####
    while status == "logged in":
        commands = ["CRT", "MSG", "DLT", "EDT", "LST", "RDT", "UPD", "DWN", "RMV", "XIT" ]
        command = input("Enter one of the following commands: CRT, MSG, DLT, EDT, LST, RDT, UPD, DWN, RMV, XIT:")
        command = command.split()
        if command[0] in commands:
            # create thread
            if command[0] == 'CRT':
                if len(command) != 2:
                    errorMessage(command)
                else:
                    threadTitle = command[1]
                    message = json.dumps({
                        "command": "CRT",
                        "username": username,
                        "threadTitle": threadTitle
                    })
                    clientSocket.sendto(message.encode(), ('localhost', serverPort))
                    serverMessage = clientSocket.recv(2048)
                    serverMessage = serverMessage.decode('utf-8')
                    if serverMessage == "success":
                        print(f"Thread {threadTitle} created")
                    else:
                        print(f"Thread {threadTitle} already exists")
            # list threads
            elif command[0] == 'LST':
                if len(command) != 1:
                    errorMessage(command)
                else:
                    message = json.dumps({
                        "command": "LST",
                        "username": username,
                    })
                    clientSocket.sendto(message.encode(), ('localhost', serverPort))
                    serverMessage = clientSocket.recv(2048)
                    serverMessage = serverMessage.decode('utf-8')
                    if serverMessage == "fail":
                        print("No threads to list")
                    else:
                        print("The list of active threads:")
                        serverMessage = clientSocket.recv(2048)
                        threadList =  pickle.loads(serverMessage)

                        print(*threadList, sep = "\n")

            # read thread
            elif command[0] == 'RDT':
                if len(command) != 2:
                    errorMessage(command)
                else:
                    threadTitle = command[1]
                    message = json.dumps({
                        "command": "RDT",
                        "username": username,  
                        "threadTitle": threadTitle
                    })
                    clientSocket.sendto(message.encode(), ('localhost', serverPort))
                    serverMessage = clientSocket.recv(2048)
                    serverMessage = serverMessage.decode('utf-8')
                    if serverMessage == "success":
                        serverMessage = clientSocket.recv(2048)
                        file = pickle.loads(serverMessage)
                        if len(file) == 0:
                            print(f"Thread {threadTitle} is empty")
                        else:
                            print(*file, sep = "\n")
                    else:
                        print(f"Thread {threadTitle} does not exist")

            # remove thread
            elif command[0] == 'RMV':
                if len(command) != 2:
                    errorMessage(command)
                else:
                    threadTitle = command[1]
                    message = json.dumps({
                        "command": "RMV",
                        "username": username,
                        "threadTitle": threadTitle
                    })
                    clientSocket.sendto(message.encode(), ('localhost', serverPort))
                    serverMessage = clientSocket.recv(2048)
                    serverMessage = serverMessage.decode('utf-8')
                    if serverMessage == "success":

                        print(f"Thread {threadTitle} removed")
                    elif serverMessage == "Not Owner":
                        print(f"The thread was created by another user and cannot be removed")
                    else:
                        print(f"Thread {threadTitle} does not exists")
            # post message
            elif command[0] == 'MSG':
                if len(command) < 3:
                    errorMessage(command)
                else:
                    threadTitle = command[1]
                    i = 2
                    msg = ''
                    while i < len(command):
                        msg += command[i] + " "
                        i += 1
                    message = json.dumps({
                        "command": "MSG",
                        "username": username,
                        "threadTitle": threadTitle,
                        "message": msg
                    })
                    clientSocket.sendto(message.encode(), ('localhost', serverPort))
                    serverMessage = clientSocket.recv(2048)
                    serverMessage = serverMessage.decode('utf-8')
                    if serverMessage == "success":
                        print(f"Message posted to {threadTitle} thread")
                    else:
                        print(f"{threadTitle} thread does not exists")
                        
            # delete message
            elif command[0] == 'DLT':
                if len(command) != 3:
                    errorMessage(command)
                else:
                    threadTitle = command[1]
                    msgNum = command [2]
                    message = json.dumps({
                        "command": "DLT",
                        "username": username,
                        "threadTitle": threadTitle,
                        "messageNumber": msgNum
                    })
                    clientSocket.sendto(message.encode(), ('localhost', serverPort))
                    serverMessage = clientSocket.recv(2048)
                    serverMessage = serverMessage.decode('utf-8')
                    if serverMessage == "success":
                        print("The message has been deleted")
                    elif serverMessage == "does not own":
                        print("The message belongs to another user and cannot be deleted")
                    elif serverMessage == "does not exist":
                        print(f"Message number {msgNum} does not exist")
                    elif serverMessage == "Thread does not exist":
                        print(f"Thread {threadTitle} does not exist")

            # edit message
            elif command[0] == 'EDT':
                if len(command) < 4:
                    errorMessage(command)
                else:
                    threadTitle = command[1]
                    msgNum = command [2]
                    i = 3
                    msg = ''
                    while i < len(command):
                        msg += command[i] + " "
                        i += 1
                    message = json.dumps({
                        "command": "EDT",
                        "username": username,
                        "threadTitle": threadTitle,
                        "messageNumber": msgNum,
                        "message": msg
                    })
                    clientSocket.sendto(message.encode(), ('localhost', serverPort))
                    serverMessage = clientSocket.recv(2048)
                    serverMessage = serverMessage.decode('utf-8')
                    if serverMessage == "success":
                        print("The message has been edited")
                    elif serverMessage == "does not own":
                        print("The message belongs to another user and cannot be edited")
                    elif serverMessage == "does not exist":
                        print(f"Message number {msgNum} does not exist")
                    elif serverMessage == "Thread does not exist":
                        print(f"Thread {threadTitle} does not exist")
            # upload file
            elif command[0] == 'UPD':
                if len(command) != 3:
                    errorMessage(command)
                else:
                    
                    threadTitle = command[1]
                    fileName = command[2]
                    message = json.dumps({
                        "command": "UPD",
                        "username": username,
                        "threadTitle": threadTitle,
                        "fileName": fileName
                    })
                    clientSocket.sendto(message.encode(), ('localhost', serverPort))
                    serverMessage = clientSocket.recv(2048)
                    serverMessage = serverMessage.decode('utf-8')

                    if serverMessage == "success":
                        tcpClient = socket(AF_INET, SOCK_STREAM)
                        time.sleep(0.1)
                        tcpClient.connect(('localhost', serverPort))

                        file = open(fileName, "rb")
                        fileContent = file.read(2048)
                        while fileContent:
                            tcpClient.send(fileContent)
                            fileContent = file.read(2048)
                        file.close()
                        tcpClient.close()
                                
                        print(f"{fileName} uploaded to {threadTitle} thread")
                    elif serverMessage == "Already exist":
                        print(f"{fileName} already exist in {threadTitle} thread")
                    else:
                        print(f"Thread {threadTitle} does not exist")

            # download file
            elif command[0] == 'DWN':
                if len(command) != 3:
                    errorMessage(command)
                else:
                    threadTitle = command[1]
                    fileName = command[2]
                    message = json.dumps({
                        "command": "DWN",
                        "username": username,
                        "threadTitle": threadTitle,
                        "fileName": fileName
                    })
                    clientSocket.sendto(message.encode(), ('localhost', serverPort))
                    serverMessage = clientSocket.recv(2048)
                    time.sleep(0.1)
                    serverMessage = serverMessage.decode('utf-8')
                    if serverMessage == "success":
                        tcpClient = socket(AF_INET, SOCK_STREAM)
                        tcpClient.connect(('localhost', serverPort))
                        with open(fileName, "wb") as file:
                            data = tcpClient.recv(2048)
                            while data: 
                                file.write(data)
                                data = tcpClient.recv(2048)
                        tcpClient.close()
                        
                        print(f"{fileName} successfully downloaded")
                    elif serverMessage == "Does not exist":
                        print(f"{fileName} does not exist in {threadTitle} thread")
                    else:
                        print(f"Thread {threadTitle} does not exist")
                        
            # exit
            elif command[0] == 'XIT':
                if len(command) != 1:
                    errorMessage(command)
                else:
                    message = json.dumps({
                        "command": "XIT",
                        "username": username
                    })
                    clientSocket.sendto(message.encode(), ('localhost', serverPort))
                    serverMessage = clientSocket.recv(2048)
                    serverMessage = serverMessage.decode('utf-8')
                    if serverMessage == "success":
                        print("Goodbye")
                        status = "logged out"
                        exit()
                    else:
                        continue
            else: 
                print('Invalid command')
        else:
            print("Invalid command")

clientSocket.close()


