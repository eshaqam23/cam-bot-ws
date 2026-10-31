#include "helpers.h"

char message[32];

void setLeftMotor(int pwm, int dir) {
  pwm = constrain(pwm, 0, 255);

  if (pwm == 0) {
    stopLeft();
    analogWrite(ENB, 0);
    return;
  }

  if (dir == 1) leftForward();
  else leftBackwards();

  analogWrite(ENB, pwm);
}

void setRightMotor(int pwm, int dir) {
  pwm = constrain(pwm, 0, 255);

  if (pwm == 0) {
    stopRight();
    analogWrite(ENA, 0);
    return;
  }

  if (dir == 1) rightForward();
  else rightBackwards();

  analogWrite(ENA, pwm);
}

void setup() {
  initPins();
  analogWrite(ENA, 0);
  analogWrite(ENB, 0);
  Serial.println("Ready");
}

void loop() {
  if (Serial.available()) {
    int bytesRead = Serial.readBytesUntil('\n', message, sizeof(message) - 1);
    message[bytesRead] = '\0';

    int leftPwm, leftDir, rightPwm, rightDir;

    if (sscanf(message, "%d,%d,%d,%d", &leftPwm, &leftDir, &rightPwm, &rightDir) == 4) {
      setLeftMotor(leftPwm, leftDir);
      setRightMotor(rightPwm, rightDir);
      Serial.println("OK");
    } else {
      Serial.println("ERR");
    }
  }
}

