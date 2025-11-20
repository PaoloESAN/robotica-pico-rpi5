/*
 * servo_control.ino - Arduino Uno
 * Recibe comandos por serial desde Raspberry Pi Pico W (vía level converter)
 * y controla un servomotor MG946R
 * 
 * Conexiones:
 * - Arduino TX -> Level Converter (Low Voltage Side)
 * - Arduino RX -> Level Converter (Low Voltage Side)
 * - Level Converter (High Voltage Side) -> Pico W UART
 * - Servo Signal -> Pin 9
 * - Servo VCC -> Fuente externa 5V
 * - Servo GND -> GND común con Arduino y fuente
 */

#include <Servo.h>

Servo myServo;
const int servoPin = 9;

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
    // Leer el comando (hasta nueva línea)
    String command = Serial.readStringUntil('\n');
    command.trim(); // Eliminar espacios en blanco
    
    // Procesar el comando
    if (command == "ACTIVATE") {
      Serial.println("Comando ACTIVATE recibido - Ejecutando secuencia servo");
      activateServo();
    } else {
      Serial.print("Comando desconocido: ");
      Serial.println(command);
    }
  }
}

void activateServo() {
  // Secuencia de movimiento: 0 -> 90 -> 180 -> 0
  Serial.println("Moviendo servo a 0 grados");
  myServo.write(0);
  delay(500);
  
  Serial.println("Moviendo servo a 90 grados");
  myServo.write(90);
  delay(500);
  
  Serial.println("Moviendo servo a 180 grados");
  myServo.write(180);
  delay(500);
  
  Serial.println("Moviendo servo a 0 grados");
  myServo.write(0);
  delay(500);
  
  Serial.println("Secuencia completada");
}
