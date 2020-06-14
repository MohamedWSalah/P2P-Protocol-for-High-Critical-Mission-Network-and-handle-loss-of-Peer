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
import time


#               0               1                              2          3       4           5            
#Protocol : returnOrNot? ~ if return -> ip else -> data ~ numberOfData ~ size ~ toDelete ~ fileName 

numberOfClient = 2
protocolTag = '~'
returnIps = {}
downloadedFiles = {}
uploadedFiles = {}
hostsHaveFile = []
i=0

Battery = 100
processing = float("{:.2f}".format(random.uniform(5,60)))
bandwidth = random.randint(100,1024)

oldTime = 0

def updateBattery():
	global oldTime
	global Battery
	
	if((time.time() - oldTime) > 30):
		oldTime = time.time()
		Battery = Battery-1
	
def showDeviceInfo():
	global Battery,processing,bandwidth
	print "Battery:",Battery,"%"
	print "processing:", processing
	print "bandwidth:",bandwidth," Kb/s"

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
	print("The node that will help shouldnt have LESS than the following")
	fileName = raw_input("Needed File name: ")

	RequiredPower = raw_input("Required Power :")
	RequiredProcessing = raw_input("Required Processing :")
	RequiredBandwidth = raw_input("Required Bandwidth :")

	#if(not fileName in uploadedFiles):
		#print ("You can not downoad this file. Access denied.")
		#return
	ourIp = commands.getoutput('/sbin/ifconfig').split('\n')[10][13:21]
	src = ourIp
	
	for i in range(numberOfClient):
		msg = 'help~'+ ourIp +'~0~0~0~' + fileName + '~' + RequiredPower + '~' + RequiredProcessing + '~' + RequiredBandwidth
		dst="10.0.0.%s"%(i+1)
		if(dst == ourIp):
			continue
		p.set_new_config(src, dst, msg)
		p.do_send()
		print("sending help request to ip :" , dst)
		while(True):
			packet_size , src_ip, dest_ip, ip_header, icmp_header , payLoad = p.do_receive()

			if(payLoad == 0):
				continue
			payloadData = payLoad.split('~')
			if(payloadData[0] != "help"):
				break
		
		if(payloadData[0] == "Available"):
			hostsHaveFile.append(src_ip)
			print("#### Host",src_ip,"was added")
			
	print("************************")
	if (len(hostsHaveFile) == 0):
		print("THERE IS NO NODE THAT MEET THE REQUIRED CONSTRAINTS")
		print("NO HOSTS TO RECEIVE HELP FROM")
		return
	print("hosts that can help",hostsHaveFile)
	msgreturn = 'return~'+ ourIp +'~0~0~0~' + fileName
	choiceIP = raw_input("Host IP to Receive help from: ")
	while(choiceIP not in hostsHaveFile):
		print("Host IP is Invalid")
		choiceIP = raw_input("Host IP to Receive help from: ")
	hostsHaveFile = []
	p.set_new_config(src, choiceIP, msgreturn)
	p.do_send()
	print("sending help request to ip :" , dst)
	
	
	downloadedFiles[fileName] = {}
#               0               1                              2          3       4           5            
#Protocol : returnOrNot? ~ if return -> ip else -> data ~ numberOfData ~ size ~ toDelete ~ fileName ~ battery ~ processing ~ bandwidth

def receiverFunction(p):
	global i
	global returnIps
	global hostsHaveFile
	global Battery,processing,bandwidth
	
	packet_size , src_ip, dest_ip, ip_header, icmp_header , payLoad = p.do_receive()
	ourIp = commands.getoutput('/sbin/ifconfig').split('\n')[10][13:21]
	if not packet_size == 0:
		payloadData = payLoad.split('~')
		
		 #If it was a downloaded data
		if(icmp_header['type'] == ping.ICMP_ECHO and (not payloadData[0] == 'return') and (not payloadData[0] == 'Available') and (not payloadData[0] == 'help')):
			#print("payload",payLoad)
			if(i==0):
				print("help found on host with ip address",src_ip)
				
				print("======Mohamed159588======")
				print("Starting to receive help ...")

				i=i+1
			fileName = payloadData[5]
			chunkNumber = int(payloadData[2])
			
			print ("***********Downloading data number %d for file %s"%(chunkNumber, fileName))
			downloadedFiles[fileName][chunkNumber] = payloadData[1]
			
			size = int(payloadData[3])
			#print("size",size)
			if(len(downloadedFiles[fileName]) == size):
				packData(fileName, size)
			
		if(payloadData[0] == 'help'):
			if(uploadedFiles.__contains__(payloadData[5]) and float(payloadData[6]) <= Battery and float(payloadData[7]) <= processing and float(payloadData[8]) <= bandwidth):

				response = 'Available~'+ ourIp +'~0~0~0~0~' + payloadData[5] + '~' + str(Battery) + '~' + str(processing) + '~' + str(bandwidth)
				print("sending Available state to ", src_ip)
				print("Device Current States are : ")
				showDeviceInfo()
				p.set_new_config(dest_ip, src_ip, response)
				p.do_send()
			else:
				response = 'Unavailable~'+ ourIp +'~0~0~0~0~' + payloadData[5] + '~' + str(Battery) + '~' + str(processing) + '~' + str(bandwidth)
				print("sending Unavailable state to ", src_ip)
				print("Device Current States are : ")
				showDeviceInfo()
				p.set_new_config(dest_ip, src_ip, response)
				p.do_send()

		#If msg was return to home
		if(payloadData[0] == 'return'):
			returnIps[payloadData[5]] = payloadData[1]
			print "***seding help request to",src_ip
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
	showDeviceInfo()
	p = Ping('0.0.0.0', '0.0.0.0')
	currentSocket = p.get_socket()
	buffer = []
	print(uploadedFiles)
	while(True):
		
		updateBattery()
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
				elif buffer[i] == "help":
					downloadFunction(p)
				elif buffer[i] == "showInfo":
					showDeviceInfo()
				elif buffer[i] == "showUfiles":
					showUploadedFiles()
				elif buffer[i] == "showDfiles":
					showDownloadedFiles()
				else :
					print ("Commmand not found! try again.")
			buffer = []
	
if __name__ == "__main__":
    main()
