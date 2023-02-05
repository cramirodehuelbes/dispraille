#include <Servo.h>

// create six servos
// 1  6
// 2  5
// 3  4

Servo s1;
Servo s2;
Servo s3;
Servo s4;
Servo s5;  
Servo s6;


int pos = 0;    // variable to store the servo position

byte BRAILLE [][6] = {{1}, {1, 2}, {1, 4}, {1,4,5}, {1,5}, {1,2,4}, {1,2,4,5}, {1,2,5}, {2,4}, {2,4,5}, {1,3}, {1,2,3}, {1,3,4}, {1,3,4,5}, {1,3,5}, {1,2,3,4}, {1,2,3,4,5}, {1,2,3,5}, {2,3,4}, {2,3,4,5}, {1,3,6}, {1,2,3,6}, {2,4,5,6}, {1,3,4,6}, {1,3,4,5,6}, {1,3,5,6}, {3,4,5,6}, {1}, {1,2}, {1,4}, {1,4,5}, {1,5}, {1,2,4}, {1,2,4,5}, {1,2,5}, {2,4}, {2,4,5}};
Servo motors[6] = {s1, s2, s3, s4, s5, s6};

// servo params
int start = 90;
int end = 120;

void setup() {
  s1.attach(3);  // attaches servo pins to servo objects
  s2.attach(5);
  s3.attach(6);
  s4.attach(9);
  s5.attach(10);
  s6.attach(11);

  Serial.begin(9600);
}

void loop() {

  Serial.println("Insert letter");

  while (Serial.available() == 0) {
  }

  int letter = Serial.parseInt();
  Serial.println(letter);

//    for (pos =90; pos <= 120; pos += 1) { // goes from 0 degrees to 180 degrees, gradually
      for (int i = 0; i<= sizeof(BRAILLE[letter]); i+=1){
        // in steps of 1 degree
        motors[BRAILLE[letter][i]-1].write(end);              // // tell servo to yeet to end position
        delay(15);                       // waits 15ms for the servo to reach the position
      }//}

//    delay(2000);
    
    //for (pos = 90; pos >= 120; pos -= 1) {     // goes from 180 degrees to 0 degrees, gradually
      for (int i = 0; i<= sizeof(BRAILLE[letter]); i+=1){
        // in steps of 1 degree
        motors[BRAILLE[letter][i]-1].write(start);              // tell servo to yeet back to start position
        delay(15);                       // waits 15ms for the servo to reach the position
    }//}
}
