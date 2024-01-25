/*
 * LCD lib : https://github.com/fdebrabander/Arduino-LiquidCrystal-I2C-library. Pin 20 SDA, 21 SCL. Adresse 0x27.
 * Fast Read\Write : https://github.com/mmarchetti/DirectIO
 * 4* 7 segment, TM1637 : https://github.com/avishorp/TM1637
 * LCD Matrix 8*8 : http://wayoda.github.io/LedControl/
 * RTC DS3231 (3.3v, SDA, SCL, empty, GND). Adress: 0x68
 */
 
//STACK_DECLARE
#include <Arduino.h>
#include <EEPROMex.h>
#include <EEPROMVar.h>
#include <MemoryUsage.h>
#include "constants.h"
#include "ctrlPanel.h"
#include "ledmatrix.h"
#include "jsonCommands.h"


// Work variables
storage parametres;

void auxOn() {
  #ifdef MEGA
    digitalWrite(AUX_PIN, HIGH);
  #else
    digitalWrite(AUX_PIN, LOW);
  #endif
}

void auxOff() {
  #ifdef MEGA
    digitalWrite(AUX_PIN, LOW);
  #else
    digitalWrite(AUX_PIN, HIGH);
  #endif
}


void setup() {

  Serial.begin(115200);
  Serial.println(F("Start"));

  //Aux light
  pinMode(AUX_PIN, OUTPUT);
  auxOff();

  pinMode(START_BTN_PIN, INPUT_PULLUP);

  // Mechanical counter
  pinMode(COUNT_PIN, OUTPUT);
  digitalWrite(COUNT_PIN, LOW);

  pinMode(SELECTOR_PIN, INPUT_PULLUP);

  initStrip();
  
  EEPROM.readBlock(EEPROM_ADRESS, parametres);
  
  // Check verif code, if not correct init eeprom.
  if(parametres.checkCode != 131){
    parametres.checkCode = 131;
    parametres.totMoney = 0;
    parametres.totStrip = 0;
    parametres.mode = MODE_PAYING;
    parametres.price_cts = 300;
    parametres.bRunning = false;
    EEPROM.writeBlock(EEPROM_ADRESS, parametres);
  }
  
  //parametres.price_cts = 400;
  //parametres.mode = MODE_PAYING;
  parametres.mode = MODE_FREE;
  EEPROM.updateBlock(EEPROM_ADRESS, parametres);
  
  disableCoinAcceptor();
  initLedMatrix();
  initCoinSegment();
  enableCoinAcceptor(parametres);
  showSmiley();
}

unsigned long lastRefresh = 0;
void loop() {
  //FREERAM_PRINT;

  #ifdef JSON
    checkAvailableCommand();

    unsigned long currMillis = millis();
    if(currMillis - lastRefresh > 200){
      refreshStrip();
      lastRefresh = currMillis;
    }
      
    //Check for updates from raspi.
    if(checkCmd(5)){ // set free mode
      parametres.mode = MODE_FREE;
      EEPROM.updateBlock(EEPROM_ADRESS, parametres);
      enableCoinAcceptor(parametres);
    }

    if(checkCmd(6)){ // set paying mode
      parametres.price_cts = 300;
      parametres.mode = MODE_PAYING;
      EEPROM.updateBlock(EEPROM_ADRESS, parametres);
      enableCoinAcceptor(parametres);
    }
  #endif

  // If coin acceptor OK and clic start button.
  if(manageCoinsAndStart(parametres)) {
    auxOn();
    #ifdef JSON
      byte pose1 = readRotSwitchByte(ROTSW1_PIN);
      byte pose2 = readRotSwitchByte(ROTSW2_PIN);
      byte pose3 = readRotSwitchByte(ROTSW3_PIN);
      byte pose4 = readRotSwitchByte(ROTSW4_PIN);
      startShot();
    #else
      digitalWrite(NUMERIC_PIN, HIGH); // start raspberry pi sequence
      delay(100);
      digitalWrite(NUMERIC_PIN, LOW);
    #endif

    bool bClassic = digitalRead(SELECTOR_PIN);

    for(byte i = 0; i < 4;i++){
      #ifdef JSON
        if(!bClassic){
          lightOne(112 - pose1, 255, 0, 0);
          lightOne(54 + pose2, 255, 0, 0);
          lightOne(126 - pose3, 255, 0, 0);
          lightOne(40 + pose4, 255, 0, 0);
          if(i == 0){
            lightOne(112 - pose1, 0, 255, 0);
          } else if(i == 1){
            lightOne(54 + pose2, 0, 255, 0);
          } else if(i == 2){
            lightOne(126 - pose3, 0, 255, 0);
          } else {
            lightOne(40 + pose4, 0, 255, 0);
          }
          fastLedShow();
        }

        unsigned long currMillis = millis();
        unsigned long timeout = currMillis;
        while(!checkCmdCountdown()){
          currMillis = millis();
          if(currMillis - timeout > 3000){
            // si pas de réponse aprés timeout 3sec, continue.
            break;
          }
          checkAvailableCommand();
        }
      #endif  
      showCountdown();
      while(getCountDown() > 0){
        refreshCountdown();
      }
      #ifndef JSON
        delay(1000);
      #endif
    }
    // 2 more sec before switching aux off.
    delay(2000);
    auxOff();
    //showCross();
    #ifdef JSON
      unsigned long currMillis = millis();
      unsigned long timeout = currMillis;
      unsigned long animRefresh = 0;
      while(!checkCmdEndWait()){
        currMillis = millis();
        if(currMillis - animRefresh > 200){
          animRefresh = currMillis;
          waitAnim();
        }
        if(currMillis - timeout > 180000){
          // si pas de réponse aprés timeout 3mn, continue.
          break;
        }
        checkAvailableCommand();
      }
    #endif
    showSmiley();
    enableCoinAcceptor(parametres);
    /*parametres.bRunning = false;
    EEPROM.updateBlock(EEPROM_ADRESS, parametres);*/
  }
}

