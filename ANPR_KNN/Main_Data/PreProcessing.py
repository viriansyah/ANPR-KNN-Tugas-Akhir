import cv2
import numpy as np

GAUSSIAN_SMOOTH_FILTER_SIZE = (5, 5)
ADAPTIVE_THRESH_BLOCK_SIZE = 17
ADAPTIVE_THRESH_WEIGHT = -1

def preprocess(imgOriginal):
    ImageGrayScale = extractValue(imgOriginal)

    ImageMaxContrastGrayscale = maximizeContrast(ImageGrayScale)

    height, width = ImageGrayScale.shape

    ImageBlurred = np.zeros((height, width, 1), np.uint8)

    ImageBlurred = cv2.GaussianBlur(ImageMaxContrastGrayscale, GAUSSIAN_SMOOTH_FILTER_SIZE, 5)

    imgThresh = cv2.adaptiveThreshold(ImageBlurred, 255.0, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, ADAPTIVE_THRESH_BLOCK_SIZE, ADAPTIVE_THRESH_WEIGHT)

    return ImageGrayScale, imgThresh

def extractValue(ImageOriginal):
    height, width, numChannels = ImageOriginal.shape

    ImageHSV = np.zeros((height, width, 1), np.uint8)

    ImageHSV = cv2.cvtColor(ImageOriginal, cv2.COLOR_BGR2HSV)

    ImageHue, ImageSaturation, ImageValue = cv2.split(ImageHSV)

    return ImageValue

def maximizeContrast(ImageGrayscale):

    height, width = ImageGrayscale.shape

    ImageTopHat = np.zeros((height, width, 1), np.uint8)
    ImageBlackHat = np.zeros((height, width, 1), np.uint8)

    structuringElement = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))

    ImageTopHat = cv2.morphologyEx(ImageGrayscale, cv2.MORPH_TOPHAT, structuringElement)
    ImageBlackHat = cv2.morphologyEx(ImageGrayscale, cv2.MORPH_BLACKHAT, structuringElement)

    ImageGrayscalePlusTopHat = cv2.add(ImageGrayscale, ImageTopHat)
    ImageGrayscalePlusTopHatMinusBlackHat = cv2.subtract(ImageGrayscalePlusTopHat, ImageBlackHat)

    return ImageGrayscalePlusTopHatMinusBlackHat