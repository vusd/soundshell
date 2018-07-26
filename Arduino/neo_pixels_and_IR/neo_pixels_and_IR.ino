#include <Adafruit_NeoPixel.h>
#ifdef __AVR__
#include <avr/power.h>
#endif

#define PIN 3

int current_color = 0;
int dir = 1;
long last_color_change = millis();
long change_delay = 1000;
long ir_delay = 150;
long last_ir_polling = millis();
int ir_readings[] = {0, 0};
int ir_pins[] = {0, 1};
int prox_pin = 2;
int prox_reading = 0;
int last_prox_reading = 0;

int trig_pin = 13;
int echo_pin = 12;
float us_distance = 0.0; // the distance reading from the ultrasonic

// Parameter 1 = number of pixels in strip
// Parameter 2 = Arduino pin number (most are valid)
// Parameter 3 = pixel type flags, add together as needed:
//   NEO_KHZ800  800 KHz bitstream (most NeoPixel products w/WS2812 LEDs)
//   NEO_KHZ400  400 KHz (classic 'v1' (not v2) FLORA pixels, WS2811 drivers)
//   NEO_GRB     Pixels are wired for GRB bitstream (most NeoPixel products)
//   NEO_RGB     Pixels are wired for RGB bitstream (v1 FLORA pixels, not v2)
//   NEO_RGBW    Pixels are wired for RGBW bitstream (NeoPixel RGBW products)
Adafruit_NeoPixel strip = Adafruit_NeoPixel(46, PIN, NEO_GRB + NEO_KHZ800);

// IMPORTANT: To reduce NeoPixel burnout risk, add 1000 uF capacitor across
// pixel power leads, add 300 - 500 Ohm resistor on first pixel's data input
// and minimize distance between Arduino and first pixel.  Avoid connecting
// on a live circuit...if you must, connect GND first.

void setup() {
  pinMode(trig_pin, OUTPUT);
  pinMode(echo_pin, INPUT);
  pinMode(ir_pins[0], INPUT);
  pinMode(ir_pins[1], INPUT);
  Serial.begin(57600);
  strip.begin();
  strip.show(); // Initialize all pixels to 'off'
  strip.setBrightness(50);
}


int readUltrasonicDistance() {
  /*
    This function deals with all of the logic needed to read the ultrasonic rangefinder
    It will return an integer which corresponds to the distance of the closest object to the rangefinder
    in cm. The output will be constrained from 1 to 100.
  */
  // Clears the trigPin
  digitalWrite(trig_pin, LOW);
  delayMicroseconds(2);

  // Sets the trigPin on HIGH state for 10 micro seconds
  digitalWrite(trig_pin, HIGH);
  delayMicroseconds(10);
  digitalWrite(trig_pin, LOW);

  // Reads the echoPin, returns the sound wave travel time in microseconds
  // Calculating the distance in cm
  float us_reading = pulseIn(echo_pin, HIGH) * 0.017;
  // constrain ensures that extreme values are filtered out.
  return us_reading;
}

// Fill the dots one after the other with a color
void colorWipe(uint32_t c, uint8_t wait) {
  for (uint16_t i = 0; i < strip.numPixels(); i++) {
    strip.setPixelColor(i, c);
    strip.show();
    delay(wait);
  }
}

void setColorForStrip(int color) {
  for (int i = 0; i < strip.numPixels(); i++) {
    strip.setPixelColor(i, Wheel(color));
  }
  strip.show();
}

void rainbow(uint16_t wait) {
  uint16_t i, j;

  for (j = 0; j < 256; j++) {
    for (i = 0; i < strip.numPixels(); i++) {
      strip.setPixelColor(i, Wheel((j) & 255));
    }
    strip.show();
    delay(wait);
  }
  for (j = 256; j > 0; j--) {
    for (i = 0; i < strip.numPixels(); i++) {
      strip.setPixelColor(i, Wheel((j) & 255));
    }
    strip.show();
    delay(wait);
  }
}

// Slightly different, this makes the rainbow equally distributed throughout
void rainbowCycle(uint8_t wait) {
  uint16_t i, j;

  for (j = 0; j < 256 * 5; j++) { // 5 cycles of all colors on wheel
    for (i = 0; i < strip.numPixels(); i++) {
      strip.setPixelColor(i, Wheel(((i * 256 / strip.numPixels()) + j) & 255));
    }
    strip.show();
    delay(wait);
  }
}

// Input a value 0 to 255 to get a color value.
// The colours are a transition r - g - b - back to r.
uint32_t Wheel(byte WheelPos) {
  WheelPos = 255 - WheelPos;
  if (WheelPos < 85) {
    return strip.Color(255 - WheelPos * 3, 0, WheelPos * 3);
  }
  if (WheelPos < 170) {
    WheelPos -= 85;
    return strip.Color(0, WheelPos * 3, 255 - WheelPos * 3);
  }
  WheelPos -= 170;
  return strip.Color(WheelPos * 3, 255 - WheelPos * 3, 0);
}

void sendValues() {
  /*
    This function will send the Arduino's important variables
    to Processing by utalizing Serial.print();

    To send your own values simply add
    Serial.print(",");
    Serial.print(int(your_variable), DEC);

    before the Serial.println(); line
  */
  Serial.print(int(prox_reading), DEC);
  Serial.println();
}

void serialReceive() {
  bool stringComplete = false;
  String msg = "";
  while(Serial.available()) {
    char in =  Serial.read();
    if (in == '\n') {
      stringComplete  = true;
    }
    else {
      msg += in;
    }
    if (stringComplete == true){
      setColorForStrip((int)in);
      Serial.print("received : ");
      Serial.println((int)in);
    }
  }
}

void loop() {
  serialReceive();
  // slowly cycle through all the colors every second
  if (millis() > last_color_change + change_delay) {
    current_color = current_color + dir;
    // if color reaches limit change the dir
    if (current_color > 254 || current_color < 1) {
      dir = dir * -1;
    }
    last_color_change = millis();
    /*
    Serial.print("current color :");
    Serial.println(current_color);
    */
    setColorForStrip(current_color);
  }
  if (millis() > last_ir_polling + ir_delay) {
    for (int i = 0; i < 2; i++) {
      ir_readings[1] = analogRead(ir_pins[1]);
      ir_readings[0] = analogRead(ir_pins[0]);
      last_prox_reading = prox_reading;
      prox_reading = digitalRead(prox_pin);
      us_distance = readUltrasonicDistance();
      /*
      Serial.print(us_distance);
      Serial.print("\t");
      Serial.print(prox_reading);
      Serial.print("\t");
      Serial.print(ir_readings[0]);
      Serial.print("\t");
      Serial.println(ir_readings[0]);
      */
      last_ir_polling = millis();
      if (prox_reading == 1 && last_prox_reading == 0) {
        sendValues();
      }
    }
  }
}

