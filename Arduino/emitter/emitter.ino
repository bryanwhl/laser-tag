#include <IRremote.h>
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#include <Fonts/FreeSans12pt7b.h>

#define SCREEN_WIDTH 128 // OLED display width, in pixels
#define SCREEN_HEIGHT 64 // OLED display height, in pixels
Adafruit_SSD1306 display(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
int bulletCount = 6;
int buttonState = 1;
const int IR_send_pin = 3;
const int button_pin = A2;
IRsend irsend(IR_send_pin);

void setup()
{
  Serial.begin(9600);
  pinMode(button_pin, INPUT_PULLUP);
  pinMode(13, OUTPUT);
  IrSender.begin(IR_send_pin);
  
  if(!display.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { // Address 0x3D for 128x64
    Serial.println(F("SSD1306 allocation failed"));
    for(;;);
  }
  display.clearDisplay();
  display.setFont(&FreeSans12pt7b);
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 10);
  display.println("Ready");
  display.display();
  delay(1000);
}

void loop() {
  
  buttonState = digitalRead(button_pin);
  
  // check if the pushbutton is pressed. If it is, the buttonState is LOW:
  if (buttonState == 0) {
    display.clearDisplay();
    display.setCursor(30,30);  
    display.println("Bang!");
    display.display();
    irsend.sendNEC(0x111111,32);
    //irsend.sendNEC(0x1111,0x22,true);
    digitalWrite(13, HIGH);
    bulletCount-=1;
    if (bulletCount <= 0){
      bulletCount = 6;
    }
    delay(500);
    display.clearDisplay();
    display.setCursor(30,30);  
    display.println(bulletCount);
    display.display(); 
    digitalWrite(13, LOW);
  } else {
  }

}