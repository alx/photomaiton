
#ifndef ledmatrix_h
#define ledmatrix_h

#include <LedControl.h>
#include "constants.h"

// For LED Matrix (5, 4 ,3, 2, 1, smiley)
const byte IMAGES[][8] = {
{
  B00000000,
  B01100100,
  B01100010,
  B00000010,
  B00000010,
  B01100010,
  B01100100,
  B00000000
},{
  B00000000,
  B00000001,
  B00000001,
  B01111111,
  B01111111,
  B00010001,
  B00000001,
  B00000000
},{
  B00000000,
  B00110001,
  B01111001,
  B01001001,
  B01000101,
  B01100111,
  B00100011,
  B00000000
},{
  B00000000,
  B00110110,
  B01111111,
  B01001001,
  B01001001,
  B01100011,
  B00100010,
  B00000000
},{
  B00000000,
  B00000100,
  B01111111,
  B01111111,
  B00100100,
  B00010100,
  B00001100,
  B00000000
},{
  B00000000,
  B01001110,
  B01011111,
  B01010001,
  B01010001,
  B01110011,
  B01110010,
  B00000000
}};

const byte ARROWDOWN[8] = {
  B00001000,
  B00001100,
  B11111110,
  B11111111,
  B11111110,
  B00001100,
  B00001000,
  B00000000
};

const byte CROSS[8] = {
  B10000001,
  B01000010,
  B00100100,
  B00011000,
  B00011000,
  B00100100,
  B01000010,
  B10000001
};

const int IMAGES_LEN = sizeof(IMAGES)/8;

const uint64_t ANIM[] PROGMEM = {
  0x1c00000000002070,
  0x1c00000000400070,
  0x1c000000800000e0,
  0x38000040000000e0,
  0x38002000000000e0,
  0x70100000000000e0,
  0x7000080000000070,
  0x7000000400000070,
  0x7000000002000038,
  0x700000000001000e,
  0x7000000000000107,
  0x3800000000020007,
  0x3800000004000007,
  0x700000080000000e,
  0xe00010000000001c,
  0xe020000000000038,
  0xe000200000000038,
  0xe000002000000070,
  0x3800000020000070,
  0x3800000000200070
};
const int ANIM_LEN = sizeof(ANIM)/8;

void initLedMatrix();
void displayNumber(byte numero);
void showCountdown();
void refreshCountdown();
void showArrowDown();
void showSmiley();
void showCross();
void waitAnim();
void clearLedMatrix();
byte getCountDown();

#endif
