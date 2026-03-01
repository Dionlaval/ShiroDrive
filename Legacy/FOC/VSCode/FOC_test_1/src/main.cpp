#include <Arduino.h>
#include <Wire.h>
#include <SimpleFOC.h>

// Define motor + driver on pins 9,10,11,12
BLDCDriver3PWM driver = BLDCDriver3PWM(9, 10, 11, 12);
BLDCMotor motor = BLDCMotor(7);  // pole-pairs: adjust as per your motor

// AS5600 via I2C quick config
MagneticSensorI2C sensor = MagneticSensorI2C(AS5600_I2C);

void setup() {
  Serial.begin(115200);
  Wire.begin();
  
  driver.init();
  motor.linkDriver(&driver);

  sensor.init();
  motor.linkSensor(&sensor);

  motor.init();
  motor.initFOC();

  Serial.println("Setup done. Spinning...");
}

void loop() {
  // FOC control loop
  motor.loopFOC();

  // Rotate clockwise at 2 rad/s for 5 s
  Serial.println("⟳ CW");
  motor.move(2.0);
  float t0 = millis();
  while (millis() - t0 < 5000) {
    motor.loopFOC();
    delay(5);
  }

  // Then anticlockwise
  Serial.println("⟲ CCW");
  motor.move(-2.0);
  t0 = millis();
  while (millis() - t0 < 5000) {
    motor.loopFOC();
    delay(5);
  }
}
