
#ifndef ctrlpanel_h
#define ctrlpanel_h

#include <DirectIO.h>
#include <TM1637Display.h>
#include <Adafruit_NeoPixel.h>
#include "constants.h"
#include "ledmatrix.h"
#include "jsonCommands.h"


boolean manageCoinsAndStart(struct storage parametres);
void setCoinDigit(int number);
void refreshCoinSegment(struct storage parametres);
void initCoinSegment();
void coinInterrupt();
void disableCoinAcceptor();
void enableCoinAcceptor(struct storage parametres);
void startLedOn();
void startLedOff(); 
boolean isCoinEnabled();
boolean isStartLedOn();
bool readSWStart();
void incrementCounter();
void errSegment();
const char* readRotSwitch(byte id);
byte readRotSwitchByte(byte id);
void initStrip();
void refreshStrip();
#endif
