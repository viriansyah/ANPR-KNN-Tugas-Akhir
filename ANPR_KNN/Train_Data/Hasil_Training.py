import cv2
import numpy as np
import operator
import os

MIN_CONTOUR_AREA = 100
RESIZED_IMAGE_WIDTH = 20
RESIZED_IMAGE_HEIGHT = 30

class ContourWithData:
    npaContour = None
    boundingRect = None
    intRectX = 0
    intRectY = 0
    intRectWidth = 0
    intRectHeight = 0
    fltArea = 0.0

    def calculateRectTopLeftPointAndWidthAndHeight(self):
        [intX, intY, intWidth, intHeight] = self.boundingRect
        self.intRectX = intX
        self.intRectY = intY
        self.intRectWidth = intWidth
        self.intRectHeight = intHeight

    def checkIfContourIsValid(self):
        if self.fltArea < MIN_CONTOUR_AREA: return False
        return True

def main():
    allContoursWithData = []
    validContoursWithData = []

    try:
        npaClassifications = np.loadtxt("classifications.txt", np.float32)
    except:
        print("Gagal membuka file Classifications.txt, Close Program\n")
        os.system("pause")
        return

    try:
        npaFlattenedImages = np.loadtxt("flattened_images.txt", np.float32)
    except:
        print("Gagal membuka file Flattened_Images.txt, Close Program\n")
        os.system("pause")
        return

    npaClassifications = npaClassifications.reshape((npaClassifications.size, 1))

    kNearest = cv2.ml.KNearest_create()

    kNearest.train(npaFlattenedImages, cv2.ml.ROW_SAMPLE, npaClassifications)

    ImageTesting = cv2.imread("Data_Training/test_5.jpg")

    if ImageTesting is None:
        print("Gagal mengimport file citra \n\n")
        os.system("pause")
        return

    ImageGray = cv2.cvtColor(ImageTesting, cv2.COLOR_BGR2GRAY)
    ImageBlurred = cv2.GaussianBlur(ImageGray, (5, 5), 0)

    ImageThresh = cv2.adaptiveThreshold(ImageBlurred, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)

    ImageThreshCopy = ImageThresh.copy()

    npaContours, npaHierarchy = cv2.findContours(ImageThreshCopy,
                                                 cv2.RETR_EXTERNAL,
                                                 cv2.CHAIN_APPROX_SIMPLE)

    for npaContour in npaContours:
        contourWithData = ContourWithData()
        contourWithData.npaContour = npaContour
        contourWithData.boundingRect = cv2.boundingRect(contourWithData.npaContour)
        contourWithData.calculateRectTopLeftPointAndWidthAndHeight()
        contourWithData.fltArea = cv2.contourArea(contourWithData.npaContour)
        allContoursWithData.append(contourWithData)
    
    for contourWithData in allContoursWithData:
        if contourWithData.checkIfContourIsValid():
            validContoursWithData.append(contourWithData)

    validContoursWithData.sort(key=operator.attrgetter("intRectX"))

    strFinalString = ""

    for contourWithData in validContoursWithData:
        cv2.rectangle(ImageTesting, (contourWithData.intRectX, contourWithData.intRectY), (contourWithData.intRectX + contourWithData.intRectWidth,
                      contourWithData.intRectY + contourWithData.intRectHeight), (0, 255, 0), 2)

        imgROI = ImageThresh[contourWithData.intRectY: contourWithData.intRectY + contourWithData.intRectHeight, contourWithData.intRectX: 
                 contourWithData.intRectX + contourWithData.intRectWidth]

        imgROIResized = cv2.resize(imgROI, (RESIZED_IMAGE_WIDTH, RESIZED_IMAGE_HEIGHT))

        npaROIResized = imgROIResized.reshape((1, RESIZED_IMAGE_WIDTH * RESIZED_IMAGE_HEIGHT))

        npaROIResized = np.float32(npaROIResized)

        retval, npaResults, neigh_resp, dists = kNearest.findNearest(npaROIResized, k=1)

        strCurrentChar = str(chr(int(npaResults[0][0])))

        strFinalString = strFinalString + strCurrentChar

    print("\n" + "Karakter yang di Kenali Adalah : " + strFinalString + "\n")

    cv2.imshow("Citra Test", ImageTesting)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

    return
    
if __name__ == "__main__":
    main()