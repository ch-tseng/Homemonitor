#!/usr/bin/env python
# -*- coding: utf-8 -*-

import subprocess
import json
import time
import urllib2, time
import pygame
from pygame import mixer
from cStringIO import StringIO

def is_json(myjson):
	try:
        	json_object = json.loads(myjson)
        except ValueError, e:
        	return False
        return True

class TTSspech:

	def __init__(self):
        	self.words = "\"早安\""
                self.speaker = "\"Theresa\""
                self.volume = 100
                self.speed = 0
                self.pitchLevel = 2
                self.pitchSign = 0
                self.pitchScale = 0
		self.speakingAccu = 0   #目前累積正在speaking的
		self.busySpeaking = 0
		self.Channel = 0
		self.resultUrl = ""
		self.numGiveup = 120  #try幾次URL沒有回應後, 就放棄

	def setWords(self, words="\"早安\""):
		words = words.replace(".", "")
		words = words.replace("［", "")
		words = words.replace("］", "，")
		words = words.replace("[", "")
		words = words.replace("]", "，")
		words = words.replace("　", "，")
                words = words.replace(" ", "，")
                words = words.replace("．", "，")
                words = words.replace("。", "，")
                words = words.replace(",", "，")
		words = words.replace('\n', '，').replace('\r', '，')
		self.words = "\"" + words + "\""

	def setSpeaker(self, speaker="\"Theresa\""):
		self.speaker = "\"" + speaker + "\""

	def setVolume(self, volume=100):
		self.volume = volume

	def setSpeed(self, speed=-3):
		self.speed = speed

	def setPitchLevel(self, pitchLevel=0):
		self.pitchLevel = pitchLevel

	def setPitchSign(self, pitchSign=0):
		self.pitchSign = pitchSign

	def setPitchScale(self, pitchScale=0):
		self.pitchScale = pitchScale

	def isBusySpeakingNow(self):
		return self.busySpeaking

	def createConvertID(self):
		phpScript = "php voice1.php " + self.words + " " + self.speaker + " " + str(self.volume) + " " + str(self.speed) + " " + str(self.pitchLevel) + " " + str(self.pitchSign) + " " + str(self.pitchScale);
		proc = subprocess.Popen( phpScript, shell = True, stdout = subprocess.PIPE)
		phpResponse = proc.stdout.read()
		print phpResponse
		if(is_json(phpResponse)):
			decodejson =  json.loads(phpResponse)
			print decodejson["resultConvertID"]
			self.resultConvertID = decodejson["resultConvertID"]
			self.resultString = decodejson["resultString"]
			self.resultCode = decodejson["resultCode"]

			return decodejson["resultConvertID"]
		else:
			return 0

	def getVoiceURL(self):
		resultCode = "1"
		statusCode = "0"

		phpScript = "php voice2.php " + self.resultConvertID

		i=0
		#while ((resultCode!="0" or statusCode!="2")):
		while ((statusCode=="0" or statusCode=="1") and i<self.numGiveup):
			proc = subprocess.Popen(phpScript, shell=True, stdout=subprocess.PIPE)
			phpResponse = proc.stdout.read()
			print str(i) + ') ' + phpResponse
			decodejson =  json.loads(phpResponse)

			resultCode = decodejson["resultCode"]
			statusCode = decodejson["statusCode"]
			#time.sleep(1)
			i+=1

		print "self.resultUrl: " + decodejson["resultUrl"] 
		self.resultUrl = decodejson["resultUrl"]
		self.resultCode = decodejson["resultCode"]
		self.resultString = decodejson["resultString"]
		self.statusCode = decodejson["statusCode"]
		self.status = decodejson["status"]
		
		return decodejson["resultUrl"]

	def playMusic(self, music_file="music/a2.mp3", volume=0.8):

		freq = 44100     # audio CD quality
		bitsize = -16    # unsigned 16 bit
		channels = 2     # 1 is mono, 2 is stereo
		buffer = 2048    # number of samples (experiment to get best sound)
		pygame.mixer.init(freq, bitsize, channels, buffer)
		# volume value 0.0 to 1.0
		pygame.mixer.music.set_volume(volume)
		clock = pygame.time.Clock()

		try:
			pygame.mixer.music.load(music_file)
	        	print("Music file {} loaded!".format(music_file))

		except pygame.error:
			print("File {} not found! ({})".format(music_file, pg.get_error()))
			return

		pygame.mixer.music.play()

		#while pygame.mixer.music.get_busy():
		        # check if playback has finished
		 #       clock.tick(30)

	def playVoice(self, voiceFrequency=22050, totalChannels=1):
		tmpURL = self.resultUrl

		if(tmpURL[-3:]=="wav"):
			f = urllib2.urlopen(self.resultUrl).read()
			pygame.mixer.init(voiceFrequency, -16, totalChannels)  #frequency, size, channels
			Channel = pygame.mixer.Channel(0)

			snd = StringIO(f)
			sound = pygame.mixer.Sound(snd)
			self.speakingAccu+=1
			print "Channel.get_busy --> "
			print Channel.get_busy()
			print self.speakingAccu
		
			if(Channel.get_busy()):
				while (Channel.get_busy()>0):
					time.sleep( 0.05 )
				Channel = sound.play()
			else:
	                        Channel = sound.play()

		#if(self.speakingAccu>1):
		#	if(Channel.get_busy()):
		#		while (Channel.get_busy()>0):
	        #                        time.sleep( 0.05 )
		#	else:
		#		Channel = sound.play()
		#		self.speakingAccu-=1
		#else:
		#	if(Channel.get_busy()):
		#		print "go to download another wav."
		#	else:
		#		Channel = sound.play()
		#		self.speakingAccu-=1



#person = TTSspech()
#person.setWords("午安, 您吃過飯了嗎?")
#print person.createConvertID()
##time.sleep(5)
#print person.getVoiceURL()
##time.sleep(5)
#person.playVoice()
