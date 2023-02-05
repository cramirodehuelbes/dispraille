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

def main():
    video = cv2.VideoCapture(0)
    logging.basicConfig(filename='playground.log', level=logging.DEBUG)

    while True:
        ret, orig = video.read()
        frame = imutils.resize(orig, width=600)
        ratio = orig.shape[1] / float(frame.shape[1])

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mean, blurry = detect_blur_fft(gray, size=60, thresh=10, vis=False)

        color = (0, 0, 255) if blurry else (0, 255, 0)
        text = "Blurry ({:.4f})" if blurry else "Not Blurry ({:.4f})"
        text = text.format(mean)
        cv2.putText(orig, text, (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

        if not blurry:
            blurred = cv2.GaussianBlur(gray, (5, 5), 0)
            edged = cv2.Canny(blurred, 30, 40)
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
                cv2.drawContours(orig, [cardCnt], -1, (0, 255, 0), 2)
                warped = four_point_transform(orig, cardCnt.reshape(4, 2) * ratio)

                ocr = np.zeros(warped.shape, dtype="uint8")
                rgb = cv2.cvtColor(warped, cv2.COLOR_BGR2RGB)
                results = pytesseract.image_to_data(rgb, output_type=Output.DICT)

                for i in range(0, len(results["text"])):
                    x = results["left"][i]
                    y = results["top"][i]
                    w = results["width"][i]
                    h = results["height"][i]

                    text = results["text"][i]
                    conf = int(results["conf"][i])

                    if conf > 20:
                        # clean text
                        text = clean(text)
                        if len(text) > 0:
                            pass
                            cv2.rectangle(warped, (x, y), (x + w, y + h), (0, 0, 255), 2)
                            cv2.putText(orig, text, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)

                output = build_output(orig, warped, ocr)
            cv2.imshow("Output", output)

    video.release()
    cv2.destroyAllWindows()

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
        output[frameH:frameH + cardH, 0:cardW] = cardH

    if ocr is not None:
        output[frameH + cardH:outputH, 0:ocrW] = ocr
    
    return output

def detect_blur_fft(image, size=60, thresh=10, vis=False):
    (h, w) = image.shape
    (cX, cY) = (int(w / 2.0), int(h / 2.0))

    fft = np.fft.fft2(image)
    fftShift = np.fft.fftshift(fft)

    if vis:
        magnitude = 20 * np.log(np.abs(fftShift))
        (fig, ax) = plt.subplots(1, 2, )
        ax[0].imshow(image, cmap="gray")
        ax[0].set_title("Input")
        ax[0].set_xticks([])
        ax[0].set_yticks([])

        ax[1].imshow(magnitude, cmap="gray")
        ax[1].set_title("Magnitude Spectrum")
        ax[1].set_xticks([])
        ax[1].set_yticks([])
        plt.show()

    fftShift[cY - size:cY + size, cX - size:cX + size] = 0
    fftShift = np.fft.ifftshift(fftShift)
    recon = np.fft.ifft2(fftShift)
    fftShift[cY - size:cY + size, cX - size:cX + size] = 0

    magnitude = 20 * np.log(np.abs(recon))
    mean = np.mean(magnitude)

    return mean, mean <= thresh

def east_text_detection(image):
    start = time.perf_counter()
    # load the input image and grab the image dimensions
    orig = image.copy()
    (H, W) = image.shape[:2]

    # set the new width and height and then determine the ratio in change
    # for both the width and height
    (newW, newH) = (320, 320)
    rW = W / float(newW)
    rH = H / float(newH)

    # resize the image and grab the new image dimensions
    image = cv2.resize(image, (newW, newH))
    (H, W) = image.shape[:2]

    # define the two output layer names for the EAST detector model that
    # we are interested -- the first is the output probabilities and the
    # second can be used to derive the bounding box coordinates of text
    layerNames = [
        "feature_fusion/Conv_7/Sigmoid",
        "feature_fusion/concat_3"]

    # load the pre-trained EAST text detector
    logging.info("Loading EAST text detector...")
    net = cv2.dnn.readNet("frozen_east_text_detection.pb")

    # construct a blob from the image and then perform a forward pass of
    # the model to obtain the two output layer sets
    blob = cv2.dnn.blobFromImage(image, 1.0, (W, H),
        (123.68, 116.78, 103.94), swapRB=True, crop=False)
    net.setInput(blob)
    scores, geometry = net.forward(layerNames)

    # show timing information on text prediction
    logging.info("Text detection took {:.6f} seconds".format(time.perf_counter() - start))

    # grab the number of rows and columns from the scores volume, then
    # initialize our set of bounding box rectangles and corresponding
    # confidence scores
    (numRows, numCols) = scores.shape[2:4]
    rects = []
    confidences = []

    # loop over the number of rows
    for y in range(0, numRows):
        # extract the scores (probabilities), followed by the geometrical
        # data used to derive potential bounding box coordinates that
        # surround text
        scoresData = scores[0, 0, y]
        xData0 = geometry[0, 0, y]
        xData1 = geometry[0, 1, y]
        xData2 = geometry[0, 2, y]
        xData3 = geometry[0, 3, y]
        anglesData = geometry[0, 4, y]

    for x in range(0, numCols):
        # if our score does not have sufficient probability, ignore it
        if scoresData[x] < .5:
            continue

        # compute the offset factor as our resulting feature maps will
        # be 4x smaller than the input image
        (offsetX, offsetY) = (x * 4.0, y * 4.0)

        # extract the rotation angle for the prediction and then
        # compute the sin and cosine
        angle = anglesData[x]
        cos = np.cos(angle)
        sin = np.sin(angle)

        # use the geometry volume to derive the width and height of
        # the bounding box
        h = xData0[x] + xData2[x]
        w = xData1[x] + xData3[x]

        # compute both the starting and ending (x, y)-coordinates for
        # the text prediction bounding box
        endX = int(offsetX + (cos * xData1[x]) + (sin * xData2[x]))
        endY = int(offsetY - (sin * xData1[x]) + (cos * xData2[x]))
        startX = int(endX - w)
        startY = int(endY - h)

        # add the bounding box coordinates and probability score to
        # our respective lists
        rects.append((startX, startY, endX, endY))
        confidences.append(scoresData[x])

    boxes = non_max_suppression(np.array(rects), probs=confidences)

    for (startX, startY, endX, endY) in boxes:
        # scale the bounding box coordinates based on the respective
        # ratios
        startX = int(startX * rW)
        startY = int(startY * rH)
        endX = int(endX * rW)
        endY = int(endY * rH)

        # draw the bounding box on the image
        cv2.rectangle(orig, (startX, startY), (endX, endY), (0, 255, 0), 2)

    return boxes, orig


def ocr(im):
    # Uncomment the line below to provide path to tesseract manually
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
    
    # Define config parameters.
    # '-l eng'  for using the English language
    # '--oem 1' for using LSTM OCR Engine
    config = ('-l eng --oem 1 --psm 3')

    # Run tesseract OCR on image
    text = pytesseract.image_to_string(im, config=config)

    # Print recognized text
    print(text)

if __name__ == '__main__':
    main()
