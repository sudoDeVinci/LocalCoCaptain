#include <Arduino.h>
#include "io.h"

FS* fileSystem;

#define BUFFER_SIZE 512
#define SAMPLE_RATE 16000
#define ANALOG_PIN 9 

void setup() {
  // put your setup code here, to run once:
  Serial.begin(115200);
  Serial.println("Hello, ESP32-S3!");
}

void loop() {
  // put your main code here, to run repeatedly:
  uint16_t freq = analogRead(ANALOG_PIN);
  Serial.println(freq);
  delay(25);
}
