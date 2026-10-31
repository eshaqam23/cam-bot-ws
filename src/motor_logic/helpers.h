// Adam Eshaq - 04/03/2026
// Header for helper functions

#ifndef HELPERS_H
#define HELPERS_H

#include <Arduino.h>

// --------- Left motor ---------- //
const int IN3 = 0;
const int IN4 = 2;
const int ENB = 25;

// --------- Right motor ---------- //
const int IN1 = 16;
const int IN2 = 4;
const int ENA = 26;

// ----------- Helper functions ---------- //
void initPins();

void leftForward();
void leftBackwards();
void stopLeft();
void rightForward();
void rightBackwards();
void stopRight();
void stall();

#endif