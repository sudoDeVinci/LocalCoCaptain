#include <Arduino.h>
#include "audio.h"

// Pin definitions
#define BUFFER_SIZE 16000 * 10  // 5 seconds at 16kHz
#define SAMPLE_RATE 16000      // 16kHz sample rate
#define ANALOG_PIN 9           // ADC input pin for MAX9814 microphone
#define BUTTON_PIN 5           // Button pin (change as needed)

// Global file system pointer
fs::FS* fileSystem = nullptr;

// Button and recording state
volatile bool buttonPressed = false;
bool isRecording = false;
unsigned long lastSampleTime = 0;
unsigned long sampleInterval_us = 1000000 / SAMPLE_RATE; // microseconds between samples

// Audio objects
WAVFile wavFile;
int recordingNumber = 0;

// Interrupt handler for button press/release
void IRAM_ATTR buttonISR() {
  // Read button state (LOW when pressed if using pull-up)
  buttonPressed = !digitalRead(BUTTON_PIN);
}

void setup() {
  // Initialize serial communication
  Serial.begin(115200);
  Serial.println("Hello, ESP32-S3!");
  
  // Configure button pin with internal pull-up and interrupt
  pinMode(BUTTON_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(BUTTON_PIN), buttonISR, CHANGE);
  
  // Configure ADC
  pinMode(ANALOG_PIN, INPUT);
  
  // Initialize filesystem using the utility function
  fileSystem = DetermineFileSystem();
  if (!fileSystem) {
    Serial.println("Failed to mount any filesystem");
  }
  
  // Initialize WAV file
  wavFile.setSampleRate(SAMPLE_RATE);
}

void loop() {
  // Check if button state changed
  if (buttonPressed && !isRecording) {
    // Start recording
    startRecording();
    isRecording = true;
  }
  else if (!buttonPressed && isRecording) {
    // Stop recording
    stopRecording();
    isRecording = false;
  }
  
  // Handle recording
  if (isRecording) {
    unsigned long currentTime = micros();
    if (currentTime - lastSampleTime >= sampleInterval_us) {
      // Take a sample
      if (wavFile.waveForm.size < BUFFER_SIZE) {
        // Read from ADC and store in buffer
        uint16_t sample = analogRead(ANALOG_PIN);
        wavFile.waveForm.data[wavFile.waveForm.size++] = sample;
      } else {
        // If we've reached max buffer size, stop recording
        debugln("Buffer full");
        stopRecording();
        isRecording = false;
      }
      lastSampleTime = currentTime;
    }
  }
}

void startRecording() {
  debugln("Starting recording...");
  
  // Allocate buffer for recording
  if (!wavFile.allocateBuffer(BUFFER_SIZE)) {
    debugln("Failed to allocate memory for recording");
    isRecording = false;
    return;
  }
  
  // Reset sample index and timestamp
  wavFile.waveForm.size = 0;
  lastSampleTime = micros();
}

void stopRecording() {
  debugf("Recording stopped with %d samples\n", wavFile.waveForm.size);
  
  // Save recording if we have samples and a valid filesystem
  if (fileSystem && wavFile.waveForm.size > 0) {
    // Get current timestamp
    time_t now;
    time(&now);
    tm* timeinfo = localtime(&now);
    char* timestamp = formattime(timeinfo);
    
    // Create filename with timestamp
    String filename = "/rec_" + String(recordingNumber++) + "_" + String(timestamp) + ".wav";
    delete[] timestamp; // Free allocated memory
    
    debugf("Saving recording to %s\n", filename.c_str());
    wavFile.write(*fileSystem, filename);
  } else {
    debugln("Could not save recording (no filesystem or empty buffer)");
  }
  
  // Free the buffer
  wavFile.freeBuffer();
}