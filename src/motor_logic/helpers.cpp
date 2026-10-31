// Implementation of helper functions

#include "helpers.h"

// ----------- Initialization ---------- //
void initPins() {
  pinMode(IN3, OUTPUT);
  pinMode(IN4, OUTPUT);
  pinMode(ENB, OUTPUT);

  pinMode(IN1, OUTPUT);
  pinMode(IN2, OUTPUT);
  pinMode(ENA, OUTPUT);

  analogWrite(ENA, 0);
  analogWrite(ENB, 0);

  Serial.begin(9600);
  delay(100);
}

// ----------- Individual Side ---------- //
void leftForward() {
  digitalWrite(IN3, HIGH);
  digitalWrite(IN4, LOW);
}

void leftBackwards() {
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, HIGH);
}

void stopLeft() {
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
}

void rightForward() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, HIGH);
}

void rightBackwards() {
  digitalWrite(IN1, HIGH);
  digitalWrite(IN2, LOW);
}

void stopRight() {
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
}

void stall()
{
  digitalWrite(IN1, LOW);
  digitalWrite(IN2, LOW);
  digitalWrite(IN3, LOW);
  digitalWrite(IN4, LOW);
  digitalWrite(ENA, LOW);
  digitalWrite(ENB, LOW);
}