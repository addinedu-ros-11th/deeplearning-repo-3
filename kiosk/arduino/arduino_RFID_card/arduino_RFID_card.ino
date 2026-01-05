#include <SPI.h>
#include <MFRC522.h>

#define SS_PIN 10
#define RST_PIN 9

MFRC522 rfid(SS_PIN, RST_PIN);

void setup()
{
  Serial.begin(9600);
  SPI.begin();
  rfid.PCD_Init();

  Serial.println("READY");   // Python에서 대기 신호
}

void loop()
{
  // 카드 감지 대기
  if (!rfid.PICC_IsNewCardPresent()) return;
  if (!rfid.PICC_ReadCardSerial()) return;
  
  // 결제 처리
  Serial.println("PAY_OK");

  rfid.PICC_HaltA();
  delay(1500);  // 중복 결제 방지
}
