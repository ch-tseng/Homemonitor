<?php

function errorHandle($errno, $errstr) {
	echo "<b>Error:</b> [$errno] $errstr";
}

set_error_handler("errorHandle");

$id = (int)$argv[1];

//Setup Web Service
$client = new SoapClient("http://tts.itri.org.tw/TTSService/Soap_1_3.php?wsdl");
// Invoke Call to ConvertText
$result=$client->GetConvertStatus("chtseng","e020770", $id);
// Iterate through the returned string array
$resultArray= explode("&",$result);
if(isset($resultArray[4])) {
	list($resultCode, $resultString, $statusCode, $status, $resultUrl) = $resultArray;
	echo "{ ";
	echo "\"resultCode\": \"".$resultCode."\"";
	echo ", \"resultString\": \"".$resultString."\"";
	echo ", \"statusCode\": \"".$statusCode."\"";
	echo ", \"status\": \"".$status."\"";
	echo ", \"resultUrl\": \"".$resultUrl."\"";
	echo " }";
}else{
        echo "{ ";
        echo "\"resultCode\": \"0\"";
        echo ", \"resultString\": \"0\"";
        echo ", \"statusCode\": \"0\"";
        echo ", \"status\": \"0\"";
        echo ", \"resultUrl\": \"0\"";
        echo " }";
}
?>
