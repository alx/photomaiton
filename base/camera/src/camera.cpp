/*
 * LCD lib : https://github.com/fdebrabander/Arduino-LiquidCrystal-I2C-library. Pin 20 SDA, 21 SCL. Adresse 0x27.
 * Fast Read\Write : https://github.com/mmarchetti/DirectIO
 * 4* 7 segment, TM1637 : https://github.com/avishorp/TM1637
 * LCD Matrix 8*8 : http://wayoda.github.io/LedControl/
 * RTC DS3231 (3.3v, SDA, SCL, empty, GND). Adress: 0x68
 */
 
//#include <MemoryUsage.h>
//STACK_DECLARE
#include <Arduino.h>
#include <DirectIO.h>
#include <EEPROMex.h>
#include <EEPROMVar.h>
#include <Adafruit_NeoPixel.h>
#include "constants.h"
#include "ctrlPanel.h"
#include "ledmatrix.h"
#include "jsonCommands.h"


// Work variables
storage parametres;
bool bClassic = false; // Classic or IA.
//Aux light
Output<AUX_PIN> aux;
Adafruit_NeoPixel strip = Adafruit_NeoPixel(40, STRIP_PIN, NEO_GRB + NEO_KHZ800);

void auxOn() {
  //#ifdef MEGA
    aux.write(HIGH);
  //#else
    //aux.write(LOW);
  //#endif
}

void auxOff() {
  //#ifdef MEGA
    aux.write(LOW);
  //#else
    //////////////////////aux.write(HIGH);
  //#endif
}


void setup() {

  Serial.begin(9600);
  Serial.println(F("Start"));

  // Mechanical counter
  pinMode(COUNT_PIN, OUTPUT);
  digitalWrite(COUNT_PIN, LOW);

  pinMode(SELECTOR_PIN, INPUT_PULLUP);
  bClassic = digitalRead(SELECTOR_PIN);

  //Init strip
  strip.begin();
  strip.setBrightness(100);
  for(byte i=0; i<strip.numPixels(); i++) {
    strip.setPixelColor(i, !bClassic ? 255 : 0, 0, bClassic ? 255 : 0);
  }
  strip.show();
  
  EEPROM.readBlock(EEPROM_ADRESS, parametres);
  
  // Check verif code, if not correct init eeprom.
  if(parametres.checkCode != 131){
    parametres.checkCode = 131;
    parametres.totMoney = 0;
    parametres.totStrip = 0;
    parametres.mode = MODE_PAYING;
    parametres.price_cts = 300;
    parametres.free_price_cts = 100;
    parametres.bRunning = false;
    EEPROM.writeBlock(EEPROM_ADRESS, parametres);
  }
  
  //parametres.price_cts = 300;
  //parametres.mode = MODE_PAYING;
  parametres.mode = MODE_FREE;
  auxOff();
  disableCoinAcceptor();
  initCoinSegment();
  initLedMatrix();
  enableCoinAcceptor(parametres.mode);
  showSmiley();
}

void loop() {
  // Blue or red pill
  if(bClassic != digitalRead(SELECTOR_PIN)){
    bClassic = !bClassic;
    for(byte i=0; i<strip.numPixels(); i++) {
      strip.setPixelColor(i, !bClassic ? 255 : 0, 0, bClassic ? 255 : 0);
    }
    strip.show();
  }

  // If coin acceptor OK and clic start button.
  if(manageCoinsAndStart(parametres.mode)) {
    auxOn();
    /*parametres.totStrip += 1;
    parametres.bRunning = true;
    EEPROM.updateBlock(EEPROM_ADRESS, parametres);*/
    #ifdef JSON
      startShot(bClassic);
    #else
      digitalWrite(NUMERIC_PIN, HIGH); // start raspberry pi sequence
      delay(100);
      digitalWrite(NUMERIC_PIN, LOW);
    #endif

    for(byte i = 0; i < 4;i++){
      #ifdef JSON
        unsigned long currMillis = millis();
        unsigned long timeout = currMillis;
        while(!checkCmdCountdown()){
          currMillis = millis();
          if(currMillis - timeout > 3000){
            // si pas de réponse aprés timeout 3sec, continue.
            break;
          }
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
    showSmiley();
    enableCoinAcceptor(parametres.mode);
    /*parametres.bRunning = false;
    EEPROM.updateBlock(EEPROM_ADRESS, parametres);*/
  }
}

