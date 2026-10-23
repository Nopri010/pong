// Pongino: Arduino Uno -> USB serial -> servidor Python.
// Potenciometros: terminal central em A0/A1; extremos em 5V e GND.
// O modo hibrido usa A0 e ignora A1, mas preserva os dois campos seriais.

#include <Arduino.h>

constexpr uint8_t PINO_JOGADOR_1 = A0;
constexpr uint8_t PINO_JOGADOR_2 = A1;
constexpr unsigned long BAUDRATE = 115200;
constexpr unsigned long INTERVALO_MS = 100;

void setup() {
  pinMode(PINO_JOGADOR_1, INPUT);
  pinMode(PINO_JOGADOR_2, INPUT);
  Serial.begin(BAUDRATE);
}

void loop() {
  const int valorJogador1 = analogRead(PINO_JOGADOR_1);
  const int valorJogador2 = analogRead(PINO_JOGADOR_2);

  // Cada quadro tem exatamente tres linhas, sem mensagens extras.
  Serial.println(valorJogador1);
  Serial.println(';');
  Serial.println(valorJogador2);

  delay(INTERVALO_MS);
}
