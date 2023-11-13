#include "jsonCommands.h"

StaticJsonDocument<500> jason;

void startShot(bool mode){
    jason.clear();
    jason["cmd"] = "startShot";
    jason["pay"] = 0;//0 =cash, 1=cb
    jason["ia"] = mode ? 0 : 1;//0 = normal, 1 = ia.
    JsonArray data = jason.createNestedArray("styl");

    data.add(readRotSwitch(ROTSW1_PIN));
    data.add(readRotSwitch(ROTSW2_PIN));
    data.add(readRotSwitch(ROTSW3_PIN));
    data.add(readRotSwitch(ROTSW4_PIN));
    //Serial.println(jason.overflowed());
    serializeJson(jason, Serial);
    Serial.println();
};

String checkAvailableCommand(){
    String cmd = "";
    if (Serial.available()) {
        char incomingData[200];  // json de 200 caractéres max
        int bytesRead = Serial.readBytesUntil('\n', incomingData, sizeof(incomingData));
        incomingData[bytesRead] = '\0'; 

        DeserializationError error = deserializeJson(jason, incomingData);

        if (!error) {
            cmd = jason["cmd"].as<String>();
        }
    }
    return cmd;
}

bool initShot(){
    return checkAvailableCommand() == "initShot";
}