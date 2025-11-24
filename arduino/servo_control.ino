/*
 * servo_control.ino - Arduino Uno
 * Recibe comandos por serial desde Raspberry Pi Pico W (vía level converter)
 * y controla un servomotor MG946R
 * 
 * Conexiones:
 * - Arduino TX (Pin 1) -> Level Converter HV2
 * - Arduino RX (Pin 0) -> Level Converter HV1
 * - Level Converter LV1 -> Pico W GP4 (Pin 6)
 * - Level Converter LV2 -> Pico W GP5 (Pin 7)
 * - Servo Signal -> Pin 9
 * - Servo VCC -> Fuente externa 5V
 * - Servo GND -> GND común con Arduino y fuente
 * 
 * Protocolo: Recibe comando "A" (sin salto de línea)
 */

#include <Servo.h>

Servo myServo;
const int servoPin = 9;
const byte ACTIVATE_CMD = 'A';  // Comando para activar servo

void setup() {
  // Inicializar comunicación serial
  Serial.begin(9600);
  
  // Adjuntar servo al pin 9
  myServo.attach(servoPin);
  
  // Posición inicial
  myServo.write(0);
  
  Serial.println("Arduino listo - Esperando comandos...");
}

void loop() {
  // Verificar si hay datos disponibles en el puerto serial
  if (Serial.available() > 0) {
    // Leer un carácter
    char command = Serial.read();
    
    // Procesar el comando
    if (command == 'A') {  // 'A' para ACTIVATE
      Serial.println("Comando ACTIVATE recibido - Ejecutando secuencia servo");
      activateServo();
    } else {
      Serial.print("Comando desconocido: ");
      Serial.println(command);
    }
  }
}

void activateServo() {
  // Secuencia de movimiento: 0 -> 180 -> 0
  Serial.println("Moviendo servo a 0 grados");
  myServo.write(0);
  
  Serial.println("Moviendo servo a 180 grados");
  myServo.write(180);
  delay(500);
  
  Serial.println("Moviendo servo a 0 grados");
  myServo.write(0);
  delay(500);
  
  Serial.println("Secuencia completada");
  
  // Enviar confirmación al Pico
  Serial.write('D');  // 'D' para Done
}
