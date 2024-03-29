#include "ledmatrix.h"

// LED Matrix
LedControl ledMatrix = LedControl(LED_MATRIX_SDI_PIN, LED_MATRIX_SCL_PIN, LED_MATRIX_CS_PIN, 1); 
unsigned long prevousMillisCountdown = 0;
byte countDown = 5;


/********************************
 *  LED MATRIX FOR COUNTDOWN
 ********************************/
void initLedMatrix(){
  ledMatrix.shutdown(0,false);  // Wake up displays
  ledMatrix.setIntensity(0,1);  // Set intensity levels at the minimum
  ledMatrix.clearDisplay(0);  // Clear Displays
}

void displayNumber(byte numero)
{
  for (int i = 0; i < 8; i++)  
  {
    ledMatrix.setRow(0,i,IMAGES[numero][i]);
  }
}

void showCountdown()
{
  countDown = 5;
  displayNumber(countDown);
  prevousMillisCountdown = millis();
}

void refreshCountdown()
{
  unsigned long currentMillis = millis();
  if(currentMillis - prevousMillisCountdown >= 1000){
    prevousMillisCountdown = currentMillis;
    countDown = countDown > 0 ? countDown-1 : 0;
    displayNumber(countDown);
  }
}

void showArrowDown()
{
  for (int i = 0; i < 8; i++)  
  {
    ledMatrix.setRow(0,i,ARROWDOWN[i]);
  }
}

void clearLedMatrix(){
  ledMatrix.clearDisplay(0);
}

byte getCountDown(){
  return countDown;
}

void showSmiley()
{
  for (int i = 0; i < 8; i++)  
  {
    ledMatrix.setRow(0,i,IMAGES[0][i]);
  }
}

void showCross()
{
  for (int i = 0; i < 8; i++)  
  {
    ledMatrix.setRow(0,i,CROSS[i]);
  }
}

void displayImage(uint64_t image) {
  for (int i = 0; i < 8; i++) {
    byte row = (image >> i * 8) & 0xFF;
    for (int j = 0; j < 8; j++) {
      ledMatrix.setLed(0, i, j, bitRead(row, j));
    }
  }
}
int frame = 0;
void waitAnim(){
   uint64_t image;
  memcpy_P(&image, &ANIM[frame], 8);

  displayImage(image);
  if (++frame >= ANIM_LEN ) {
    frame = 0;
  }
}