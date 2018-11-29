// This sketch is used to read load cells and provide instructions to stepper motors attached 
// to the same board.

#include <Wire.h>
#include <Adafruit_MotorShield.h>
#include <WheatstoneBridge.h>

// Set up strain gauge on ports 1, 2 and 3
// WheatstoneBridge(byte AnalogPin, int inputMin = 0, int inputMax = 1023, int outputMin = 0, int outputMax = 65535)
WheatstoneBridge wsb_strain1(A0, 365, 675, 0, 1000);
WheatstoneBridge wsb_strain2(A1, 365, 675, 0, 1000);
WheatstoneBridge wsb_strain3(A2, 365, 675, 0, 1000);

// Create the motor shield object with the default I2C address
Adafruit_MotorShield AFMS = Adafruit_MotorShield();

// Connect a stepper motor with 200 steps per revolution to 
// motor port #1 (M1 and M2)
Adafruit_StepperMotor *myMotor1 = AFMS.getStepper(64, 1);
Adafruit_StepperMotor *myMotor2 = AFMS.getStepper(64, 2);

void setup() {
  Serial.begin(9600);
  Serial.println("Ready");

  AFMS.begin(100); 
  myMotor1->setSpeed(10);
  myMotor2->setSpeed(15);
}


int load;

void loop() {
  char inBytes[10] = {0, 0, 0, 0, 0, 0, 0, 0, 0, 0};
  String mode = "";
  String choice = "";
  String dir = "";
  String steps = "";
  int steps_val;
  if (Serial.available()) { // wait for serial input
    delay(50);

    int size_t = Serial.readBytesUntil('\n', inBytes, sizeof(inBytes)-1);
    for (int i = 3; i < size_t; i++) {
      steps += (char)inBytes[i];
    }
    steps_val = steps.toInt();

    if (inBytes[0] == 'M') { //move motors 
      if (inBytes[1] == '1') {
        if (inBytes[2] == '+') {
          myMotor1->step(steps_val, FORWARD, DOUBLE);
          myMotor1->release();
        }
        if (inBytes[2] == '-') {
          myMotor1->step(steps_val, BACKWARD, DOUBLE);
          myMotor1->release();
        }
      }
        if (inBytes[1] == '2') {
          if (inBytes[2] == '+') {
            myMotor2->step(steps_val, FORWARD, DOUBLE);
            myMotor2->release();
          }
          if (inBytes[2] == '-') {
            myMotor2->step(steps_val, BACKWARD, DOUBLE);
            myMotor2->release();
          } 
        }
    }  

    if (inBytes[0] == 'r') { // read load cell
      if (inBytes[1] == '1') {
        load = wsb_strain1.measureForce();
        Serial.println(load, DEC);
      }
      if (inBytes[1] == '2') {
        load = wsb_strain2.measureForce();
        Serial.println(load, DEC);
      }
      if (inBytes[1] == '3') {
        load = wsb_strain3.measureForce();
        Serial.println(load, DEC);
      }
    }
  }
}
