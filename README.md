# Dispraille
For MakeHarvard 2023, we wanted to challenge ourselves by making a project centered around a braille display.

Dispraille is a module that uses optical character recognition (OCR) software to detect text around its user and convert it to braille using a 6-pin tactile interface. By placing a finger on the 3x2 matrix on the top of Dispraille, users can choose to read the text around them through a quick letter-by-letter run-through. For extra challenge, we chose to limit ourselves in making this project with only the materials that MakeHarvard provided, leading us to both enter in and win the top prize in the MakeHarvard Original category.

## Mechanical System
Our mechanical system used a rack and pinion mechanism to lift the pins out of the display. Since braille is very size-specific, we added bent pins in order to bypass the limitation of the larger servo motors and make the display regulation braille size with six micro-servos. We then mounted these into a custom 3D printed case and cover.

## Software
Our software system uses the OpenCV and Tesseract Python libraries in order to create a real-time optical character recognition (OCR) system. This reads text from a webcam live feed and sends serial information to an Arduino sketch, which converts the text into servo commands and lifts the corresponding pins. 

## Electrical
Our electrical subsystem is made up of an Arduino module which is connected to a Raspberry Pi through USB and our set of six motors through its six digital pins. Each pin is mapped to a different position on the braille display, and each letter is mapped to a different combination of pins according to Braille 1. Our electrical subsystem also includes a vibrating motor and a button. The vibrating motor is to alert the user that the webcam is recognizing text, while the button confirms that the user would like the text to be translated to braille.
