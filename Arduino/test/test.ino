#include <IRremote.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Fonts/FreeSans12pt7b.h>

#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 64 // OLED display height, in pixels
IRsend irsend(3);
int bulletCount = 6;
const int button_pin = 16;
//IR_SEND_PIN = 3;

void setup() {
  pinMode(A2, INPUT_PULLUP); 
  Serial.begin(9600);
}

int buttonStatus = 0;
void loop() {
  int pinValue = digitalRead(A2);
  delay(10); // quick and dirty debounce filter
  Serial.println(pinValue);
  
}