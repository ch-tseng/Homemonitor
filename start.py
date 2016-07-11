#!/usr/bin/env python
# -*- coding: utf-8 -*-

#=======CONFIGURE============================================
APIKEY_MAILGUN = "key-YOUR-API-KEY"
API_MAILGUN_DOMAIN = "YOUR-DOMAIN"

#-for mode 1 ---------------------
tvList = ["wav/tv/tv1.mp3", "wav/tv/tv2.mp3", "wav/tv/tv3.mp3", "wav/tv/tv4.mp3", "wav/tv/tv5.mp3", "wav/tv/tv6.mp3", "wav/tv/tv7.mp3"]

PIR_sleep_PictureAgainPeriod = 30  #要休息幾秒再度開始一輪的拍攝
PIR_sleep_take_2_PicturesPeriod = 0.5  #拍攝每張相片的間隔時間

modeSecutirt_waittime = 300  # 180, 300, 600, 900 設定外出模式後. 幾秒後才會開始動作.
#-for all mode ------------------------------
ENV_checkPeriod = 180  #幾秒要偵測一次溫溼度等環境值
ENV_takePicture_period = 1800  #居家或外出模式下，每隔幾秒拍一次

securityAuto = 0 # 半夜是否自動轉為安全模式，0為否，1為是
securityAuto_start = 1  #開始時間(24小時制)
securityAuto_end = 6  #結束時間(24小時制)

msgSMS = "PIR Alert! 家中有人入侵，請注意。"

speakVolume = "+700"  #音量大小

localImageSize_w = 1296
localImageSize_h = 972
uploadImageSize_w = 720
uploadImageSize_h = 480

##蘋果日報-財經總覽 "http://www.appledaily.com.tw/rss/newcreate/kind/sec/type/8"
##蘋果日報-頭條 "http://www.appledaily.com.tw/rss/newcreate/kind/sec/type/1077"
##聯合報-要聞 "http://udn.com/udnrss/BREAKINGNEWS1.xml"
##聯合報-財經 "http://udn.com/udnrss/BREAKINGNEWS6.xml"
##聯合報-財經焦點 "http://udn.com/udnrss/financesfocus.xml"
##天下雜誌 "http://www.cw.com.tw/RSS/cw_content.xml"
##自由時報-頭版 "http://news.ltn.com.tw/rss/focus.xml"
##自由時報-財經 "http://news.ltn.com.tw/rss/business.xml"
##中央氣象局警報、特報 "http://www.cwb.gov.tw/rss/Data/cwb_warning.xml"
##商業周刊 - 最新綜合文章 "http://bw.businessweekly.com.tw/feedsec.php?feedid=0"
##國民健康署 » 新聞 "http://www.hpa.gov.tw/Bhpnet/Handers/RSSHandler.ashx?c=news"
##NEWSREPORT_URL = "http://www.appledaily.com.tw/rss/newcreate/kind/sec/type/1077"
##NEWSREPORT_SPEAKER = "MCHEN_Bruce"

# ---------------------------------->尚待完成
#A1:目前時間 A2:靜思語 A3:外面天氣 A4:室內狀況 A5:新聞播報 A6:今日預約提醒 A7:明日預約提醒 A8:未來預約提醒 A80:開頭語 A99:結語
#schedule_workingDay = [ {"time": "07:15", "action": ["A80", "A2", "A4", "A3", "A5", "A6"]}, {"time":"12:00", "action": ["A80", "A4", "A3", "A2"]}, {"time":"18:30", "action": ["A1","A4","A3","A2","A7","A8"]} ]
#schedule_offDay = [ {"time":"11:30", "action": ["A4","A3","A6"] } ]

#S1:播放音樂  S2:播放電視  S3:播放錄音人聲
#schedule_security = [ {"time":"09:30", "action":["S1", "S3"]}, {"time":"12:30", "action": ["S2"]}, {"time":"18:00", "action": ["S2"]}. {"time":"21:30","action":["S1","S2","S3"]} ]
#<--------------------------------------


#======MODULES================================================
import RPi.GPIO as GPIO
import os, sys
from subprocess import call
import requests
import mcp3008
import time
import Adafruit_DHT as dht
import logging, random
import picamera
import speechClass
import urllib
import json

# Cloudinary ---------------------------
from cloudinary.uploader import upload
from cloudinary.utils import cloudinary_url
from cloudinary.api import delete_resources_by_tag, resources_by_tag

#=====SYSTEM===================================================
reload(sys)
sys.setdefaultencoding('utf8')

camera = picamera.PiCamera()
camera.sharpness = 10
camera.contrast = 10
camera.brightness = 50
camera.saturation = 10
camera.resolution = (localImageSize_w, localImageSize_h)
camera.ISO = 400
camera.video_stabilization = False
camera.exposure_compensation = 0
camera.exposure_mode = 'auto'
camera.meter_mode = 'average'
camera.awb_mode = 'auto'
camera.image_effect = 'none'
camera.color_effects = None
camera.rotation = 0
camera.hflip = True
camera.vflip = True
camera.crop = (0.0, 0.0, 1.0, 1.0)

pinPIR = 35
pinPIR2 = 8
pinDHT22 = 13
pinLED_RED = 38
pinLED_BLUE = 36
pinLED_YELLOW = 40
pinBTN_Security = 32

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)
GPIO.setup(pinBTN_Security, GPIO.IN, pull_up_down=GPIO.PUD_UP) #使用內建的上拉電阻

GPIO.setup(pinPIR ,GPIO.IN)
GPIO.setup(pinPIR2 ,GPIO.IN)
GPIO.setup(pinLED_RED ,GPIO.OUT)
GPIO.setup(pinLED_YELLOW ,GPIO.OUT)
GPIO.setup(pinLED_BLUE ,GPIO.OUT)

os.chdir(os.path.join(os.path.dirname(sys.argv[0]), '.'))  # for Cloudinary

logger = logging.getLogger('msg')
hdlr = logging.FileHandler('/home/pi/monitor/msg.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr)
logger.setLevel(logging.INFO)

PIR_last_pictureTime = time.time()  #上次拍攝相片時間

ENV_warning_repeat_period = 120  #相同的警示提示音, 要間隔多少秒再提醒一次
ENV_lastwarningtime = 0  #上次警示提示音的時間

ENV_lstchecktime = 0  #上次偵測環境值的時間

modeOperation = 0  # 0 -> 儲存目前的運作模式, 一般模式  1 -> 外出模式
modeSecutiry_starttime = 0  #儲存外出模式的開始時間, 預設在 modeSecutirt_waittime 後才開始動作

lastHourlySchedule = 999 #上次每小時固定執行工作的執行時間(小時)
btn_secutiry_lastclicktime = 0   #上次按按鈕的時間, 以避免多次觸發

lastENV_takePicture_period = time.time()  # 居家或外出模式下，上次每隔幾秒拍一次的時間
lastPlayTV = time.time()  #上次播放TV聲的時闁

lastPIRfounded = "" #上次PIR發現到人的時間
lightDegree = 0  #目前燈光的照明度

autoSecutiryNow = 0  #自動模式時，目前是否在設定的安全模式時間啟用內

#===Functions===========================================================

def is_json(myjson):
	try:
		json_object = json.loads(myjson)
	except ValueError, e:
		return False
	return True

def send_mailgun(apikey, domainName, imagefile, toEmail, ccEmail, txtSubject, txtContent):
        return requests.post(
                "https://api.mailgun.net/v3/"+domainName+"/messages",
                auth=("api", apikey),
                files=[("attachment", open(imagefile))
                        ],
                data={"from": "HomeMonitor <monitor@"+domainName+">",
                        "to": toEmail,
                        "cc": ccEmail,
#                       "bcc": "bar@example.com",
                        "subject": txtSubject,
                        "text": txtContent
#                       "html": "<html>HTML version of the body</html>"
                        })

def sendSMS(msg):
	return requests.post(
		"http://data.sunplusit.com/Api/SNSMS?code=FB4A77FFA62AD06F48257C190013FB76",
		data={ "subject": msg })

def send_mailgun_multi(apikey, domainName, imagefile1, imagefile2, imagefile3, toEmail, ccEmail, txtSubject, txtContent):
	return requests.post(
		"https://api.mailgun.net/v3/"+domainName+"/messages",
		auth=("api", apikey),
		files=[("attachment", open(imagefile1))
			,("attachment", open(imagefile2))
			,("attachment", open(imagefile3))
			],
		data={"from": "HomeMonitor <monitor@"+domainName+">",
			"to": toEmail,
			"cc": ccEmail,
#			"bcc": "bar@example.com",
			"subject": txtSubject,
			"text": txtContent
#			"html": "<html>HTML version of the body</html>"
			})

def number2speakwords(numValue):
	strTMP = str(numValue)
	unitSpeak = ["", "十", "百", "千", "萬", "十", "百", "千"]

	if strTMP.find('.')==-1:
		strIntNum = strTMP
		strDecimal = ""
	else:
		NumSplit = strTMP.split('.')
		strIntNum = NumSplit[0]
		strDecimal = NumSplit[1]

	if len(strIntNum)>2 and strIntNum[len(strIntNum)-2]=="0": #十位是0
		if strIntNum[len(strIntNum)-1]!="0":
			nitSpeak[1] = '零'
		else:
			unitSpeak[1] = ''

	if len(strIntNum)>3 and strIntNum[len(strIntNum)-3]=="0": #百位是0
		unitSpeak[2] = ' '
	if len(strIntNum)>4 and strIntNum[len(strIntNum)-4]=="0": #千位是0
		unitSpeak[3] = ' '

	if len(strIntNum)>5:
		if strIntNum[len(strIntNum)-5]!="0": #萬位不是0
			unitSpeak[4] = "萬"
		else:
			unitSpeak[4] = ' '

		if len(strIntNum)>5 and strIntNum[len(strIntNum)-6]!="0": #萬位是0, 十萬位不是0
			unitSpeak[5] = "十萬"
		elif len(strIntNum)>6 and strIntNum[len(strIntNum)-7]!="0": #十萬位是0, 百萬位不是0
			unitSpeak[6] = "百萬"
		elif len(strIntNum)>7 and strIntNum[len(strIntNum)-8]!="0": #百萬位是0, 千萬位不是0
			unitSpeak[7] = "千萬"

	stringIntSpeak = ""
	for i in range(0, len(strIntNum)):
		stringIntSpeak = stringIntSpeak + strIntNum[i] + unitSpeak[len(strIntNum)-i-1]
		i=i+1

	stringIntSpeak = stringIntSpeak.replace("0", "")

	if len(strDecimal)>0:
		return stringIntSpeak + "點" + strDecimal
	else:
		return stringIntSpeak

def speakWords(wordsSpeak, speakerName, frequency, speed):
	nessContent = wordsSpeak
	newsArray = nessContent.split("｜")
	i=0
	person = speechClass.TTSspech()

	for newsSpeak in newsArray:
		logger.info("(" + str(len(newsSpeak)) + ") " + newsSpeak)
		person.setWords("\"" + newsSpeak + "\"")
		person.setSpeaker("\"" + speakerName + "\"")  # Bruce, Theresa, Angela, MCHEN_Bruce, MCHEN_Jo$
		person.setSpeed(speed)

		id = int(person.createConvertID())
		logger.info("URL: " + person.getVoiceURL())
		if(id>0):
			person.playVoice(frequency ,5)	

def lightLED(mode):
	if mode == 0:	#居家模式
		GPIO.output(pinLED_BLUE, GPIO.LOW)
		GPIO.output(pinLED_RED, GPIO.LOW)
		GPIO.output(pinLED_YELLOW, GPIO.HIGH)
	elif mode == 1:	# 外出模式
		GPIO.output(pinLED_BLUE, GPIO.HIGH)
		GPIO.output(pinLED_RED, GPIO.LOW)
		GPIO.output(pinLED_YELLOW, GPIO.LOW)
	elif mode == 2: # 自動模式
                GPIO.output(pinLED_BLUE, GPIO.LOW)
                GPIO.output(pinLED_RED, GPIO.HIGH)
                GPIO.output(pinLED_YELLOW, GPIO.LOW)
	elif mode == 6: # 拍照
                GPIO.output(pinLED_BLUE, GPIO.LOW)
                GPIO.output(pinLED_RED, GPIO.HIGH)
                GPIO.output(pinLED_YELLOW, GPIO.HIGH)
	elif mode == 7: # 說話
                GPIO.output(pinLED_BLUE, GPIO.HIGH)
                GPIO.output(pinLED_RED, GPIO.HIGH)
                GPIO.output(pinLED_YELLOW, GPIO.LOW)
	elif mode == 9: # 不發光
                GPIO.output(pinLED_BLUE, GPIO.LOW)
                GPIO.output(pinLED_RED, GPIO.LOW)
                GPIO.output(pinLED_YELLOW, GPIO.LOW)
	else:
		GPIO.output(pinLED_BLUE, GPIO.HIGH)
		GPIO.output(pinLED_RED, GPIO.HIGH)
		GPIO.output(pinLED_YELLOW, GPIO.HIGH)

def playWAV(wavFile):
	lightLED(7)
	logger.info("PLAY WAV: "+wavFile)
	#call('omxplayer --no-osd ' + wavFile)
	call(["omxplayer","--vol", speakVolume, "--no-osd",wavFile])
	lightLED(9)
			
#--Cloudinary--------------------------
def dump_response(response):
	logger.info("Upload response:")
	for key in sorted(response.keys()):
		logger.info("  %s: %s" % (key, response[key]))

def upload_files(filename, width, height, tag, pid):
	logger.info("--- Upload a local file with custom public ID")
	response = upload(filename,
		tags = tag,
		public_id = pid,
	)
	dump_response(response)

	url, options = cloudinary_url(response['public_id'],
		format = response['format'],
		width = width,
		height = height,
		crop = "fit"
	)
	logger.info("Image uploaded to url: " + url)
	
#--Actions------------------------------
def read_Sentence1():  #靜心語
	wavNumber = str(random.randint(1, 80))
	playWAV("wav/sentence1/start.wav")
	playWAV("wav/sentence1/"+wavNumber+".wav")	


def read_Weather():
	lightLED(0)
	dt = list(time.localtime())
	nowYear = dt[0]
	nowMonth = dt[1]
	nowDay = dt[2]
	nowHour = dt[3]
	nowMinute = dt[4]

	link = "http://data.sunplusit.com/Api/WeatherUVIF"
	f = urllib.urlopen(link)
	myfile = f.read()
	jsonData = json.loads(myfile)
	nowUV = "而目前室外紫外線指數是" + jsonData[0]['UVIStatus'] + ", " + jsonData[0]['ProtectiveMeasure']
	
	link = "http://data.sunplusit.com/Api/WeatherCWB"
	f = urllib.urlopen(link)
	myfile = f.read()
	jsonData = json.loads(myfile)
	nowWeather_tmp = "目前室外的氣象是" + jsonData[0]['Weather'] + ", " + jsonData[0]['Precipitation'] + ", " + jsonData[0]['Temperature'] + ", " +  jsonData[0]['RelativeHumidity'] + ", 整體來說氣候是" + jsonData[0]['ConfortIndex']
	nowWeather = nowWeather_tmp.replace("為", "是 ")

	link = "http://data.sunplusit.com/Api/WeatherAQX"
	f = urllib.urlopen(link)
	myfile = f.read()
	jsonData = json.loads(myfile)
	nowAir_tmp = "另外, 關於室外空氣指數部份, 目前室外的PM2.5數值為" + number2speakwords(jsonData[0]['PM25']) + ", PM十的數值為" + number2speakwords(jsonData[0]['PM10']) + ", 空氣品質PSI指數為" + number2speakwords(jsonData[0]['PSI']) + ", 整體來說空氣品質" + jsonData[0]['Status'] + ", " + jsonData[0]['HealthEffect'] + ", 建議" + jsonData[0]['ActivitiesRecommendation']
	nowAir_tmp = nowAir_tmp.replace(".", "點")
	nowAir = nowAir_tmp.replace("為", "是 ")
	
	speakString = "今天" + str(nowYear) + "年" + number2speakwords(int(nowMonth)) + "月" + number2speakwords(int(nowDay)) + "日  " + number2speakwords(int(nowHour)) + "點" + number2speakwords(int(nowMinute)) + "分  ," + nowWeather + " , " + nowUV + nowAir
	logger.info(speakString)

	speakWords(speakString, "MCHEN_Bruce", 15600, 0)
	lightLED(9)

def alarmSensor(nowT, nowH, nowLight, nowGAS ):

	arrayWAVs = []
	
	if(nowGAS>100):
		arrayWAVs.append("wav/sensor/w2.wav") #危險，危險！空氣中偵測到媒氣外洩，請立即開門窗並檢查家中瓦斯！
		
	if(nowT<=16):
		#sensorAlarm+="現在室內氣溫為" + str(nowT) + "度，相當寒冷，建議您一定要多穿衣服保暖。"
		arrayWAVs.append("wav/sensor/w3.wav")  #現在室內氣溫為
		arrayWAVs.append("wav/number/" + str(nowT) + ".wav")
		arrayWAVs.append("wav/sensor/unitc.wav")   #度C
		arrayWAVs.append("wav/sensor/w4.wav")  #建議您一定要多穿衣服保暖。
	elif(nowT<=22 and nowT>16):
		#sensorAlarm+="現在室內氣溫為" + str(nowT) + "度，有些寒冷，建議您可以多穿件衣服保暖，以免感冒了。"
		arrayWAVs.append("wav/sensor/w3.wav")  #現在室內氣溫為
		arrayWAVs.append("wav/number/" + str(nowT) + ".wav")
		arrayWAVs.append("wav/sensor/unitc.wav")   #度C
		arrayWAVs.append("wav/sensor/w5.wav")  #有些寒冷，建議您可以多穿件衣服保暖，以免感冒了。
	elif(nowT<=30 and nowT>25):
		#sensorAlarm+="現在室內氣溫為" + str(nowT) + "度，氣溫剛剛好，相當舒適。"
		arrayWAVs.append("wav/sensor/w3.wav")  #現在室內氣溫為
		arrayWAVs.append("wav/number/" + str(nowT) + ".wav")
		arrayWAVs.append("wav/sensor/unitc.wav")   #度C
		arrayWAVs.append("wav/sensor/w6.wav")  #氣溫剛剛好，相當舒適。
	elif(nowT<=35 and nowT>30):
		#sensorAlarm+="現在室內氣溫為" + str(nowT) + "度，感覺有些悶熱，建議您可開啟空調冷氣來降低室溫。"
		arrayWAVs.append("wav/sensor/w3.wav")  #現在室內氣溫為
		arrayWAVs.append("wav/number/" + str(nowT) + ".wav")
		arrayWAVs.append("wav/sensor/unitc.wav")   #度C
		arrayWAVs.append("wav/sensor/w7.wav")  #感覺有些悶熱，建議您可開啟空調冷氣來降低室溫。
	elif(nowT<=40 and nowT>35):
		#sensorAlarm+="現在室內氣溫異常悶熱，已經" + str(nowT) + "度了，請立即檢查您的空調及冷氣系統。"
		arrayWAVs.append("wav/sensor/w8.wav")  #現在室內氣溫異常悶熱，已經有
		arrayWAVs.append("wav/number/" + str(nowT) + ".wav")
		arrayWAVs.append("wav/sensor/unitc.wav")   #度C
		arrayWAVs.append("wav/sensor/w9.wav")  #度了，請立即檢查您的空調及冷氣系統。
	elif(nowT>40):
		#sensorAlarm+="危險，危險！現在室內溫度高達" + str(nowT) + "度，已經超過常人可忍受的溫度警戒值，可能有火災發生，請注意安全。"
		arrayWAVs.append("wav/sensor/w10.wav")  #危險，危險！現在室內溫度高達
		arrayWAVs.append("wav/number/" + str(nowT) + ".wav")
		arrayWAVs.append("wav/sensor/unitc.wav")   #度C
		arrayWAVs.append("wav/sensor/w11.wav")	#已經超過常人可忍受的溫度警戒值，可能有火災發生，請檢查家中火源並注意安全。
	
	for sentence in arrayWAVs:
		playWAV(sentence)
	
	arrayWAVs = []
	
	if(nowH<=30):
		arrayWAVs.append("wav/sensor/w20.wav")  #溼度則是
		arrayWAVs.append("wav/number/" + str(nowH) + ".wav")
		arrayWAVs.append("wav/sensor/unitpercent.wav")   #%
		arrayWAVs.append("wav/sensor/w21.wav")  #空氣比較乾燥
	elif(nowH<=75 and nowH>30):
		arrayWAVs.append("wav/sensor/w20.wav")  #溼度則是
		arrayWAVs.append("wav/number/" + str(nowH) + ".wav")
		arrayWAVs.append("wav/sensor/unitpercent.wav")   #%
		arrayWAVs.append("wav/sensor/w22.wav")  #溼度正常相當舒服
	elif(nowH>75):
		arrayWAVs.append("wav/sensor/w20.wav")  #溼度則是
		arrayWAVs.append("wav/number/" + str(nowH) + ".wav")
		arrayWAVs.append("wav/sensor/unitpercent.wav")   #%
		arrayWAVs.append("wav/sensor/w23.wav")  #室內空氣很潮溼哦, 請考慮是否打開除潮機
		
	for sentence in arrayWAVs:
		playWAV(sentence)
		
def timeTell(hour, minute):
	arrayWAVs = []
	
	arrayWAVs.append("wav/clock/c1.wav")	#目前時刻
	#arrayWAVs.append("wav/number/" + str(hour) + ".wav")
	arrayWAVs.append("wav/hour/" + str(hour) + ".wav")
	#arrayWAVs.append("wav/clock/hour.wav")   #點
	#arrayWAVs.append("wav/number/" + str(minute) + ".wav")
	#arrayWAVs.append("wav/clock/minute.wav")   #分

	for sentence in arrayWAVs:
		playWAV(sentence)

def EnvWarning(T, H, MQ4):
	global modeOperation, ENV_lastwarningtime, ENV_warning_repeat_period

	logger.info("Environment warning!")
	captureTime = time.localtime()

	if ((time.time()-ENV_lastwarningtime))>ENV_warning_repeat_period:
		picture_date = time.strftime("%H點%M分%S秒", captureTime)
		picture_filename1 = time.strftime("%Y%m%d%H%M%S", captureTime) + '1.jpg'
		camera.capture(picture_filename1)
		time.sleep(PIR_sleep_take_2_PicturesPeriod)
		upload_files(picture_filename1, 2048, 2048, "PIR_1", picture_filename1)

		picture_date = time.strftime("%H點%M分%S秒", captureTime)
		picture_filename2 = time.strftime("%Y%m%d%H%M%S", captureTime) + '2.jpg'
		camera.capture(picture_filename2)
		time.sleep(PIR_sleep_take_2_PicturesPeriod)
		upload_files(picture_filename2, 2048, 2048, "PIR_2", picture_filename2)

		picture_date = time.strftime("%H點%M分%S秒", captureTime)
		picture_filename3 = time.strftime("%Y%m%d%H%M%S", captureTime) + '3.jpg'
		camera.capture(picture_filename3)
		time.sleep(PIR_sleep_take_2_PicturesPeriod)
		upload_files(picture_filename3, 2048, 2048, "PIR_3", picture_filename3)
			
		txtSubject = "環境警報:"
		txtContent = ""
		if T>45:
			txtSubject += "溫度超過45度C "
			txtContent += "目前家中的溫度是" + T + "度C。"
		if MQ4>120:
			txtSubject += "煤氣可能外洩 "
			txtContent += "目前家中的煤氣指數是" + MQ4 + "。"
				
		send_mailgun(APIKEY_MAILGUN, API_MAILGUN_DOMAIN, picture_filename1, picture_filename2 , picture_filename3,  "myvno@hotmail.com", "ch.tseng@sunplusit.com", txtSubject, txtContent + ", 已立即拍攝相片，時間為" + picture_date + "。")
		ENV_lastwarningtime = time.time()

def playTV():
	lightLED(7)
	tvfile = random.choice(tvList)
        logger.info("PLAY TV FileV: "+tvfile)
        #call('omxplayer --no-osd ' + wavFile)
        call(["omxplayer","--vol",speakVolume,"--no-osd",tvfile])
	lightLED(9)


def takePicture(typePIC, subject, content):
	global modeOperation, lightDegree
	lightLED(6)
	camera.ISO = 100

	if lightDegree>50 and lightDegree<70:
		camera.ISO = 200
	elif lightDegree<=50 and lightDegree>30:
		camera.ISO = 400
	elif lightDegree<=30 and lightDegree>20:
                camera.ISO = 600
	elif lightDegree<=20:
                camera.ISO = 800

	captureTime = time.localtime()
	picture_date = time.strftime("%H點%M分%S秒", captureTime)
	picture_filename = time.strftime("%Y%m%d%H%M%S", captureTime) + '.jpg'
	camera.capture(picture_filename)
	logger.info("ISO:" + str(camera.ISO) + " / LightDegree:" + str(lightDegree) + " / A picture was taken: " + picture_filename )
	logger.info("picture_filename=" + picture_filename + " / uploadImageSize_w=" + str(uploadImageSize_w) + " / uploadImageSize_h=" + str(uploadImageSize_h) + " / typePIC=" + typePIC + " / picture_filename=" + picture_filename)
	upload_files(picture_filename, uploadImageSize_w, uploadImageSize_h, typePIC, picture_filename)
	#send_mailgun(APIKEY_MAILGUN, API_MAILGUN_DOMAIN, picture_filename, "myvno@hotmail.com", "ch.tseng@sunplusit.com", "PIR警報：有人入侵 " + picture_date, "PIR偵測到有人進入客廳, 已立即拍攝相片，時間為" + picture_date + "。")
	send_mailgun(APIKEY_MAILGUN, API_MAILGUN_DOMAIN, picture_filename, "myvno@hotmail.com", "ch.tseng@sunplusit.com", "監測時間" + picture_date + ": " + subject, content + "\n\n 相片拍攝時間為" + picture_date)

	lightLED(9)	

def speakTime(hour, minute):
	arrayWAVs = []

	arrayWAVs.append("wav/number/" + str(hour) + ".wav")
	#arrayWAVs.append("wav/hour/" + str(hour) + ".wav")
	arrayWAVs.append("wav/clock/hour.wav")   #點
	arrayWAVs.append("wav/number/" + str(minute) + ".wav")
	arrayWAVs.append("wav/clock/minute.wav")   #分

        for sentence in arrayWAVs:
                playWAV(sentence)
	
#for Interrupts--------------------------
def MOTION(pinPIR):
	global lastPIRfounded, PIR_last_pictureTime, modeOperation, modeSecutiry_starttime, ENV_lastwarningtime, ENV_warning_repeat_period, autoSecutiryNow, msgSMS
	lightLED(modeOperation)
	#time.sleep(3)	
	captureTime = time.localtime()
	lastPIRfounded = time.strftime("%Y/%m/%d %H:%M:%S", captureTime)

	#print ("Security mode will start after " + str(modeSecutirt_waittime - (time.time()-modeSecutiry_starttime)))
	if (modeOperation==1 and modeSecutiry_starttime>0 and ((time.time()-modeSecutiry_starttime)>modeSecutirt_waittime)) or (modeOperation==2 and autoSecutiryNow==1):
		logger.info("Motion Detected!")
		picIndex = time.strftime("%Y%m%d%H%M%S", captureTime)

		if ((time.time()-PIR_last_pictureTime))>PIR_sleep_PictureAgainPeriod:
			#playWAV("wav/warning/warning1.wav")
			#try:
			#	sendSMS(msgSMS)
			#except:
			#	logger.info("Unexpected error:", sys.exc_info()[0])

			takePicture("PIR-"+picIndex+"-1", "PIR偵測", "PIR偵測到有人進入客廳！")			
			time.sleep(PIR_sleep_take_2_PicturesPeriod)
			takePicture("PIR-"+picIndex+"-2", "PIR偵測", "PIR偵測到有人進入客廳！")
			time.sleep(PIR_sleep_take_2_PicturesPeriod)
			takePicture("PIR-"+picIndex+"-3", "PIR偵測", "PIR偵測到有人進入客廳！")

			#send_mailgun(APIKEY_MAILGUN, API_MAILGUN_DOMAIN, picture_filename1, picture_filename2 , picture_filename3,  "myvno@hotmail.com", "ch.tseng@sunplusit.com", "PIR警報：有人入侵 " + picture_date, "PIR偵測到有人進入客廳, 已立即拍攝相片，時間為" + picture_date + "。")

			playWAV("wav/warning/warning1.wav")

			time.sleep(PIR_sleep_take_2_PicturesPeriod)
                        takePicture("PIR-"+picIndex+"-4", "PIR偵測", "PIR偵測到有人進入客廳！")
			time.sleep(PIR_sleep_take_2_PicturesPeriod)
                        takePicture("PIR-"+picIndex+"-5", "PIR偵測", "PIR偵測到有人進入客廳！")

			PIR_last_pictureTime = time.time()
			lightLED(9)
	else:
		if modeOperation==1:
			if ((time.time()-ENV_lastwarningtime))>ENV_warning_repeat_period:
				tmpTime = (modeSecutirt_waittime - (time.time()-modeSecutiry_starttime))/60
				logger.info("In TIME: " + str(tmpTime) )

				if tmpTime<=1:
					playWAV("wav/startIn1min.wav")
				elif tmpTime<=3 and tmpTime>1:
					playWAV("wav/startIn3min.wav")
				elif tmpTime<=5 and tmpTime>3:
					playWAV("wav/startIn5min.wav")
				elif tmpTime<=10 and tmpTime>5:
					playWAV("wav/startIn10min.wav")
				elif tmpTime<=30 and tmpTime>10:
					playWAV("wav/startIn30min.wav")
				elif tmpTime>30:
					playWAV("wav/startAfter30min.wav")

				ENV_lastwarningtime = time.time()
	lightLED(9)

def change_Mode(securiityMode):
	global modeOperation, securityAuto, modeSecutiry_starttime
	
	lightLED(securiityMode)

	if securiityMode==0:
		securityAuto = 0
		modeSecutiry_starttime = 0
		call(["omxplayer","--vol",speakVolume,"--no-osd", "wav/mode0.wav"])
	elif securiityMode==1:
		securityAuto = 0
		modeSecutiry_starttime = time.time()
		call(["omxplayer","--vol",speakVolume,"--no-osd", "wav/mode1.wav"])
	elif securiityMode==2:
		securityAuto = 1
		modeSecutiry_starttime = 0
		call(["omxplayer","--vol",speakVolume,"--no-osd", "wav/mode2a.wav"])
		speakTime(securityAuto_start, 0)
		call(["omxplayer","--vol",speakVolume,"--no-osd", "wav/to.wav"])
		if securityAuto_end<securityAuto_start:
			call(["omxplayer","--vol",speakVolume,"--no-osd", "wav/nextday.wav"])
		speakTime(securityAuto_end, 0)
		call(["omxplayer","--vol",speakVolume,"--no-osd", "wav/activesecurity.wav"])

def btn_Security(pinBTN_Security):
	global modeOperation, modeSecutiry_starttime, btn_secutiry_lastclicktime, securityAuto
	if (time.time()-btn_secutiry_lastclicktime)>3:

		if modeOperation == 0:
			modeOperation = 1

		elif modeOperation == 1:
			modeOperation = 2

		elif modeOperation == 2:
			modeOperation = 0
	
		change_Mode(modeOperation)

		logger.info('Button Pressed, mode change to ' + str(modeOperation))
		btn_secutiry_lastclicktime = time.time()

		fo = open("finalStatus", "wb")
		fo.write(str(modeOperation))
		fo.close()
		lightLED(9)

def motion_outdoor(pinPIR2):
	global uploadImageSize_w, uploadImageSize_h, APIKEY_MAILGUN, API_MAILGUN_DOMAIN

	dt = list(time.localtime())
	#nowYear = dt[0]
	#nowMonth = dt[1]
	#nowDay = dt[2]
	nowHour = dt[3]
	nowMinute = dt[4]

	if nowHour>18:
		lightLED(6)
		logger.info("Outdoor PIR dectected!")
		playWAV("wav/warning/warning2.wav")

		#captureTime = time.localtime()
	        #picture_date = time.strftime("%H點%M分%S秒", captureTime)
		#picture_filename = time.strftime("%Y%m%d%H%M%S", captureTime) + '.jpg'
		#call(["fswebcam","-r", "1280x720", "--no-banner",picture_filename])

		#logger.info("A outdoor picture was taken: " + picture_filename )
	        #upload_files(picture_filename, uploadImageSize_w, uploadImageSize_h, "Outdoor", picture_filename)
	        #send_mailgun(APIKEY_MAILGUN, API_MAILGUN_DOMAIN, picture_filename, "myvno@hotmail.com", "ch.tseng@sunplusit.com", "門口有人警報：" + picture_date, "相片拍攝時間為" + picture_date)

	        lightLED(9)
		
#Register----------------------------------------------
GPIO.add_event_detect(pinPIR, GPIO.RISING, callback=MOTION)
GPIO.add_event_detect(pinPIR2, GPIO.RISING, callback=motion_outdoor)
#GPIO.add_event_detect(pinBTN_Security, GPIO.FALLING, callback=btn_Security)

#Start--------------------------------------------------

try:
	strMode = "1"
	fo = open("finalStatus", "r+")
	strMode = fo.read()
	fo.close()
	logger.info("Status read from the file : " + strMode)
except:
	fo = open("finalStatus", "wb")
        fo.write(str(modeOperation))
        fo.close()

#回到上個按鈕模式，讓btn_Security()會自動切換到目前模式
if strMode=="1":
	modeOperation = 0
elif strMode=="2":
	modeOperation = 1
else:
	modeOperation = 2

btn_Security(pinBTN_Security)

try:
	while True:

		#print "PIR:" + str(GPIO.input(pinPIR))

		if GPIO.input(pinBTN_Security) == False:
			btn_Security(pinPIR)

		else:
			dt = list(time.localtime())
			nowYear = dt[0]
			nowMonth = dt[1]
			nowDay = dt[2]
			nowHour = dt[3]
			nowMinute = dt[4]

			if lastHourlySchedule==999:
				playWAV("wav/welcome/welcome1.wav") #您好，歡迎使用居家安全時鐘。按鈕 可切換居家或外出模式。
				lastHourlySchedule = nowHour

			if modeOperation == 2:

				if securityAuto_end<securityAuto_start:
					#看看有否在區間內
					if (nowHour>=securityAuto_start and nowHour<=23) or (nowHour>=0 and nowHour<securityAuto_end):
						autoSecutiryNow = 1
					else:
						autoSecutiryNow = 0
				else:
					if nowHour>=securityAuto_start and nowHour<securityAuto_end:
						autoSecutiryNow = 1
					else:
						autoSecutiryNow = 0

				#if autoChange == 1:
				#	if modeOperation == 0:
				#		btn_Security(1)
				#else:
				#	if modeOperation == 1:					
				#		btn_Security(0)


			#Environment information
			if (time.time()-ENV_lstchecktime)>ENV_checkPeriod:		
				statusPIR = GPIO.input(pinPIR)		
				adc = mcp3008.MCP3008()
				vLight = adc.read([mcp3008.CH1])
				lightDegree = vLight[0]

				vMQ4 = adc.read([mcp3008.CH2])
				adc.close()

				h,t = dht.read_retry(dht.DHT22, pinDHT22)

				statusContent = ""
				statusContent +=  '偵測時間：' + str(nowYear) + '/' + str(nowMonth) + '/' + str(nowDay) + ' ' + str(nowHour) + ':' + str(nowMinute)
				if modeOperation==1:
					statusContent +=  "\n\n 目前居家安全掛鐘處於[外出模式]"
				if modeOperation==2:
					statusContent +=  "\n\n 目前居家安全掛鐘處於[自動模式]"
				else:
					statusContent +=  "\n\n 目前居家安全掛鐘處於[居家模式]"


				if lastPIRfounded!="":
					statusContent +=  "\n 上次PIR偵測有人的時間：" + lastPIRfounded

				if vLight[0]<5:
					statusContent +=  "\n 客聽未開燈，為全暗的狀態，照度為：" + str(vLight[0])
				elif vLight[0]<15 and vLight[0]>=5:
					statusContent +=  "\n 客聽可能未開燈，相當的暗，照度為：" + str(vLight[0])
				elif vLight[0]<30 and vLight[0]>=15:
					statusContent +=  "\n 客聽稍暗，有些亮光，照度為：" + str(vLight[0])
				elif vLight[0]<50 and vLight[0]>=30:
                                        statusContent +=  "\n 客聽為正常亮度，照度為：" + str(vLight[0])
				elif vLight[0]>=50:
                                        statusContent +=  "\n 客聽很亮，照度為：" + str(vLight[0])

				if vMQ4[0]<120:
					statusContent +=  "\n 此外，空氣中煤氣指數為" + str(vMQ4[0]) + "，並沒有煤氣或瓦斯外洩的疑慮，請安心。"
				elif vMQ4[0]>=120 and vMQ4[0]<130:
					statusContent +=  "\n 此外請注意，空氣中煤氣指數為" + str(vMQ4[0]) + "，數值稍高，請注意煤氣或瓦斯是否有外洩可能。"
				elif vMQ4[0]>=130:
                                        statusContent +=  "\n 此外，請您特別注意，空氣中煤氣指數為" + str(vMQ4[0]) + "，數值偏高，請檢查煤氣或瓦斯是否有外洩。"


				if t != None:
					if t<20:
						statusContent +=  "\n 溫溼度方面，客聽的溫度目前為" + str(int(t)) + "度C，有點寒冷。"
					elif t<30 and t>=20:
						statusContent +=  "\n 溫溼度方面，客聽溫度目前為" + str(int(t)) + "度C，有些涼爽。"
					elif t<35 and t>=30:
		                                statusContent +=  "\n 溫溼度方面，客聽溫度目前為" + str(int(t)) + "度C，有些悶熱。"
					elif t>=35:
	                                        statusContent +=  "\n 溫溼度方面，要請您注意，客聽溫度很高，目前為" + str(int(t)) + "度C，請檢查火燭。"
				if h != None:
					if h<10:
						statusContent +=  "溼度是" + str(int(h)) + "%，客聽的空氣相當乾燥。"
					elif h<30 and h>=10:
						statusContent +=  "溼度是" + str(int(h)) + "%，客聽的空氣稍微乾燥。"
					elif h<65 and h>=30:
	                                        statusContent +=  "溼度是" + str(int(h)) + "%，客聽的溼度在理想狀態。"
					elif h<90 and h>=65:
	                                        statusContent +=  "溼度是" + str(int(h)) + "%，客聽的溼度偏高。"
					elif h>=90:
						statusContent +=  "溼度是" + str(int(h)) + "%，客聽的溼度相當高。"
			
				logger.info(statusContent)
				logger.info("-------------------------------------")
				ENV_lstchecktime = time.time()
			if modeOperation==0 or (autoSecutiryNow==0 and modeOperation==2):
				#異常警示
				if (t != None and h != None and t>40) and vMQ4[0]>120:
					EnvWarning(int(t), int(h),int(vMQ4[0]))
				else:		
					if nowHour>6 and nowHour<=23:
						if lastHourlySchedule!=nowHour:
							lastHourlySchedule = nowHour

							#靜心語
							#if nowHour==7 or nowHour==12 or nowHour==18 or nowHour==21:
							#	read_Sentence1()
							read_Sentence1()
										
							#整點報時					
							timeTell(nowHour, nowMinute)
							
							#室內溫度狀況告知					
							if t != None and h != None:
								alarmSensor(int(t), int(h), int(vLight[0]), int(vMQ4[0]) )
							
							#室外氣象
							if nowHour>6 or nowHour<19:
								try:
									read_Weather()
								except:
									print("Unexpected error:", sys.exc_info()[0])
							#if nowHour==7 or nowHour==12 or nowHour==18:
							#	playWAV("wav/news/n1.wav")	#下面為您播報重點新聞提要
							#	newsRead(NEWSREPORT_URL, NEWSREPORT_SPEAKER, 10)
				
				if time.time() - lastENV_takePicture_period > ENV_takePicture_period:
					takePicture("Home", "居家安全定時回報", statusContent)
					lastENV_takePicture_period = time.time()
	
			if modeOperation==1 or (autoSecutiryNow==1 and modeOperation==2):
				#logger.info("Enter modeOperation=1")
				#異常警示
				if (t != None and h != None and t>40) and vMQ4[0]>130:
					EnvWarning(int(t), int(h),int(vMQ4[0]))
				if (modeSecutirt_waittime - (time.time()-modeSecutiry_starttime))/60 < 0:
					#播放TV聲
					if lastPlayTV!=nowHour and (nowHour==8 or nowHour==17 or nowHour==22):
						logger.info("PLAY TV SOUND.")
						playTV()
						lastPlayTV = nowHour
				
					if time.time() - lastENV_takePicture_period > ENV_takePicture_period:
	                                        takePicture("Home", "居家安全定時回報", statusContent)
	                                        lastENV_takePicture_period = time.time()	
		
except:
	print("Unexpected error:", sys.exc_info()[0])
	logger.info("Unexpected error:", sys.exc_info()[0])
	#raise
