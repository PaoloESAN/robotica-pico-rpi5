#include <Servo.h>

Servo miServo; // Crear objeto servo
const int servoPin = 9; // Pin donde conectas el servo
char incomingByte; // Variable para leer el dato serial

void setup() {
  miServo.attach(servoPin); 
  
  // Inicializar en posición 0
  miServo.write(0);
  
  // Iniciar comunicación serial a 9600 baudios (igual que en Python)
  Serial.begin(9600); 
}

void loop() {
  // Verificar si hay datos disponibles desde Python
  if (Serial.available() > 0) {
    // Leer el dato
    incomingByte = Serial.read();
    
    // Si recibimos el 1 se movera el servo
    if (incomingByte == '1') {
      prueba();
    }
  }/*
  else {
     desac();
  }*/
}

void activarSecuenciaServo() {
  // Mover de 0 a 180 grados
  for (int pos = 90; pos <= 180; pos += 2) { 
    miServo.write(pos);              
    delay(5); // Ajusta este delay para cambiar la velocidad de subida
  }
  
  delay(500); // Esperar medio segundo arriba
  
  // Mover de 180 a 0 grados
  for (int pos = 180; pos >= 90; pos -= 2) { 
    miServo.write(pos);              
    delay(5); // Ajusta este delay para cambiar la velocidad de bajada
  }
}
void desac() {
  // Mover de 0 a 180 grados
  for (int pos = 90; pos >= 0; pos -= 2) { 
    miServo.write(pos);              
    delay(5); // Ajusta este delay para cambiar la velocidad de subida
  }
  
  delay(500); // Esperar medio segundo arriba
  
  // Mover de 180 a 0 grados
  for (int pos = 0; pos <= 90; pos += 2) { 
    miServo.write(pos);              
    delay(5); // Ajusta este delay para cambiar la velocidad de bajada
  }
}
void prueba() {
  // Mover de 0 a 180 grados
  for (int pos = 0; pos <= 90; pos += 2) { 
    miServo.write(pos);              
    delay(5); // Ajusta este delay para cambiar la velocidad de subida
  }
  
  delay(500); // Esperar medio segundo arriba
  
  // Mover de 180 a 0 grados
  for (int pos = 90; pos >= 0; pos -= 2) { 
    miServo.write(pos);              
    delay(5); // Ajusta este delay para cambiar la velocidad de bajada
  }
}