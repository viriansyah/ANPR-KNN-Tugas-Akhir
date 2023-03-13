import cv2
import numpy as np
import sys

MIN_CONTOUR_AREA = 100
RESIZED_IMAGE_WIDTH = 20
RESIZED_IMAGE_HEIGHT = 30

def main():
    ImageTraining = cv2.imread("Citra_Plate_Training/training_0.jpg")

    scale_percent = 80
    width = int(ImageTraining.shape[1] * scale_percent/100)
    height = int(ImageTraining.shape[0] * scale_percent/100)
    dimensi = (width, height)

    ResizeImageTrain = cv2.resize(ImageTraining, dimensi, interpolation=cv2.INTER_AREA)

    if ImageTraining is None:
        print("Tidak Terdapat Gambar Training")
        return
    
    ImageGray = cv2.cvtColor(ResizeImageTrain, cv2.COLOR_BGR2GRAY)
    ImageBlurred = cv2.GaussianBlur(ImageGray, (5,5), 0)
    ImageThresh = cv2.adaptiveThreshold(ImageBlurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11,2)
    cv2.imshow("Image Thresh", ImageThresh)
    
    ImageThreshCopy = ImageThresh.copy()
    npaContours, npaHierarchy = cv2.findContours(ImageThreshCopy, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    npaFlattenedImages = np.empty((0, RESIZED_IMAGE_WIDTH * RESIZED_IMAGE_HEIGHT))
    intClassifications = []
    intValidChars = [ord('0'), ord('1'), ord('2'), ord('3'), ord('4'), ord('5'), ord('6'), ord('7'), ord('8'), ord('9'),
                     ord('A'), ord('B'), ord('C'), ord('D'), ord('E'), ord('F'), ord('G'), ord('H'), ord('I'), ord('J'),
                     ord('K'), ord('L'), ord('M'), ord('N'), ord('O'), ord('P'), ord('Q'), ord('R'), ord('S'), ord('T'),
                     ord('U'), ord('V'), ord('W'), ord('X'), ord('Y'), ord('Z')]
    
    for npaContour in npaContours:
        if cv2.contourArea(npaContour) > MIN_CONTOUR_AREA:
            [intX, intY, intW, intH] = cv2.boundingRect(npaContour)

            cv2.rectangle(ResizeImageTrain, (intX, intY), (intX + intW, intY + intH), (0, 179, 0),2) #GREEN

            imgROI = ImageThresh[intY:intY + intH, intX:intX + intW]
            imgROIResized = cv2.resize(imgROI, (RESIZED_IMAGE_WIDTH, RESIZED_IMAGE_HEIGHT))

            cv2.imshow("imgROI", imgROI)
            cv2.imshow("imgROIResized", imgROIResized)
            cv2.imshow("training_numbers.png", ResizeImageTrain)

            intChar = cv2.waitKey(0)
            print(intChar)
            if intChar == 27:
                sys.exit()
            elif intChar in intValidChars:
                intClassifications.append(intChar)
                npaFlattenedImage = imgROIResized.reshape((1, RESIZED_IMAGE_WIDTH * RESIZED_IMAGE_HEIGHT))
                npaFlattenedImages = np.append(npaFlattenedImages, npaFlattenedImage, 0)

    fltClassifications = np.array(intClassifications, np.float32)
    npaClassifications = fltClassifications.reshape((fltClassifications.size, 1))

    print("\n\ntraining selesai !!\n")

    np.savetxt("classifications.txt", npaClassifications)
    np.savetxt("flattened_images.txt", npaFlattenedImages)

    cv2.destroyAllWindows()
    return

if __name__ == "__main__":
    main()