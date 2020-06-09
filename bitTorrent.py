import ping
from ping import Ping
from random import randint
import random
import commands
import time 
import socket
import sys
import threading 
import socket
import select
import pyping



#               0               1                              2          3       4           5            
#Protocol : returnOrNot? ~ if return -> ip else -> data ~ numberOfData ~ size ~ toDelete ~ fileName 

numberOfClient = 5
protocolTag = '~'
returnIps = {}
downloadedFiles = {}
uploadedFiles = {}
hostsHaveFile = []
i=0

def splitFile(fileName):
	global uploadedFiles
	#print("Uploaded files : ",uploadedFiles)
	uploadedFiles[fileName] = True
	#print("FileName",fileName)
	result = []
	try:
		f = open(fileName, "rb")
		byte = f.read(1)
		result.append(byte)
		while byte != "":
			byte = f.read(1)
			result.append(byte)
		print ("File uploaded succesfully.")
		f.close()
	except :
		print ("Can not upload.")
	result = result[:-1]
	return result

def send():
	sourceIp = findRandomIp()
	destinationIp = findRandomIp()
	while destinationIp == sourceIp:
		 destinationIp = findRandomIp()
	print ("from %s to %s" % (sourceIp, destinationIp))
	Server= Ping(sourceIp , destinationIp)
	Server.do_send()

def findRandomIp():   
	hostname = socket.gethostname()     
	ip = commands.getoutput('/sbin/ifconfig').split('\n')[1][20:28]
	ipFounded = False
	newIpToJoin = ""
	while not ipFounded :
		newIpToJoin = randint(1, numberOfClient)
		newIpToJoin = "10.0.0." + str(newIpToJoin)
		if not newIpToJoin == ip:
			ipFounded = True
	return newIpToJoin

def getRandomSourceAndDestination():
        sourceIp = findRandomIp()
        destinationIp = findRandomIp()
        while destinationIp == sourceIp :
                destinationIp = findRandomIp()
        return sourceIp, destinationIp

def senderFunction(p):
	fileName = raw_input("File name: ")

	fileData = splitFile(fileName)
	"""
	#send file
	i = 0
	length = 0
	if len(fileData) % 8 == 0 :
		length = len(fileData) / 8
	else:
		length = (len(fileData) / 8) + 1 
	while i < len(fileData):
		data = ''
		for j in range(i , i + 8):
			if j < len(fileData):
				data += fileData[j]
		payload = '0' + protocolTag + data + protocolTag + '%s'%(i/8) + protocolTag + str(length) + protocolTag  + '0' + protocolTag + fileName
		src, dst = getRandomSourceAndDestination()
		print("source: ",src,"  Dest:", dst)
		p.set_new_config( src,dst, payload)
		p.do_send()
		i = i + 8
	"""

def downloadFunction(p):
	global downloadedFiles
	global uploadedFiles
	global hostsHaveFile
	showUploadedFiles()
	showDownloadedFiles()
	fileName = raw_input("File name: ")
	#if(not fileName in uploadedFiles):
		#print ("You can not downoad this file. Access denied.")
		#return
	ourIp = commands.getoutput('/sbin/ifconfig').split('\n')[1][13:21]
	src = ourIp

	
	for i in range(numberOfClient):
		msg = 'request~'+ ourIp +'~0~0~0~' + fileName
		dst="10.0.0.%s"%(i+1)
		if(dst == ourIp):
			continue
		p.set_new_config(src, dst, msg)
		p.do_send()
		print("sending file request to ip :" , dst)
		while(True):
			packet_size , src_ip, dest_ip, ip_header, icmp_header , payLoad = p.do_receive()
			if(payLoad == 0):
				continue
			payloadData = payLoad.split('~')
			if(payloadData[0] != "request"):
				break
		
		if(payloadData[0] == "Available"):
			hostsHaveFile.append(src_ip)
			print("#### Host",src_ip,"was added")
			
	print("************************")	
	print("hosts have the file",hostsHaveFile)
	msgreturn = 'return~'+ ourIp +'~0~0~0~' + fileName
	choiceIP = raw_input("Host IP to Receive file from: ")
	while(choiceIP not in hostsHaveFile):
		print("Host IP is Invalid")
		choiceIP = raw_input("Host IP to Receive file from: ")
	hostsHaveFile = []
	p.set_new_config(src, choiceIP, msgreturn)
	p.do_send()
	print("sending file request to ip :" , dst)
		
		
		
	print("ourIP:",ourIp)
	print("msg:",msg)
	#print("fileName : " ,fileName)
	#print("msg : " ,msg)
	#src, dst = getRandomSourceAndDestination()
	
	
	downloadedFiles[fileName] = {}
#               0               1                              2          3       4           5            
#Protocol : returnOrNot? ~ if return -> ip else -> data ~ numberOfData ~ size ~ toDelete ~ fileName 

def receiverFunction(p):
	global i
	global returnIps
	global hostsHaveFile
	#print ("RETURN IPS", returnIps)
	packet_size , src_ip, dest_ip, ip_header, icmp_header , payLoad = p.do_receive()
	ourIp = commands.getoutput('/sbin/ifconfig').split('\n')[1][13:21]
	if not packet_size == 0:
		payloadData = payLoad.split('~')
		 #If it was a downloaded data
		if(icmp_header['type'] == ping.ICMP_ECHO and (not payloadData[0] == 'return') and (not payloadData[0] == 'Available') and (not payloadData[0] == 'request')):
			#print("payload",payLoad)
			if(i==0):
				print("File found on host with ip address",src_ip)
				
				print("======Mohamed159588======")
				print("Starting to download ",payloadData[5])

				i=i+1
			fileName = payloadData[5]
			chunkNumber = int(payloadData[2])
			
			print ("***********Downloading data number %d for file %s"%(chunkNumber, fileName))
			downloadedFiles[fileName][chunkNumber] = payloadData[1]
			
			size = int(payloadData[3])
			#print("size",size)
			if(len(downloadedFiles[fileName]) == size):
				print("inside If..")
				packData(fileName, size)
			
		if(payloadData[0] == 'request'):
			if(uploadedFiles.__contains__(payloadData[5])):
				response = 'Available~'+ ourIp +'~0~0~0~0~' + payloadData[5]
				print("inside request")
				print("response", response)
				print("src ",src_ip,"  Dest", dest_ip)
				p.set_new_config(dest_ip, src_ip, response)
				p.do_send()
			else:
				response = 'Unavailable~'+ ourIp +'~0~0~0~0~' + payloadData[5]
				print("inside unavailable")
				print("response", response)
				print("src ",src_ip,"  Dest", dest_ip)
				p.set_new_config(dest_ip, src_ip, response)
				p.do_send()

		#If msg was return to home
		if(payloadData[0] == 'return'):
			returnIps[payloadData[5]] = payloadData[1]
			if(uploadedFiles.__contains__(payloadData[5])):
				fileName = payloadData[5]
				chunkNumber = int(payloadData[2])
				print ("***********sending to %s data number %d for file %s"%(src_ip,chunkNumber, fileName))
				downloadedFiles[fileName] = payloadData[1]
				size = int(payloadData[3])
				if(len(downloadedFiles[fileName]) == size):
					packData(fileName, size)

				fileData = splitFile(fileName)
				i = 0
				length = 0
				if len(fileData) % 8 == 0 :
					length = len(fileData) / 8
				else:
					length = (len(fileData) / 8) + 1 
				while i < len(fileData):
					data = ''
					for j in range(i , i + 8):
						if j < len(fileData):
							data += fileData[j]
					payload = '0' + protocolTag + data + protocolTag + '%s'%(i/8) + protocolTag + str(length) + protocolTag  + '0' + protocolTag + fileName
					p.set_new_config(dest_ip, src_ip, payload)
					p.do_send()
					print("sending payload ", payload)
					i = i + 8
	
			elif(src_ip != ourIp and icmp_header['type'] == ping.ICMP_ECHOREPLY):
				return
			else:
				print("File not available for", src_ip,". file name is ", payloadData[5])
			

'''
		#If msg was return to home	
		if(icmp_header['type'] == ping.ICMP_ECHOREPLY):
			# print "PayLoad is %s"%(payLoad)
			#If Bezzy get the chunk
			if(payloadData[4] == '1'):
				print ("***********Deleting file number %s from network"%(payloadData[2]))
			#If we should send this chunk to Home 
			elif((not payloadData[0] == 'return') and payloadData[5] in returnIps):
					payloadData[4] = '1'
					payLoad = '~'.join(payloadData)
					print ("***********Sending to Home %s"%(returnIps[payloadData[5]]))
					ourIp = commands.getoutput('/sbin/ifconfig').split('\n')[1][20:28]
					p.set_new_config(ourIp, returnIps[payloadData[5]], payLoad)
					p.do_send()
			#If we should spin the chunk

			#else : 
				
				#p.set_new_config(dest_ip, src_ip, payLoad)
				#p.do_send()
'''
def packData(fileName, size):
	print ("**********Packing %s "%(fileName))
	f = open('./downloaded_' + fileName, 'wb+')
	for i in range(0, size):
		f.write(downloadedFiles[fileName][i])
	f.close()
	
def showFile():
	fileName = raw_input("File name: ")
	result = ""
	try:
		f = open(fileName, 'rb')
		byte = f.read(1)
		result += str(byte)
		while byte != "":
			byte = f.read(1)
			result += str(byte)
		print (result)
		f.close()
	except :
		print ("Can not open file.")
	result = result[:-1]

#Mohamed159588#	
def showUploadedFiles():
	print("The uploaded Files are > ",uploadedFiles)

def showDownloadedFiles():
	print("The Downloaded Files are>",downloadedFiles)

def main():
	p = Ping('0.0.0.0', '0.0.0.0')
	currentSocket = p.get_socket()
	buffer = []
	print(uploadedFiles)
	while(True):
		inputs, output, exception = select.select([currentSocket, sys.stdin] , [currentSocket], [])
		for i in inputs:
			if i == currentSocket :
				receiverFunction(p)
			elif i == sys.stdin :
				x = raw_input()
				buffer.append(x)
		if currentSocket in output :
			for i in range(len(buffer)):
				if buffer[i] == "upload":
					senderFunction(p)
				elif buffer[i] == "download":
					downloadFunction(p)
				elif buffer[i] == "vim":
					
					pingAllFull()
				elif buffer[i] == "showUfiles":
					showUploadedFiles()
				elif buffer[i] == "showDfiles":
					showDownloadedFiles()
				else :
					print ("Commmand not found! try again.")
			buffer = []
	
if __name__ == "__main__":
    main()
