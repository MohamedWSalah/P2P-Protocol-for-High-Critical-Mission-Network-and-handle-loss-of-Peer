import ping
from ping import Ping
from random import randint
import random
import commands
import subprocess
import time 
import socket
import sys
import threading 
import socket
import select
import pyping
import time
import signal
import operator
import collections
import multiprocessing

#               0               1                              2          3       4           5            
#Protocol : returnOrNot? ~ if return -> ip else -> data ~ numberOfData ~ size ~ toDelete ~ fileName 

numberOfClient = 6
protocolTag = '~'
returnIps = {}
downloadedFiles = {}
uploadedFiles = {}
hostsHaveFile = []
bestHosts = []
test = ''
i=0
RequiredPower,RequiredProcessing,RequiredBandwidth = 0,0,0
class TimeoutException(Exception):
    pass

def sigalrm_handler(signum, frame):
    # We get signal!
    raise TimeoutException()



Battery = 100
processing = float("{:.2f}".format(random.uniform(5,15)))
bandwidth = random.randint(100,1024)
state = 'transmitting'

oldTime = 0

def updateBattery():
	global oldTime
	global Battery
	
	if((time.time() - oldTime) > 30):
		oldTime = time.time()
		Battery = Battery - 1


def showDeviceInfo():
	global Battery,processing,bandwidth
	print "Battery:",Battery,"%"
	print "processing:", processing
	print "bandwidth:",bandwidth," Kb/s"
	print "State:",state

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
		#print ("File uploaded succesfully.")
		f.close()
	except :
		print ("Can not upload.")
	result = result[:-1]
	return result

def hopsCount():
	global hostsHaveFile
	global bestHosts
	hopsCounter = -1
	chosenIP = ''
	chosenHops = 100
	listIPs = []
	listHops = []
	for IP in hostsHaveFile:
		time.sleep(3)
		print "checking number of hops to ",IP
		traceroute = subprocess.Popen(["traceroute", '-w', '100',IP],stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

		for line in iter(traceroute.stdout.readline,""):
			hopsCounter = hopsCounter+1
		
		if (hopsCounter < chosenHops):
			chosenHops = hopsCounter
			chosenIP = IP
		
		listIPs.append(IP)
		listHops.append(hopsCounter)
		hopsCounter=-1
		
	ziplist = zip(listHops,listIPs)
	sortedlist = sorted(ziplist)
	bestHosts = [element for _,element in sortedlist]
	print("best hosts",bestHosts)
	return chosenIP


def senderFunction(p,X):
	fileName = X

	fileData = splitFile(fileName)


def downloadFunction(p,X,power=None,processing=None,bandwidth=None):
	global downloadedFiles
	global uploadedFiles
	global hostsHaveFile
	global bestHosts
	global state
	global RequiredPower,RequiredProcessing,RequiredBandwidth

	state = "receiving"
	print("The node that will help shouldnt have LESS than the following")
	fileName = X
	if power:
		RequiredPower = power
		RequiredProcessing = processing
		RequiredBandwidth = bandwidth
	else:
		
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
			print "#### Host ",src_ip," was added"
			print "Host ",src_ip, " current stats is:"
			print "Battery:",payloadData[7]," *** Power: ", payloadData[8]," *** Bandwidth:", payloadData[9]
			
	print("************************")
	if (len(hostsHaveFile) == 0):
		print("THERE IS NO NODE THAT MEET THE REQUIRED CONSTRAINTS")
		print("NO HOSTS TO RECEIVE HELP FROM")
		return
	print("hosts that can help",hostsHaveFile)
	print("Find the best node to receive help from.....")
	msgreturn = 'return~'+ ourIp +'~0~0~0~' + fileName
	choiceIP = hopsCount()
	hostsHaveFile = []
	p.set_new_config(src, choiceIP, msgreturn)
	p.do_send()
	downloadedFiles[fileName] = {}


def handlingLoss(destIP,p):
	print "**** Searching for another host to receive help from ****"
	time.sleep(2)
	ourIp = commands.getoutput('/sbin/ifconfig').split('\n')[10][13:21]
	msgreturn = 'return~'+ ourIp +'~0~0~0~' + 'help.txt'
	p.set_new_config(ourIp, destIP, msgreturn)
	print "Receiving help from",destIP
	p.do_send()
#               0               1                              2          3       4           5            
#Protocol : returnOrNot? ~ if return -> ip else -> data ~ numberOfData ~ size ~ toDelete ~ fileName ~ battery ~ processing ~ bandwidth

def handlePacket(r1,r2,r3,r4,r5,r6,p):
	packet_size , src_ip, dest_ip, ip_header, icmp_header , payLoad = p.do_receive()
	r1.put(packet_size)
	r2.put(src_ip)
	r3.put(dest_ip)
	r4.put(ip_header)
	r5.put(icmp_header)
	r6.put(payLoad)
	return

def receiverFunction(p):

	global i
	global returnIps
	global hostsHaveFile
	global Battery,processing,bandwidth,state,bestHosts,RequiredPower,RequiredProcessing,RequiredBandwidth,test
	
	ourIp = commands.getoutput('/sbin/ifconfig').split('\n')[10][13:21]
	
	packet_size , src_ip, dest_ip, ip_header, icmp_header , payLoad = "","","","","",""
	if ( state == "receiving" ):
		r1 = multiprocessing.Queue()
		r2 = multiprocessing.Queue()
		r3 = multiprocessing.Queue()
		r4 = multiprocessing.Queue()
		r5 = multiprocessing.Queue()
		r6 = multiprocessing.Queue()
		proc = multiprocessing.Process(target=handlePacket, args=[r1,r2,r3,r4,r5,r6,p])
		proc.start()
		proc.join(6)
		if (proc.is_alive()):
			proc.terminate()
			proc.join()
			receiverFunction(p)
			return
		else:
			packet_size , src_ip, dest_ip, ip_header, icmp_header , payLoad = r1.get(),r2.get(),r3.get(),r4.get(),r5.get(),r6.get()
			if(packet_size==0):
				#downloadFunction(p,'help.txt',power=RequiredPower,processing=RequiredProcessing,bandwidth=RequiredBandwidth)
				print "lost connection from",test
				bestHosts.pop(0)
				if(len(bestHosts) == 0):
					print "No Hosts found to receive help from."
					state = 'transmitting'
					return
				i = i-1
				handlingLoss(bestHosts[0],p)
		
	else:
		packet_size , src_ip, dest_ip, ip_header, icmp_header , payLoad = p.do_receive()
		
	if not packet_size == 0:
		payloadData = payLoad.split('~')
		
		 #If it was a downloaded data
		if(icmp_header['type'] == ping.ICMP_ECHO and (not payloadData[0] == 'return') and (not payloadData[0] == 'Available') and (not payloadData[0] == 'help') and state == 'receiving'):
			#print("payload",payLoad)
			if(i==0):
				print("help found on host with ip address",src_ip)
				
				print("======Mohamed159588======")
				print "Receiving help ... from",src_ip
				test=src_ip
				i=i+1
			fileName = payloadData[5]
			chunkNumber = int(payloadData[2])
			
			print ("***********Downloading data number %d from %s"%(chunkNumber,src_ip))

			downloadedFiles[fileName][chunkNumber] = payloadData[1]
			
			size = int(payloadData[3])
			#print("size",size)
			if(len(downloadedFiles[fileName]) == size):
				packData(fileName, size)
				
			receiverFunction(p)
		if(payloadData[0] == 'help'):
			if(uploadedFiles.__contains__(payloadData[5]) and float(payloadData[6]) <= Battery and float(payloadData[7]) <= processing and float(payloadData[8]) <= bandwidth):

				response = 'Available~'+ ourIp +'~0~0~0~0~' + payloadData[5] + '~' + str(Battery) + '~' + str(processing) + '~' + str(bandwidth)
				print "sending Available state to ", src_ip
				print "Device Current States are : "
				showDeviceInfo()
				p.set_new_config(dest_ip, src_ip, response)
				p.do_send()
			else:
				response = 'Unavailable~'+ ourIp +'~0~0~0~0~' + payloadData[5] + '~' + str(Battery) + '~' + str(processing) + '~' + str(bandwidth)
				print "sending Unavailable state to ", src_ip
				print "Device Current States are : "
				showDeviceInfo()
				p.set_new_config(dest_ip, src_ip, response)
				p.do_send()

		#If msg was return to home
		if(payloadData[0] == 'return' and src_ip != ourIp and state == 'transmitting'):
			returnIps[payloadData[5]] = payloadData[1]
			
			if(uploadedFiles.__contains__('help.txt') and src_ip != ourIp and state == 'transmitting'):
				print "*******sending help to",src_ip
				fileName = payloadData[5]
				chunkNumber = int(payloadData[2])
				#print "***********sending to %s data number %d for file %s"%(src_ip,chunkNumber, fileName)
				print "*******Sending the data requested to", src_ip
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
					#Made this to randomize the drop/loss of peer in order to simulate a real life situtation
					dropChance = random.randint(1,10)

					data = ''
					for j in range(i , i + 8):
						if j < len(fileData):
							data += fileData[j]
					payload = '0' + protocolTag + data + protocolTag + '%s'%(i/8) + protocolTag + str(length) + protocolTag  + '0' + protocolTag + fileName
					
					if (dropChance <= 2 and i != 0):
						print "drop chance",dropChance
						print "Host Disconnected"
						return
					else:
						p.set_new_config(dest_ip, src_ip, payload)
						p.do_send()
						print "sending payload ", data," ~ ", '%s'%(i/8)
						i = i + 8
				print("Help sent successfuly")
	
			elif(src_ip != ourIp and icmp_header['type'] == ping.ICMP_ECHOREPLY and state != "receiving"):

				return
			
			


def packData(fileName, size):
	global state,downloadedFiles
	#print ("**********Packing %s "%(fileName))
	print("Help received successfuly")
	
	state = "transmitting"
	f = open('./downloaded_' + fileName, 'wb+')
	for i in range(0, size):
		f.write(downloadedFiles[fileName][i])
	f.close()
	downloadedFiles = {}
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
				if buffer[i] == "u":
					senderFunction(p,'help.txt')
				elif buffer[i] == "help":
					downloadFunction(p,'help.txt')
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
