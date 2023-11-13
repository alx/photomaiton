#ifndef constants_h
#define constants_h

#include "Arduino.h"

// uncomment to activate debug with serial output.
#define DEBUG_MODE

// If it run on arduino mega
//#define MEGA

// Uncomment if communication with raspi is with usb link & json
#define JSON

// Coin multiplier
#define COIN_MULTI 10

//PINS

#define STRIP_PIN 9 // Chatoyance

#define LED_MATRIX_SDI_PIN 12 // SDI = DIN
#define LED_MATRIX_CS_PIN 11 // CS
#define LED_MATRIX_SCL_PIN 10 // SCL = CLOCK

#define COIN_PIN 3 // Add 10k/100k pull up resistor on pin to 5V.
#define COIN_SEGMENT_CLK_PIN 6
#define COIN_SEGMENT_DIO_PIN 5


#define COUNT_PIN 8 //Mechanical counter

#define SELECTOR_PIN 4 // To choose between normal mode & IA.

#ifdef MEGA
  #define AUX_PIN 46
  #define NUMERIC_PIN 47
  #define START_BTN_PIN 53
  #define CB_PIN 19
#else
  #define AUX_PIN 2
  #define START_BTN_PIN 7 //Previously 19 (change connector)
  #define CB_PIN 13
#endif

#define ROTSW1_PIN A1
#define ROTSW2_PIN A2
#define ROTSW3_PIN A3
#define ROTSW4_PIN A4

#define WAIT_BETWEEN_SHOT 5000 // Wait between shot in ms.

// Modes and prices
#define PRICE_CTS 400 // Price of a photo in cents.
#define FREE_PRICE_CTS 100 // Minimum in free price mode
#define MODE_PAYING 0
#define MODE_FREE_PRICE 1
#define MODE_FREE 2


// EEPROM data & work variables
#define EEPROM_ADRESS 0
struct storage {
  byte checkCode = 0;
  int totStrip = 0;
  byte mode = 0;// O = paying, 1 = Free price, 2 = Free
  float totMoney = 0;
  int price_cts = 400;
  int free_price_cts = 100;
  int tank_time = 18000;
  bool bRunning = false;
};

#endif
