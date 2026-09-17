#include <Wire.h>
#include <Adafruit_NeoPixel.h>
#include <Adafruit_SSD1306.h>
#include <Adafruit_GFX.h>
#include <Adafruit_ADS1X15.h>

// ---- LED STRIP ----
#define LED_PIN 5
#define LED_COUNT 60
#define BRIGHTNESS 5
Adafruit_NeoPixel strip(LED_COUNT, LED_PIN, NEO_GRB + NEO_KHZ800);

// ---- OLED ----
#define SCREEN_WIDTH 128
#define SCREEN_HEIGHT 64
#define TCA_ADDR 0x70
#define AS5600_ADDR 0x36
#define MAX30102_ADDR 0x57

Adafruit_SSD1306 oled0(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
Adafruit_SSD1306 oled1(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);
Adafruit_SSD1306 oled2(SCREEN_WIDTH, SCREEN_HEIGHT, &Wire, -1);

// ---- ADS1115 ----
Adafruit_ADS1115 ads;

// ---- SWITCH PINS ----
#define REED1_PIN 2
#define REED2_PIN 3
#define REED3_PIN 4
#define DEMO_BTN_PIN 6
#define LIMIT_PIN 12

// ---- STATE ----
bool oledInitialised[3] = {false, false, false};
bool demoLED = false;   // when true, pixel 29 stays blue through all LED ops
volatile bool i2cBusy = false;

// ---- TCA SELECT (fast single-transaction version) ----
void selectTCA(uint8_t channel) {
  Wire.beginTransmission(TCA_ADDR);
  Wire.write(1 << channel);
  Wire.endTransmission();
}

void writeReg(uint8_t reg, uint8_t val) {
  selectTCA(6);
  Wire.beginTransmission(MAX30102_ADDR);
  Wire.write(reg);
  Wire.write(val);
  Wire.endTransmission();
  delay(5);
}

uint8_t readReg(uint8_t reg) {
  selectTCA(6);
  Wire.beginTransmission(MAX30102_ADDR);
  Wire.write(reg);
  Wire.endTransmission(false);
  Wire.requestFrom(MAX30102_ADDR, 1);
  return Wire.read();
}

// ---- INIT MAX30102 ----
void initMAX30102() {
  selectTCA(6);
  writeReg(0x09, 0x40);
  delay(500);
  selectTCA(6);
  writeReg(0x08, 0x4F);
  writeReg(0x09, 0x03);
  writeReg(0x0A, 0x27);
  writeReg(0x0C, 0x24);
  writeReg(0x0D, 0x24);
}

// ---- LED MIRROR HELPER ----
void setMirroredLED(int pos, uint32_t color) {
  strip.setPixelColor(pos, color);
  strip.setPixelColor(29 - pos, color);
  strip.setPixelColor(30 + pos, color);
  strip.setPixelColor(59 - pos, color);
}

// ---- LED PROGRESS BAR ----
// Only ever called BETWEEN i2c transactions (never mid-read), so strip.show()'s
// interrupt-disable window can't collide with a Wire transfer.
void setLEDLevel(int level) {
  level = constrain(level, 0, 15);
  strip.clear();
  uint32_t col = strip.Color(255, 0, 0);
  for (int i = 0; i < level; i++) setMirroredLED(i, col);
  strip.show();
}

// ---- STREAM MAX30102 RAW DATA (with local LED progress bar) ----
void streamMAX30102Raw(int samples) {
  i2cBusy = true;
  initMAX30102();
  delay(200);

  int lastLevel = -1;
  setLEDLevel(1); lastLevel = 1;

  // ---- SETTLING PHASE (3s): bar fills 1 -> 7 ----
  unsigned long settleStart = millis();
  int lastSettlePing = 0;
  while (millis() - settleStart < 3000) {
    if ((int)((millis() - settleStart) / 500) > lastSettlePing) {
      Serial.println("SETTLING");
      lastSettlePing++;
    }

    uint8_t wp = readReg(0x04);
    uint8_t rp = readReg(0x06);
    if (wp != rp) {
      selectTCA(6);
      Wire.beginTransmission(MAX30102_ADDR);
      Wire.write(0x07);
      Wire.endTransmission(false);
      Wire.requestFrom(MAX30102_ADDR, 6);
      for (int i = 0; i < 6; i++) Wire.read();
    }

    // update bar AFTER the i2c work for this iteration is done
    int level = min(7, lastSettlePing + 1);
    if (level != lastLevel) { setLEDLevel(level); lastLevel = level; }

    delay(10);
  }

  // ---- SAMPLING PHASE: bar fills 7 -> 15 ----
  int count = 0;
  unsigned long startTime = millis();
  while (count < samples && millis() - startTime < 7000) {
    uint8_t writePtr = readReg(0x04);
    uint8_t readPtr  = readReg(0x06);
    int numAvailable = (writePtr - readPtr) & 0x1F;
    for (int i = 0; i < numAvailable && count < samples; i++) {
      selectTCA(6);
      Wire.beginTransmission(MAX30102_ADDR);
      Wire.write(0x07);
      Wire.endTransmission(false);
      Wire.requestFrom(MAX30102_ADDR, 6);
      uint32_t red = ((uint32_t)(Wire.read() & 0x03) << 16) | ((uint32_t)Wire.read() << 8) | Wire.read();
      uint32_t ir  = ((uint32_t)(Wire.read() & 0x03) << 16) | ((uint32_t)Wire.read() << 8) | Wire.read();
      Serial.print("RAW:"); Serial.print(red); Serial.print(":"); Serial.print(ir); Serial.print(":"); Serial.println(millis() - startTime);
      count++;
    }

    // update bar AFTER the full sample batch for this iteration is read
    int level = min(15, 7 + min(8, (count * 8) / 195));
    if (level != lastLevel) { setLEDLevel(level); lastLevel = level; }

    delay(10);
  }

  setLEDLevel(15);
  Serial.println("HR_DONE");
  i2cBusy = false;
}

// ---- INIT OLEDS ----
void initOLEDs() {
  selectTCA(2);
  delay(20);
  if (oled0.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { oledInitialised[0] = true; oled0.clearDisplay(); oled0.display(); }
  selectTCA(3);
  delay(20);
  if (oled1.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { oledInitialised[1] = true; oled1.clearDisplay(); oled1.display(); }
  selectTCA(4);
  delay(20);
  if (oled2.begin(SSD1306_SWITCHCAPVCC, 0x3C)) { oledInitialised[2] = true; oled2.clearDisplay(); oled2.display(); }
}

// ---- BASE64 DECODE INTO BUFFER ----
int base64_decode_into(const char* input, int input_len, uint8_t* output, int max_output_len) {
  static const char* tbl = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
  int out_len = 0;
  uint32_t buffer = 0;
  int bits = 0;
  for (int i = 0; i < input_len; i++) {
    char c = input[i];
    if (c == '=') break;
    const char* p = strchr(tbl, c);
    if (!p) continue;
    int val = p - tbl;
    buffer = (buffer << 6) | val;
    bits += 6;
    if (bits >= 8) {
      bits -= 8;
      if (out_len < max_output_len) {
        output[out_len++] = (buffer >> bits) & 0xFF;
      }
    }
  }
  return out_len;
}

// ---- BMP COMMAND HANDLER ----
#define LINE_BUF_SIZE 1500
char lineBuf[LINE_BUF_SIZE];
int lineBufPos = 0;

void processBMP(char* line, int len) {
  if (len < 6 || line[0] != 'B' || line[1] != 'M' || line[2] != 'P' || line[3] != ':') return;

  int idx = line[4] - '0';
  if (line[5] != ':') return;
  if (idx < 0 || idx > 2 || !oledInitialised[idx]) return;

  char* b64start = line + 6;
  int b64len = len - 6;

  Adafruit_SSD1306* display;
  uint8_t tcaCh;
  if (idx == 0) { display = &oled0; tcaCh = 2; }
  else if (idx == 1) { display = &oled1; tcaCh = 3; }
  else { display = &oled2; tcaCh = 4; }

  uint8_t* buf = display->getBuffer();
  int decoded = base64_decode_into(b64start, b64len, buf, 1024);
  if (decoded != 1024) return;

  selectTCA(tcaCh);
  display->display();
}

// ---- READ AS5600 ----
float readAngle() {
  selectTCA(7);
  Wire.beginTransmission(AS5600_ADDR);
  Wire.write(0x0E);
  Wire.endTransmission(false);
  Wire.requestFrom(AS5600_ADDR, 2);
  if (Wire.available() < 2) return -1;
  uint8_t high = Wire.read();
  uint8_t low = Wire.read();
  int raw = ((high & 0x0F) << 8) | low;
  return raw * 360.0 / 4096.0;
}

// ---- READ ADS1115 POTS ----
float readADSPot(uint8_t channel) {
  selectTCA(5);
  int16_t raw = ads.readADC_SingleEnded(channel);
  return constrain((float)raw / 26400.0, 0.0, 1.0);
}

// ---- LED CONTROL ----
void handleLED(const char* cmd) {
  if (strcmp(cmd, "OFF") == 0) { strip.clear(); strip.show(); return; }

  const char* colon = strchr(cmd, ':');
  if (!colon) return;

  char colour[8];
  int colourLen = colon - cmd;
  if (colourLen >= (int)sizeof(colour)) return;
  memcpy(colour, cmd, colourLen);
  colour[colourLen] = '\0';

  int count = atoi(colon + 1);
  count = constrain(count, 0, 15);

  strip.clear();
  uint32_t col;
  if (strcmp(colour, "RED") == 0) col = strip.Color(255, 0, 0);
  else if (strcmp(colour, "WHITE") == 0) col = strip.Color(255, 255, 255);
  else if (strcmp(colour, "GREEN") == 0) col = strip.Color(0, 255, 0);
  else if (strcmp(colour, "ORANGE") == 0) col = strip.Color(255, 60, 0);
  else if (strcmp(colour, "BLUE") == 0) col = strip.Color(0, 0, 255);
  else return;

  for (int i = 0; i < count; i++) setMirroredLED(i, col);
  strip.show();
}

// ---- SETUP ----
void setup() {
  Serial.begin(115200);
  Wire.begin();
  strip.begin();
  strip.setBrightness(BRIGHTNESS);
  strip.clear();
  strip.show();
  pinMode(REED1_PIN, INPUT_PULLUP);
  pinMode(REED2_PIN, INPUT_PULLUP);
  pinMode(REED3_PIN, INPUT_PULLUP);
  pinMode(DEMO_BTN_PIN, INPUT_PULLUP);
  pinMode(LIMIT_PIN, INPUT_PULLUP);
  initOLEDs();
  initMAX30102();
  selectTCA(5);
  ads.begin(0x48);
  delay(500);
  Serial.setTimeout(50);
  Serial.println("READY");
}

// ---- LOOP ----
unsigned long lastPotSend = 0;
unsigned long lastAngleSend = 0;
bool receivingBMP = false;

void loop() {
  unsigned long now = millis();

  // send pot values — paused while receiving a BMP command to avoid interleaving
  if (!i2cBusy && !receivingBMP && now - lastPotSend > 100) {
    lastPotSend = now;

    float raw0 = readADSPot(3);   // left pot   -> OLED 0 (softpower, left)
    float raw1 = readADSPot(2);   // middle pot -> OLED 1 (overton, middle)
    float raw2 = readADSPot(1);   // right pot  -> OLED 2 (delta, right)

    float pot0 = 1.0 - raw0;
    float pot1 = 1.0 - raw1;
    float pot2 = 1.0 - raw2;

    float lin0 = analogRead(A0) / 1023.0;
    float lin1 = analogRead(A1) / 1023.0;
    float lin2 = analogRead(A2) / 1023.0;
    float lin3 = analogRead(A3) / 1023.0;
    float lin4 = analogRead(A6) / 1023.0;
    float lin5 = analogRead(A7) / 1023.0;
    int demoBtn = (digitalRead(DEMO_BTN_PIN) == LOW) ? 1 : 0;

    Serial.print("POTS:");
    Serial.print(pot0, 3); Serial.print(":");
    Serial.print(pot1, 3); Serial.print(":");
    Serial.print(pot2, 3); Serial.print(":");
    Serial.print(lin0, 3); Serial.print(":");
    Serial.print(lin1, 3); Serial.print(":");
    Serial.print(lin2, 3); Serial.print(":");
    Serial.print(lin3, 3); Serial.print(":");
    Serial.print(lin4, 3); Serial.print(":");
    Serial.println(lin5, 3);   // <-- MUST be println, not print
    
  }

  // send angle
  if (!i2cBusy && !receivingBMP && now - lastAngleSend > 50) {
    lastAngleSend = now;
    float angle = readAngle();
    if (angle >= 0) { Serial.print("ANGLE:"); Serial.println(angle, 2); }
  }

  // reed switches — edge detection: fire once on the moment they become active
  static bool reed1Last = HIGH, reed2Last = HIGH, reed3Last = HIGH;
  bool reed1Now = digitalRead(REED1_PIN);
  bool reed2Now = digitalRead(REED2_PIN);
  bool reed3Now = digitalRead(REED3_PIN);
  if (reed1Now == LOW && reed1Last == HIGH) Serial.println("REED:1");
  if (reed2Now == LOW && reed2Last == HIGH) Serial.println("REED:2");
  if (reed3Now == LOW && reed3Last == HIGH) Serial.println("REED:3");
  reed1Last = reed1Now;
  reed2Last = reed2Now;
  reed3Last = reed3Now;

  // limit and shutdown
  if (digitalRead(LIMIT_PIN) == LOW) { Serial.println("LIMIT:1"); delay(300); }
  // demo button: tap (<3s) = DEMO on release, hold >=3s = SHUTDOWN
  static bool btnDown = false;
  static unsigned long btnStart = 0;
  static bool shutdownSent = false;
  bool btnNow = (digitalRead(DEMO_BTN_PIN) == LOW);

  if (btnNow && !btnDown) {
    btnDown = true;
    btnStart = millis();
    shutdownSent = false;
  } else if (btnNow && btnDown) {
    if (!shutdownSent && millis() - btnStart >= 3000) {
      Serial.println("SHUTDOWN");
      shutdownSent = true;
    }
  } else if (!btnNow && btnDown) {
    btnDown = false;
    if (!shutdownSent && millis() - btnStart < 3000) {
      Serial.println("DEMO");
    }
  }

  // serial command handler — reads char by char to avoid String heap limit
  while (Serial.available()) {
    char c = Serial.read();
    if (c == '\n') {
      lineBuf[lineBufPos] = '\0';
      if (lineBufPos >= 4 && lineBuf[0] == 'B' && lineBuf[1] == 'M' && lineBuf[2] == 'P' && lineBuf[3] == ':') {
        processBMP(lineBuf, lineBufPos);
      } else if (lineBufPos >= 4 && strncmp(lineBuf, "LED:", 4) == 0) {
        handleLED(lineBuf + 4);
      } else if (lineBufPos >= 4 && strncmp(lineBuf, "PIX:", 4) == 0) {
        int pix = atoi(lineBuf + 4);
        strip.clear();
        if (pix >= 0 && pix < LED_COUNT) {
          strip.setPixelColor(pix, strip.Color(0, 0, 255));
        }
        strip.show();
      } else if (strcmp(lineBuf, "READ_HR") == 0) {
        streamMAX30102Raw(500);
      }
      lineBufPos = 0;
      receivingBMP = false;
    } else if (c != '\r') {
      if (lineBufPos == 3 && lineBuf[0] == 'B' && lineBuf[1] == 'M' && lineBuf[2] == 'P') {
        receivingBMP = true;
      }
      if (lineBufPos < LINE_BUF_SIZE - 1) {
        lineBuf[lineBufPos++] = c;
      }
    }
  }
}