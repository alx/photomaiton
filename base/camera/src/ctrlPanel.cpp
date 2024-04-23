#include "ctrlPanel.h"


volatile int cents = 0;
int PRICE_CTS = 0;

const uint8_t SEG_FREE[] = {
  SEG_A | SEG_F | SEG_G | SEG_E,                   // F
  SEG_G | SEG_E,                                   // R
  SEG_A | SEG_F | SEG_G | SEG_E | SEG_D,           // E
  SEG_A | SEG_F | SEG_G | SEG_E | SEG_D,           // E
  };

const uint8_t SEG_BUSY[] = {
  SEG_F | SEG_G | SEG_C | SEG_D | SEG_E,           // B
  SEG_F | SEG_E | SEG_D | SEG_C | SEG_B,           // U
  SEG_A | SEG_F | SEG_G | SEG_C | SEG_D,           // S
  SEG_F | SEG_G | SEG_B | SEG_C,                   // Y
  };

const uint8_t SEG_ERR1[] = {
  SEG_F | SEG_G | SEG_A | SEG_D | SEG_E,           // E
  SEG_F | SEG_A | SEG_E | SEG_G | SEG_C | SEG_B,   // R
  SEG_F | SEG_A | SEG_E | SEG_G | SEG_C | SEG_B,   // R
  SEG_B | SEG_C,                                   // 1
  };

TM1637Display coinSegment(COIN_SEGMENT_CLK_PIN, COIN_SEGMENT_DIO_PIN);

bool bCoinEnabled = false;
unsigned long currentMillis;
unsigned long lastInterrupt = 0;
bool bRefreshSeg = true;
volatile bool bCarteOK = false;
unsigned long startInterruptCB = 0;

CRGB strip[169];
bool bClassic = digitalRead(SELECTOR_PIN);

boolean manageCoinsAndStart(struct storage parametres){
  
  boolean bStart = false;
  PRICE_CTS = parametres.price_cts;

  // Check millis of board that manage credit card reader
  if(bCarteOK){
    startInterruptCB = millis();
    
    while(digitalRead(CB_PIN) == true){
    }

    unsigned long stopInterruptCB = millis();
    if(stopInterruptCB - startInterruptCB < 50){
      bCarteOK = false;
    }else{
      cents = parametres.price_cts;
    }
  }

  // Gestion paiement ok depuis raspi
  if(checkCmdInitShot()){
    cents = parametres.price_cts;
  }
  if(parametres.mode == MODE_FREE){
    cents = parametres.price_cts;
  }

  if(cents >= parametres.price_cts){
    if(parametres.mode == MODE_PAYING){
      disableCoinAcceptor();
      setCoinDigit(0);
    }
    showArrowDown();
    bStart = !digitalRead(START_BTN_PIN);
  }

  currentMillis = millis();
  refreshCoinSegment(parametres);

  // Gestion lancement séquence depuis raspi
  if(checkCmdStartShot()){
    cents = parametres.price_cts;
    bStart = true;
  }

  if(bStart){
    disableCoinAcceptor();
    coinSegment.setSegments(SEG_BUSY);
    incrementCounter();
    cents = 0;
  }

  
  return bStart;
}

/*
 * Display digits on 4 * 7 segments display.
 * We assume number are factor of 50 (min coin = 50cts) like (0.50, 1, 1.5).
 * and dot sign always at the second position (like 0.50 or 2.50).
 * First digit from left is always off.
 * Last digit is always 0.
 */
void setCoinDigit(int number){
  uint8_t data[] = {0x0, 0x0, 0x0, 0b00111111}; 
  if(number < 100){
    data[1] = coinSegment.encodeDigit(0) + 0b10000000;//0.
    data[2] = coinSegment.encodeDigit(number / 10);
  } else if(number >= 100 && number < 1000){
    data[1] = coinSegment.encodeDigit(number / 100) + 0b10000000;
    data[2] = coinSegment.encodeDigit((number / 10) % 10);
  }
  coinSegment.setSegments(data);
  
}



/*
 * Refresh if needed according to cents the segment.
 */
void refreshCoinSegment(struct storage parametres){

  //N'affiche que la précision à 0.5
  if(currentMillis - lastInterrupt  > 200){
    if(parametres.mode == MODE_PAYING){
      setCoinDigit(parametres.price_cts - cents);
    } else {
      coinSegment.setSegments(SEG_FREE);
    }
  }
}

/*
 * Init coin segment.
 * Brigthness is from 1 to 7.
 */
void initCoinSegment(){
  uint8_t data[] = { 0x0, 0x0, 0x0, 0x0 };
  coinSegment.setBrightness(1); // min brightness (max 7)
  coinSegment.setSegments(data);  // All segments off
}

/*
 *  COIN ACCEPTOR
 */
 
// Interrupt main loop each time a pulse from coin acceptor is coming.
// 1 pulse = 50cts, 2 = 1eur, 4 = 2eur
void coinInterrupt(){
  //unsigned long currentMillis = millis();
  // Check the duration from previous pulse. Avoid pulse from static electricity.
  //unsigned long difference = currentMillis - oldInterruptMillis;
  lastInterrupt = millis();
  //if(difference < 135 && difference >125){
    cents += bCoinEnabled ? COIN_MULTI : 0;
  //}
  if(cents > PRICE_CTS){
    cents = PRICE_CTS;
  }
}

// Only one pulse from cashless device when payment is ok.
void CBInterrupt(){
  //cents = PRICE_CTS;
  bRefreshSeg = true;
  bCarteOK = true;
}

void disableCoinAcceptor(){
  detachInterrupt(digitalPinToInterrupt(COIN_PIN));
  detachInterrupt(digitalPinToInterrupt(CB_PIN));
  //setCoinDigit(0);
  bCoinEnabled = false;
  //cents = 0;
  bRefreshSeg = true;
}

void enableCoinAcceptor(struct storage parametres){
  if(parametres.mode != MODE_FREE){
    pinMode(COIN_PIN, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(COIN_PIN), coinInterrupt, FALLING);
    pinMode(CB_PIN, INPUT);
    attachInterrupt(digitalPinToInterrupt(CB_PIN), CBInterrupt, RISING);
    bCoinEnabled = true;
    cents = 0;
  }
  bRefreshSeg = true;
  refreshCoinSegment(parametres);
}

boolean isCoinEnabled(){
  return bCoinEnabled;
}

bool readSWStart(){
  return digitalRead(START_BTN_PIN);
}

void incrementCounter(){
  digitalWrite(COUNT_PIN, HIGH);
  delay(50);
  digitalWrite(COUNT_PIN, LOW);
}

void errSegment(){
  coinSegment.setSegments(SEG_ERR1);
}

const char* readRotSwitch(byte pin){
  int read = (analogRead(pin) + analogRead(pin) + analogRead(pin) + analogRead(pin)) / 4;
  
  if(read < 205){return "A";}
  else if(read >=205 && read <300){return "B";}
  else if(read >=300 && read <400){return "C";}
  else if(read >=400 && read <490){return "D";}
  else if(read >=490 && read <630){return "E";}
  else if(read >=630 && read <730){return "F";}
  else if(read >=730 && read <800){return "G";}
  else if(read >=800 && read <890){return "H";}
  else if(read >=890 && read <970){return "I";}
  else if(read >=970 && read <1008){return "J";}
  else if(read >=1008){return "K";}
  return "A";
}

byte readRotSwitchByte(byte pin){
  int read = (analogRead(pin) + analogRead(pin) + analogRead(pin) + analogRead(pin)) / 4;
  //Serial.println(read);

  if(read < 205){return 0;}
  else if(read >=205 && read <300){return 1;}
  else if(read >=300 && read <400){return 2;}
  else if(read >=400 && read <490){return 3;}
  else if(read >=490 && read <630){return 4;}
  else if(read >=630 && read <730){return 5;}
  else if(read >=730 && read <800){return 6;}
  else if(read >=800 && read <890){return 7;}
  else if(read >=890 && read <970){return 8;}
  else if(read >=970 && read <1008){return 9;}
  else if(read >=1008){return 10;}

  return 0;
}

void initStrip(){
  FastLED.addLeds<NEOPIXEL, STRIP_PIN>(strip, NB_LEDS);    

  for(byte i = 0; i < NB_LEDS; i++) {
    strip[i] = CRGB( !bClassic ? 255 : 0, 0, bClassic ? 255 : 0);
  }
  FastLED.show(); 
}

void refreshStrip(){

  for(byte i = 40; i <169;i++){
    strip[i] = CRGB(255, 255, 255);
  }

    // Blue or red pill
  //if(bClassic != digitalRead(SELECTOR_PIN)){
    bClassic = digitalRead(SELECTOR_PIN);
    for(byte i=0; i<40; i++) {
      strip[i] = CRGB( !bClassic ? 255 : 0, 0, bClassic ? 255 : 0);
    }

    for(byte i=65; i<102; i++) {
      strip[i] = CRGB( !bClassic ? 255 : 0, 0, bClassic ? 255 : 0);
    }
    for(byte i=51; i<54; i++) {
      strip[i] = CRGB( !bClassic ? 255 : 0, 0, bClassic ? 255 : 0);
    }
    for(byte i=113; i<116; i++) {
      strip[i] = CRGB( !bClassic ? 255 : 0, 0, bClassic ? 255 : 0);
    }
  //}

  // Refresh infos panel
  byte pose1 = readRotSwitchByte(ROTSW1_PIN);
  byte pose2 = readRotSwitchByte(ROTSW2_PIN);
  byte pose3 = readRotSwitchByte(ROTSW3_PIN);
  byte pose4 = readRotSwitchByte(ROTSW4_PIN);
  
  if(!bClassic){
    // Pose 4
    strip[40 + pose4] = CRGB(255, 0, 0);

    // Pose 2
    strip[54 + pose2] = CRGB(255, 0, 0);

    // Pose 1
    strip[112 - pose1] = CRGB(255, 0, 0);

    // Pose 3
    strip[126 - pose3] = CRGB(255, 0, 0);
  }
  
  
  FastLED.show(); 
}

void lightOne(byte i, byte r, byte g, byte b){
  strip[i] = CRGB(r, g, b);
}

void fastLedShow(){
  FastLED.show();
}