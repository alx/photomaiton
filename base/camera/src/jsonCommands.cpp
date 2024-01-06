#include "jsonCommands.h"

StaticJsonDocument<600> jason;
String lastCommand = "";

void startShot(){
    bool mode = digitalRead(SELECTOR_PIN);
    jason.clear();
    jason["cmd"] = "startShot";
    jason["pay"] = 0;//0 =cash, 1=cb
    jason["mode"] = mode ? "std" : "ia";//0 = normal, 1 = ia.
    JsonArray data = jason.createNestedArray("styl");

    data.add(readRotSwitch(ROTSW1_PIN));
    data.add(readRotSwitch(ROTSW2_PIN));
    data.add(readRotSwitch(ROTSW3_PIN));
    data.add(readRotSwitch(ROTSW4_PIN));
    //Serial.println(jason.overflowed());
    serializeJson(jason, Serial);
    Serial.println();
};

void checkAvailableCommand(){
    if (Serial.available()) {
        char incomingData[200];  // json de 200 caractéres max
        int bytesRead = Serial.readBytesUntil('\n', incomingData, sizeof(incomingData));
        incomingData[bytesRead] = '\0'; 

        DeserializationError error = deserializeJson(jason, incomingData);

        if (!error) {
            lastCommand = jason["cmd"].as<String>();
        }
    }
}

bool checkCmdStartShot(){
    checkAvailableCommand();
    if(lastCommand == "startShot"){
        lastCommand = "";
        return true;
    }
    return false;
}

bool checkCmdInitShot(){
    checkAvailableCommand();
    if(lastCommand == "initShot"){
        lastCommand = "";
        return true;
    }
    return false;
}

bool checkCmdCountdown(){
    checkAvailableCommand();
    if(lastCommand == "countdown"){
        lastCommand = "";
        return true;
    }
    return false;
}

bool checkCmd(String cmd){
    checkAvailableCommand();
    if(lastCommand == cmd){
        lastCommand = "";
        return true;
    }
    return false;
}

void sendSerial(bool mode){
    jason.clear();
    jason["serial"] = "startShot";

    //Serial.println(jason.overflowed());
    serializeJson(jason, Serial);
    Serial.println();
};

bool checkUpdate(){
    /*checkAvailableCommand();
    if(lastCommand == "update"){
        lastCommand = "";
        Serial.println(String(jason["id"].as<String>()));
        Serial.println(String(jason["value"].as<String>()));
        return true;
    }*/
    return false;
}