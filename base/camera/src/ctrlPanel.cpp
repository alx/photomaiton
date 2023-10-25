#include "ctrlPanel.h"


volatile int cents = 0;

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

// btn Start + LED
Input<START_BTN_PIN> startBtn(true);
bool bCoinEnabled = false;
unsigned long currentMillis;
unsigned long lastInterrupt = 0;
bool bRefreshSeg = true;
volatile bool bCarteOK = false;

unsigned long startInterruptCB = 0;

boolean manageCoinsAndStart(byte mode){
  boolean bStart = false;

  // Check millis of board that manage credit card reader
  if(bCarteOK == true && cents == 0){
    startInterruptCB = millis();
    bCarteOK = false;

    while(digitalRead(CB_PIN) == true){
      
    }

    unsigned long stopInterruptCB = millis();
    if(stopInterruptCB - startInterruptCB < 50){
      cents = 0;
    }else{
      cents = PRICE_CTS;
    }
    if(stopInterruptCB - startInterruptCB > 50){
      Serial.print(F("CB interrupt"));
      Serial.println(stopInterruptCB - startInterruptCB);
      Serial.print(F("cents="));
      Serial.println(cents);
    }
  }else{
    bCarteOK = false;
  }
  
  
  switch(mode){
    case MODE_PAYING:
      //if(cents >= PRICE_CTS || bCarteOK){
      if(cents >= PRICE_CTS){
        disableCoinAcceptor();
        showArrowDown();
        setCoinDigit(0);
        bStart = !startBtn.read();
      }
      break;
    case MODE_FREE_PRICE:
      if(cents >= FREE_PRICE_CTS){
        showArrowDown();
        bStart = !startBtn.read();
      }
      break;
    case MODE_FREE:
      showArrowDown();
      bStart = !startBtn.read();
      break;
  }

  currentMillis = millis();
  refreshCoinSegment(mode);
  if(bStart){
    disableCoinAcceptor();
    coinSegment.setSegments(SEG_BUSY);
    incrementCounter();
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
void refreshCoinSegment(byte mode){

  //N'affiche que la précision à 0.5
  if(currentMillis - lastInterrupt  > 200){
    if(mode == MODE_PAYING){
      setCoinDigit(PRICE_CTS - cents);
    } else if (mode == MODE_FREE_PRICE){
      setCoinDigit(cents);
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
    cents += bCoinEnabled ? 50 : 0;
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

void enableCoinAcceptor(byte mode){
  if(mode != MODE_FREE){
    pinMode(COIN_PIN, INPUT_PULLUP);
    attachInterrupt(digitalPinToInterrupt(COIN_PIN), coinInterrupt, FALLING);
    pinMode(CB_PIN, INPUT);
    attachInterrupt(digitalPinToInterrupt(CB_PIN), CBInterrupt, RISING);
    bCoinEnabled = true;
    cents = 0;
  }
  bRefreshSeg = true;
  refreshCoinSegment(mode);
}

boolean isCoinEnabled(){
  return bCoinEnabled;
}

bool readSWStart(){
  return startBtn.read();
}

void incrementCounter(){
  digitalWrite(COUNT_PIN, HIGH);
  delay(50);
  digitalWrite(COUNT_PIN, LOW);
}

void errSegment(){
  coinSegment.setSegments(SEG_ERR1);
}

byte readRotSwitch(byte pin){
  int read = (analogRead(pin) + analogRead(pin) + analogRead(pin) + analogRead(pin)) / 4;
  
  byte num;
  if(read < 200){num = 0;}
  else if(read >=200 && read <300){num = 1;}
  else if(read >=300 && read <400){num = 2;}
  else if(read >=400 && read <490){num = 3;}
  else if(read >=490 && read <630){num = 4;}
  else if(read >=630 && read <730){num = 5;}
  else if(read >=730 && read <800){num = 6;}
  else if(read >=800 && read <890){num = 7;}
  else if(read >=890 && read <970){num = 8;}
  else if(read >=970 && read <1008){num = 9;}
  else if(read >=1008){num = 10;}

  return num;

}
