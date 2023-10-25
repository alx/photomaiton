#include "jsonCommands.h"

StaticJsonDocument<200> jason;

void startShot(bool mode){
    jason.clear();
    jason["cmd"] = 1;
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