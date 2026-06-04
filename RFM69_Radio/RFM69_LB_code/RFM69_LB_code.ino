#include <SPI.h>
#include <RH_RF69.h>

#define RF69_FREQ 434.0
#define RFM69_REG_LNA 0x18  // LNA register address

#if defined (__AVR_ATmega32U4__)
  #define RFM69_CS    8
  #define RFM69_INT   7
  #define RFM69_RST   4
  #define LED        13

#elif defined(ADAFRUIT_FEATHER_M0) || defined(ADAFRUIT_FEATHER_M0_EXPRESS) || defined(ARDUINO_SAMD_FEATHER_M0)
  #define RFM69_CS    8
  #define RFM69_INT   3
  #define RFM69_RST   4
  #define LED        13

#elif defined(ARDUINO_ADAFRUIT_FEATHER_RP2040_RFM)
  #define RFM69_CS   16
  #define RFM69_INT  21
  #define RFM69_RST  17
  #define LED        LED_BUILTIN

#elif defined (__AVR_ATmega328P__)
  #define RFM69_CS    4
  #define RFM69_INT   3
  #define RFM69_RST   2
  #define LED        13

#elif defined(ESP8266)
  #define RFM69_CS    2
  #define RFM69_INT  15
  #define RFM69_RST  16
  #define LED         0

#elif defined(ARDUINO_ADAFRUIT_FEATHER_ESP32S2) || defined(ARDUINO_NRF52840_FEATHER) || defined(ARDUINO_NRF52840_FEATHER_SENSE)
  #define RFM69_CS   10
  #define RFM69_INT   9
  #define RFM69_RST  11
  #define LED        13

#elif defined(ESP32)
  #define RFM69_CS   33
  #define RFM69_INT  27
  #define RFM69_RST  13
  #define LED        13

#elif defined(ARDUINO_NRF52832_FEATHER)
  #define RFM69_CS   11
  #define RFM69_INT  31
  #define RFM69_RST   7
  #define LED        17

#endif

RH_RF69 rf69(RFM69_CS, RFM69_INT);

// ---- NEW: helper to decode gain bits into human readable string ----
const char* getGainLabel(uint8_t gainBits) {
  switch (gainBits & 0x07) {
    case 0: return "AGC (auto)";
    case 1: return "G1 (max)";
    case 2: return "G2 (max-6dB)";
    case 3: return "G3 (max-12dB)";
    case 4: return "G4 (max-24dB)";
    case 5: return "G5 (max-36dB)";
    case 6: return "G6 (max-48dB)";
    default: return "Reserved";
  }
}

void setup() {
  Serial.begin(115200);

  pinMode(LED, OUTPUT);
  pinMode(RFM69_RST, OUTPUT);
  digitalWrite(RFM69_RST, LOW);

  Serial.println("Feather RFM69 RX Test!");
  Serial.println();

  digitalWrite(RFM69_RST, HIGH);
  delay(10);
  digitalWrite(RFM69_RST, LOW);
  delay(10);

  if (!rf69.init()) {
    Serial.println("RFM69 radio init failed");
    while (1);
  }
  Serial.println("RFM69 radio init OK!");

  if (!rf69.setFrequency(RF69_FREQ)) {
    Serial.println("setFrequency failed");
  }

  rf69.setTxPower(20, true);

  uint8_t key[] = { 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
                    0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08 };
  rf69.setEncryptionKey(key);

  Serial.print("RFM69 radio @ "); Serial.print((int)RF69_FREQ); Serial.println(" MHz");
}

void loop() {
  if (rf69.available()) {
    uint8_t buf[RH_RF69_MAX_MESSAGE_LEN];
    uint8_t len = sizeof(buf);

    if (rf69.recv(buf, &len)) {
      if (!len) return;
      buf[len] = 0;

      Serial.print("Received [");
      Serial.print(len);
      Serial.print("]: ");
      Serial.println((char*)buf);

      Serial.print("RSSI: ");
      Serial.println(rf69.lastRssi(), DEC);

      // ---- NEW: read and print LNA gain immediately after packet received ----
      uint8_t lnaReg   = rf69.spiRead(RFM69_REG_LNA);
      uint8_t gainBits  = lnaReg & 0x07;
      Serial.print("LNA Reg raw:  0x"); Serial.println(lnaReg, HEX);
      Serial.print("LNA Gain:     "); Serial.println(getGainLabel(gainBits));
      Serial.println("-----------------------------");

      if (strstr((char *)buf, "Hello World")) {
        uint8_t data[] = "And hello back to you";
        rf69.send(data, sizeof(data));
        rf69.waitPacketSent();
        Serial.println("Sent a reply");
        Blink(LED, 40, 3);
      }
    } else {
      Serial.println("Receive failed");
    }
  }
}

void Blink(byte pin, byte delay_ms, byte loops) {
  while (loops--) {
    digitalWrite(pin, HIGH);
    delay(delay_ms);
    digitalWrite(pin, LOW);
    delay(delay_ms);
  }
}