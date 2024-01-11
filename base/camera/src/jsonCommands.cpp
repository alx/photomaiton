#include "jsonCommands.h"

StaticJsonDocument<400> jason;
int lastCommand = 0;

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
        //Serial.print("R=");
        int cmd = Serial.read() - '0';
        if(cmd >= 0){
            //Serial.println(cmd);
            lastCommand = cmd;
        }
        
    }
}

bool checkCmdStartShot(){
    if(lastCommand == 1){
        //lightOne(2);
        lastCommand = 0;
        return true;
    }
    return false;
}

bool checkCmdInitShot(){
    if(lastCommand == 2){
        //lightOne(2);
        lastCommand = 0;
        return true;
    }
    return false;
}

bool checkCmdCountdown(){
    if(lastCommand == 3){
        lastCommand = 0;
        return true;
    }
    return false;
}

bool checkCmdEndWait(){
    if(lastCommand == 4){
        lastCommand = 0;
        return true;
    }
    return false;
}

bool checkCmd(int cmd){
    if(lastCommand == cmd){
        lastCommand = 0;
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