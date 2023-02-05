#include <Servo.h>

#define A 0
#define B 1
#define C 2
#define D 3
#define E 4
#define F 5
#define G 6
#define H 7
#define I 8
#define J 9
#define K 10
#define L 11
#define M 12
#define N 13
#define O 14
#define P 15
#define Q 16
#define R 17
#define S 18
#define T 19
#define U 20
#define V 21
#define W 22
#define X 23
#define Y 24
#define Z 25
#define HASH 26
#define ZERO 27
#define ONE 28
#define TWO 29
#define THREE 30
#define FOUR 31
#define FIVE 32
#define SIX 33
#define SEVEN 34
#define EIGHT 35
#define NINE 36
#define SPACE 37

// create six servos
// 1  4
// 2  5
// 3  6

Servo s1;
Servo s2;
Servo s3;
Servo s4;
Servo s5;
Servo s6;


int pos = 0; // variable to store the servo position
String text; // variable to store the transmitted text
int letter;  // variable to store the current letter being displayed
int potPin = A0;   // select the input pin for the potentiometer


byte BRAILLE[][6] = {{1}, {1,2}, {1,4}, {1,4,5}, {1,5}, {1,2,4}, {1,2,4,5}, {1,2,5}, {2,4}, 
  {2,4,5}, {1,3}, {1,2,3}, {1,3,4}, {1,3,4,5}, {1,3,5}, {1,2,3,4}, {1,2,3,4,5}, {1,2,3,5}, 
  {2,3,4}, {2,3,4,5}, {1,3,6}, {1,2,3,6}, {2,4,5,6}, {1,3,4,6}, {1,3,4,5,6}, {1,3,5,6}, {3,4,5,6}, 
  {2,4}, {1}, {1,2}, {1,4}, {1,4,5}, {1,5}, {1,2,4}, {1,2,4,5}, {1,2,5}, {2,4,5} , {}};

Servo motors[6] = {s1, s2, s3, s4, s5, s6};

// servo params
int starts[] = {136, 0, 73, 74, 30, 96};
int ends[] = {118, 18, 55, 56, 48, 78};

void setup() {
  s1.attach(3);  // attaches servo pins to servo objects
  s1.write(starts[0]);
  delay(15);

  s2.attach(5);
  s2.write(starts[1]);
  delay(15);

  s3.attach(6);
  s3.write(starts[2]);
  delay(15);

  s4.attach(9);
  s4.write(starts[3]);
  delay(15);

  s5.attach(10);
  s5.write(starts[4]);
  delay(15);

  s6.attach(11);
  s6.write(starts[5]);
  delay(15);

  Serial.begin(9600);
}

void loop() {

  // Serial.println("Waiting for text to translate");

  while (Serial.available() == 0) {
 }

  text = Serial.readString(); // Read incoming data as string 
  text.toLowerCase();
  // Serial.println(text); // Print data we just read as a check

  for (int ind = 0; ind < text.length(); ind += 1){
    // Serial.println(text[ind]);
    int asciiVal = int(text[ind]);
    switch (asciiVal){
      case 97 ... 122:
        letter = asciiVal - 97 + A;
        break;
      case 48 ... 57:
        letter = asciiVal - 48 + ZERO;
        break;
      case 35:
        letter = HASH;
        break;
      default:
        letter = SPACE;
        break;
    }

    for (int i = 0; i <= sizeof(BRAILLE[letter]); i += 1) {
      // in steps of 1 degree
      motors[BRAILLE[letter][i] - 1].write(ends[BRAILLE[letter][i] - 1]);  // // tell servo to yeet to end position
      delay(15);                                  // waits 15ms for the servo to reach the position
    }                                             //}

    delay(analogRead(potPin) * 1.5 + 500);

    for (int i = 0; i <= sizeof(BRAILLE[letter]); i += 1) {
      // in steps of 1 degree
      motors[BRAILLE[letter][i] - 1].write(starts[BRAILLE[letter][i] - 1]);  // tell servo to yeet back to start position
      delay(15);                                    // waits 15ms for the servo to reach the position
    }   
  }    

  Serial.println("DONE");                                        
}
