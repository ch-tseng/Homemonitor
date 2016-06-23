<?php
$words = $argv[1];
$speaker = $argv[2];  
$volume = (int)$argv[3];  //其音量大小可調整範圍為0~100，預設值為100
$speed = (int)$argv[4];  //其語音速度可調整範圍為-10~10，預設值為0
$pitchLevel = (int)$argv[5];  //韻律調整：值越大則音高越高；反之則音高越低，可調整範圍-10~10，預設值為0
$pitchSign = (int)$argv[6];  //韻律調整：0=正常、1=像機器人、2=像外國人說中文，預設值為0
$pitchScale = (int)$argv[7];  //韻律調整：值越大則抑揚頓挫越明顯；反之則越趨平版，可調整範圍0~20，預設值為5

//echo "test: $words , $speaker , $volume , $speed , $pitchLevel , $pitchSign , $pitchScale";

//Setup Web Service
$client = new SoapClient("http://tts.itri.org.tw/TTSService/Soap_1_3.php?wsdl");
// Invoke Call to ConvertText
//$result=$client->ConvertText("chtseng","e020770","現在室內氣溫是二十八度","Angela",100, -5, "wav",-7,0,5);
$result=$client->ConvertText("chtseng","e020770", $words, $speaker, $volume, $speed, "wav", $pitchLevel, $pitchSign, $pitchScale);
// Iterate through the returned string array
$resultArray= explode("&",$result);
list($resultCode, $resultString, $resultConvertID) = $resultArray;
echo "{ ";
if(isset($resultConvertID)){
	echo "\"resultCode\":\"".$resultCode."\"";
	echo ", \"resultString\":\"".$resultString."\"";
	echo ", \"resultConvertID\":\"".$resultConvertID."\"";
}else{
	echo "\"resultCode\":\"0\"";
        echo ", \"resultString\":\"0\"";
        echo ", \"resultConvertID\":\"0\"";
}
echo " }";
?>
