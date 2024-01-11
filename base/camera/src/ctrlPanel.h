
#ifndef ctrlpanel_h
#define ctrlpanel_h

#include <TM1637Display.h>
#include <FastLED.h>
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
void lightOne(byte i, byte r, byte g, byte b);
void fastLedShow();
#endif
