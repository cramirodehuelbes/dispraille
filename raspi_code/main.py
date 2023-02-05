import numpy as np
import cv2
import pytesseract
from pytesseract import Output
import imutils
from imutils.perspective import four_point_transform
from imutils.object_detection import non_max_suppression
import logging
import time
from cleantext import clean
from collections import Counter
import RPi.GPIO as GPIO
import re
import serial

vis = True
# Pin Setup (pins are placeholders)
VIBRATION_PIN = 17 
BUTTON_PIN = 15
GPIO.setwarnings(False)

GPIO.setmode(GPIO.BCM)
GPIO.setup(VIBRATION_PIN, GPIO.OUT)
GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)

# Serial Setup
SERIAL_RATE = 9600
try:
    ser = serial.Serial('/dev/ttyACM0', SERIAL_RATE, timeout=None)
except Exception:
    ser = serial.Serial('/dev/ttyACM1', SERIAL_RATE, timeout=None)
    
ser.reset_input_buffer()

def main():
    video = cv2.VideoCapture(0)
    logging.basicConfig(filename='playground.log', level=logging.DEBUG)
    phrases = LRUList(60)

    starttime = time.time()
    while True:
        output = None
        ret, orig = video.read()
        frame = imutils.resize(orig, width=600)
        ratio = orig.shape[1] / float(frame.shape[1])

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edged = cv2.Canny(blurred, 20, 100)
        cnts = cv2.findContours(edged.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cnts = imutils.grab_contours(cnts)
        cnts = sorted(cnts, key=cv2.contourArea, reverse=True)[:5]

        cardCnt = None
        for c in cnts:
            peri = cv2.arcLength(c, True)
            approx = cv2.approxPolyDP(c, 0.02 * peri, True)

            if len(approx) == 4:
                cardCnt = approx
                break

        if cardCnt is not None:
            # cv2.drawContours(orig, [cardCnt], -1, (0, 255, 0), 2)
            warped = four_point_transform(orig, cardCnt.reshape(4, 2) * ratio)

            ocr = np.zeros(warped.shape, dtype="uint8")
            rgb = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
            results = pytesseract.image_to_data(rgb, output_type=Output.DICT)
            phrase = []

            for i in range(0, len(results["text"])):
                x = results["left"][i]
                y = results["top"][i]
                w = results["width"][i]
                h = results["height"][i]

                word  = results["text"][i]
                conf = int(results["conf"][i])
                phrase.append(word)

                if conf > 20:
                    # clean text
                    word = clean(word)
                    if len(word) > 0:
                        pass
                        cv2.rectangle(warped, (x, y), (x + w, y + h), (0, 0, 255), 2)
                        cv2.putText(ocr, word, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

            phrases.add(tuple(phrase))
            if vis:
                output = build_output(orig, warped, ocr)

        if vis:
            if output is not None:
                cv2.imshow("Output", output)
            else:
                cv2.imshow("Output", orig)

        try:
            mode = Counter(phrases.items).most_common(1)[0]
            print(mode)
            if mode[1] > 3 and len(mode[0]) > 3:
                vibrate_on()
                if button_pressed():
                    print('button pressed')
                    vibrate_off()
                    transmit(mode[0])
            else:
                vibrate_off()
                
        except:
            pass

        time.sleep(1/2 - ((time.time() - starttime) % 1/2))
            

    video.release()
    cv2.destroyAllWindows()
    ser.close()

def build_output(frame, warped, ocr):
    frameH, frameW = frame.shape[:2]
    cardH, cardW = (0,0)
    ocrH, ocrW = (0,0)

    if warped is not None:
        cardH, cardW = warped.shape[:2]

    if ocr is not None:
        ocrH, ocrW = ocr.shape[:2]

    outputW = max(frameW, cardW, ocrW)
    outputH = frameH + cardH + ocrH

    output = np.zeros((outputH, outputW, 3), dtype="uint8")
    output[0:frameH, 0:frameW] = frame

    if warped is not None:
        output[frameH:frameH + cardH, 0:cardW] = warped

    if ocr is not None:
        output[frameH + cardH:frameH+cardH+ocrH, 0:ocrW] = ocr
    
    return output
    
class LRUList:
    def __init__(self, max_size):
        self.items = []
        self.max_size = max_size

    def add(self, toadd):
        if len(self.items) == self.max_size:
            self.items.pop(0)
        self.items.append(toadd)

def vibrate_on():
    GPIO.output(VIBRATION_PIN, GPIO.HIGH)
    print('vibe on')

def vibrate_off():
    GPIO.output(VIBRATION_PIN, GPIO.LOW)
    print('vibe off')
    
def button_pressed():
    print(GPIO.input(BUTTON_PIN))
    return GPIO.input(BUTTON_PIN) == 1

def transmit(phrase):
    print('transmit')
    phrase = [p for p in phrase if p != '']
    phrase = " ".join(phrase)
    phrase = re.sub(r'(\d+)', r'#\1', phrase)
    print(phrase)
    ser.write(phrase.encode('utf-8'))
    ser.flushInput()
    print(phrase)

    while ser.inWaiting() == 0:
        pass
    
    if ser.inWaiting() > 0:
        print(ser.readline())
        vibrate_on()
        time.sleep(0.5)
        vibrate_off()

if __name__ == "__main__":
    main()
