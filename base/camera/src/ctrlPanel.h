
#ifndef ctrlpanel_h
#define ctrlpanel_h

#include <DirectIO.h>
#include <TM1637Display.h>
#include "constants.h"
#include "ledmatrix.h"


boolean manageCoinsAndStart(byte mode);
void setCoinDigit(int number);
void refreshCoinSegment(byte mode);
void initCoinSegment();
void coinInterrupt();
void disableCoinAcceptor();
void enableCoinAcceptor(byte mode);
void startLedOn();
void startLedOff(); 
boolean isCoinEnabled();
boolean isStartLedOn();
bool readSWStart();
void incrementCounter();
void errSegment();
byte readRotSwitch(byte id);
#endif
