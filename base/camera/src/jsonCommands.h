#ifndef jsoncommands_h
#define jsoncommands_h

#include <ArduinoJson.h>
#include "constants.h"
#include "ctrlPanel.h"

void startShot();
bool checkCmdInitShot();
bool checkCmdStartShot();
bool checkCmdCountdown();
bool checkUpdate();
#endif