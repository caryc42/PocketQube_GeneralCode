#include <SPI.h>
#include <RH_RF69.h>
 
String command; //for serial line control
int count;
 
/************ Radio Setup ***************/
 
// Change to 434.0 or other frequency, must match RX's freq!
#define RF69_FREQ 434.0
 
// First 3 here are boards w/radio BUILT-IN. Boards using FeatherWing follow.
#if defined (__AVR_ATmega328P__)  // Feather 328P w/wing
  #define RFM69_CS    4  //
  #define RFM69_INT   3  //
  #define RFM69_RST   2  // "A"
  #define LED        13
 
#endif
 
// Singleton instance of the radio driver
RH_RF69 rf69(RFM69_CS, RFM69_INT);
 
int16_t packetnum = 0;  // packet counter, we increment per xmission
 
void setup() {
  Serial.begin(115200);
  //while (!Serial) delay(1); // Wait for Serial Console (comment out line if no computer)
 
  pinMode(LED, OUTPUT);
  pinMode(RFM69_RST, OUTPUT);
  digitalWrite(RFM69_RST, LOW);
 
  Serial.println("******RFM69 Test********");
  Serial.println();
 
  // manual reset
  digitalWrite(RFM69_RST, HIGH);
  delay(10);
  digitalWrite(RFM69_RST, LOW);
  delay(10);
 
  if (!rf69.init()) {
    Serial.println("RFM69 radio init failed");
    while (1);
  }
  Serial.println("RFM69 radio init OK!");
  // Defaults after init are 434.0MHz, modulation GFSK_Rb250Fd250, +13dbM (for low power module)
  // No encryption
  if (!rf69.setFrequency(RF69_FREQ)) {
    Serial.println("setFrequency failed");
  }
 
  // If you are using a high power RF69 eg RFM69HW, you *must* set a Tx power with the
  // ishighpowermodule flag set like this:
  rf69.setTxPower(14, true);  // range from 14-20 for power, 2nd arg must be true for 69HCW
 
  // The encryption key has to be the same as the one in the server
  uint8_t key[] = { 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08,
                    0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x07, 0x08};
  rf69.setEncryptionKey(key);
 
  Serial.print("RFM69 radio @");  Serial.print((int)RF69_FREQ);  Serial.println(" MHz");
 
  Serial.println("Send a Command:");
  Serial.println("send, listen");
}
 
void loop(){
  if (Serial.available()) {
    command = Serial.readStringUntil('\n');
    command.trim();
  
    // Check if the command STARTS with "send"
    if (command.startsWith("send")) {
      
      // Look for a space character separating "send" from the number
      int spaceIndex = command.indexOf(' ');
      
      if (spaceIndex != -1) {
        // Extract the substring after the space and convert it to an integer
        String countString = command.substring(spaceIndex + 1);
        int repeatCount = countString.toInt();
        
        // Call send and pass the number to it
        send(repeatCount);
      }
      else {
        // If they just typed "send" without a number, default to 1 time
        send(1);
      }
    }

    else if (command.equals("listen")){
      listen();
    }

    else {
      Serial.print("Unknown command received: ");
      Serial.println(command);
    }

  }
}
 
void send(int times) {
  for(int i = 0; i < times; i++){
  
    //create 60 byte memory array (61 is the max?)
    char radiopacket[40] = "This is test packet from the RFM69 #";
    //convert integer to ASCII, moved incremented packetnum to radiopacket location
    itoa(packetnum++, radiopacket+36, 10);
    Serial.print("Sending "); 
    Serial.println(radiopacket);

    // Send the message
    rf69.send((uint8_t *)radiopacket, strlen(radiopacket));
    rf69.waitPacketSent();

    // Wait 0.250 second between transmits, could also 'sleep' here!
    delay(100);  

  }
}


 
void clearRadioBuffer() {

  uint8_t buf[RH_RF69_MAX_MESSAGE_LEN];
  uint8_t len = sizeof(buf);

  // Remove all pending packets
  while (rf69.available()) {

    rf69.recv(buf, &len);

    len = sizeof(buf);
  }

  Serial.println("Radio buffer cleared");
}
 
void listen() {

  Serial.println("Listening... press q to quit");

  // Flush old packets
  clearRadioBuffer();

  while (1) {

    // Escape condition
    if (Serial.available()) {
      String c = Serial.readStringUntil('\n');
      c.trim();
      //char c = Serial.read();

      if (c == "q" || c == "Q") {
        Serial.println("Exiting listen mode");
        break;
      }
    }

    uint8_t buf[RH_RF69_MAX_MESSAGE_LEN];
    uint8_t len = sizeof(buf);

    if (rf69.waitAvailableTimeout(500)) {

      if (rf69.recv(buf, &len)) {

        buf[len] = '\0';

        Serial.print("Got message: ");
        Serial.print((char*)buf);

        Serial.print(", RSSI: ");
        Serial.println(rf69.lastRssi());

      } else {

        Serial.println("Receive failed");
      }
    }
  }
}
 