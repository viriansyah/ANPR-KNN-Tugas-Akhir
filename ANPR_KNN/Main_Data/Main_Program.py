import os
import cv2
import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders

from RPLCD import *
from time import sleep
from RPLCD.i2c import CharLCD

import Hasil_Karakter
import Hasil_Plat

import RPi.GPIO as GPIO
import time
GPIO.setmode(GPIO.BCM)

TRIG=23
ECHO=24

SCALAR_GREEN = (0.0, 255.0, 0.0)
SCALAR_RED = (0.0, 0.0, 255.0)

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
showSteps = False

def count_file(count_file):
    dir_path = r'/home/pi/Project_TA/ANPR_KNN/Sample_Image'
    for path in os.listdir(dir_path):
        if os.path.isfile(os.path.join(dir_path, path)):
            count_file += 1
    return count_file

def trigger_sens(jarak_awal):
    GPIO.setwarnings(False)
    GPIO.setup(TRIG,GPIO.OUT)
    GPIO.setup(ECHO,GPIO.IN)
    while True:
        GPIO.output(TRIG, False)
        time.sleep(0.75)
        GPIO.output(TRIG, True)
        time.sleep(0.75)
        GPIO.output(TRIG, False)
        while GPIO.input(ECHO)==0:
            pulse_start = time.time()
        while GPIO.input(ECHO)==1:
            pulse_end = time.time()
        pulse_duration = pulse_end - pulse_start
        distance = pulse_duration * 17150
        distance = round(distance, 0)
        print ("Distance: ",distance,"cm")
        if distance <= 15:
            break
    return distance

def take_photo(count):
    cam = cv2.VideoCapture(0)
    cam.set(3, 800)
    cam.set(4, 600)
    check, frame = cam.read()
    cv2.imwrite("/home/pi/Project_TA/ANPR_KNN/Sample_Image/test%d.jpg"%count,frame)
    cam.release()
    count+=1
    proses(count)

def monitoring():
    cam = cv2.VideoCapture(0)
    cam.set(3, 800)
    cam.set(4, 600)
    while(True):
        ret, frame = cam.read()
        cv2.imshow('frame',frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    cam.release()
    cv2.destroyAllWindows()
    
def main(count):
    jarak = 0   
    while (True):
        if trigger_sens(jarak) <= 15:
            take_photo(count)
            break
        
def read_database(file,PlatNo,nourut):
    tarif = 30000
    with open('DB_Kendaraan.csv', mode='r+') as csvfile:
        data = csv.DictReader(csvfile)
        
        for row in data:
            status = row['Status']
            saldo=int(row['Saldo'])
            email=row['Email']
            emailpet="viriansyah.0906@gmail.com"
            if PlatNo == row['PlatNo'] and status == '' or PlatNo == row['PlatNo'] and status =='Keluar':
                status="Masuk"
                Keterangan="Berhasil Masuk"
                print ("Sisa Saldo saat ini = %d" % saldo)
                message = "Kendaraan Dengan Plat No %s Berhasil Masuk Dan Sisa Saldo Saat ini = %d" % (PlatNo,saldo)
                display_lcd_masuk(status,PlatNo,saldo)
                mail_image(file,email,PlatNo,saldo,message)
                send_log_masuk(PlatNo,nourut,Keterangan)
                update_saldo(PlatNo,saldo,status)
                break
            elif PlatNo == row['PlatNo'] and status =='Masuk':
                if saldo<=tarif:
                    saldo=saldo-tarif
                    print("Tarif Tol =",tarif)
                    print("sisa saldo =",saldo)
                    status="Keluar"
                    Keterangan="Berhasil Keluar"
                    display_lcd_keluar(PlatNo,tarif,saldo)
                    message = "Kendaraan Dengan Plat No %s Berhasil Keluar Dan Sisa Saldo Saat ini = %d" % (PlatNo,saldo)
                    mail_image(file,email,PlatNo,saldo,message)
                    send_log_masuk(PlatNo,nourut,Keterangan)
                    send_log_saldo(PlatNo,nourut)
                    update_saldo(PlatNo,saldo,status)
                elif saldo>=tarif:
                    saldo=saldo-tarif
                    print("Tarif Tol =",tarif)
                    print("sisa saldo =",saldo)
                    status="Keluar"
                    Keterangan="Berhasil Keluar"
                    display_lcd_keluar(PlatNo,tarif,saldo)
                    message = "Kendaraan Dengan Plat No %s Berhasil Keluar Dan Sisa Saldo Saat ini = %d" % (PlatNo,saldo)
                    mail_image(file,email,PlatNo,saldo,message)
                    send_log_masuk(PlatNo,nourut,Keterangan)
                    update_saldo(PlatNo,saldo,status)
                    break
                break
        if PlatNo != row['PlatNo']:
            print ("Plat Anda Tidak Terdaftar")
            message = "Kendaraan Dengan Plat No %s \nTidak Ditemukan" % PlatNo
            display_lcd_pelanggar(PlatNo)
            mail_image(file,emailpet,PlatNo,saldo,message)
            send_log_pelanggaran(PlatNo,nourut)
        display_lcd_welcome()

def send_log_masuk(PlatNo,nourut,message):
    f = open('LOG_Kendaraan.csv', 'a')
    writer = csv.writer(f, lineterminator='\n')
    writer.writerow([nourut,PlatNo,message])
    f.close()
    
def send_log_keluar(PlatNo,nourut):
    f = open('LOG_Kendaraan.csv', 'a')
    writer = csv.writer(f, lineterminator='\n')
    writer.writerow([nourut,PlatNo,"Berhasil Keluar"])
    f.close()
    
def send_log_pelanggaran(PlatNo,nourut):
    f = open('LOG_Kendaraan_Pelanggar.csv', 'a')
    writer = csv.writer(f, lineterminator='\n')
    writer.writerow([nourut,PlatNo,"Tidak Ditemukan Pada DataBase"])
    f.close()
    
def send_log_saldo(PlatNo,nourut):
    f = open('LOG_Kendaraan_Pelanggar.csv', 'a')
    writer = csv.writer(f, lineterminator='\n')
    writer.writerow([nourut,PlatNo,"Saldo Tidak Mencukupi"])
    f.close()
    
def update_saldo(PlatNo,nominal,status):
    f = open('DB_Kendaraan.csv', 'r')
    reader=csv.reader(f)
    L=[]
    found=False
    for row in reader:
        if row[1]==PlatNo:
            found=True
            Stream=nominal
            Status=status
            row[2]=Status
            row[3]=Stream
        L.append(row)
    f.close()
    
    if found==False:
        print('Plat No Tidak Ditemukan')
    else:
        f=open('DB_Kendaraan.csv','w+',newline='')
        writer=csv.writer(f)
        writer.writerows(L)
        f.seek(0)
        f.close
        
def mail_image(file,toaddr,PlatNo,saldo,message):
    print ("sending mail")
    fromaddr = "tugasakhir0906@gmail.com"
    body = message
    
    msg = MIMEMultipart()
    msg['From'] = fromaddr
    msg['To'] = toaddr
    msg['Subject'] = "Invoice"
    msg.attach(MIMEText(body, 'plain'))
 
    filename = ".jpg"
    attachment = open("/home/pi/Project_TA/ANPR_KNN/Sample_Image/test%d.jpg" % file, "rb" )
 
    part = MIMEBase('application', 'octet-stream')
    part.set_payload((attachment).read())
    encoders.encode_base64(part)
    part.add_header('Content-Disposition', "attachment; filename= %s" % filename)
 
    msg.attach(part)
 
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(fromaddr, "hzkrefsynluchdhb")
    text = msg.as_string()
    server.sendmail(fromaddr, toaddr, text)
    server.quit()
    
def display_lcd_masuk(status,PlatNo,saldo):
    lcd = CharLCD('PCF8574', 0x27)
    lcd.cursor_pos = (0, 0)
    lcd.write_string('------GATE IN-------')
    lcd.cursor_pos = (1, 0)
    lcd.write_string('Status\t: %s' % status)
    lcd.cursor_pos = (2, 0)
    lcd.write_string('Plat No\t: %s' % PlatNo)
    lcd.cursor_pos = (3, 0)
    lcd.write_string('Sisa Saldo\t: %d' % saldo)
    sleep(2.5)
    
def display_lcd_keluar(PlatNo,tarif,saldo):
    lcd = CharLCD('PCF8574', 0x27)
    lcd.cursor_pos = (0, 0)
    lcd.write_string('------GATE OUT------')
    lcd.cursor_pos = (1, 0)
    lcd.write_string('Plat No\t: %s' % PlatNo)
    lcd.cursor_pos = (2, 0)
    lcd.write_string('Tarif Tol\t: %d' % tarif)
    lcd.cursor_pos = (3, 0)
    lcd.write_string('Sisa Saldo\t: %d' % saldo)
    sleep(2.5)
    
def display_lcd_pelanggar(PlatNo):
    lcd = CharLCD('PCF8574', 0x27)
    lcd.cursor_pos = (0, 0)
    lcd.write_string('------GATE IN-------')
    lcd.cursor_pos = (1, 0)
    lcd.write_string('Plat No\t: %s' % PlatNo)
    lcd.cursor_pos = (2, 0)
    lcd.write_string('Anda Tidak Terdaftar')
    lcd.cursor_pos = (3, 0)
    lcd.write_string('Daftarkan Segera')
    sleep(2.5)
    
def display_lcd_welcome():
    lcd = CharLCD('PCF8574', 0x27)
    lcd.cursor_pos = (0, 0)
    lcd.write_string('++++++++++++++++++++')
    lcd.cursor_pos = (1, 0)
    lcd.write_string('+    WELCOME TO    +')
    lcd.cursor_pos = (2, 0)
    lcd.write_string('+    TOL BANDUNG   +')
    lcd.cursor_pos = (3, 0)
    lcd.write_string('++++++++++++++++++++')
    #sleep(.8)
    
def proses(count):
    count_tampil=count-1
    blnKNNTrainingSuccessful = Hasil_Karakter.loadKNNDataAndTrainKNN()  

    if not blnKNNTrainingSuccessful: 
        print("\nerror: Pelatihan algoritma KNN tidak berhasil\n")  
        return

    imgOriginalS: None = cv2.imread("/home/pi/Project_TA/ANPR_KNN/Sample_Image/test%d.jpg"%count_tampil) 

    scale_percent = 100
    width = int(imgOriginalS.shape[1] * scale_percent / 100)
    height = int(imgOriginalS.shape[0] * scale_percent / 100)
    dimensi = (width, height)

    imgOriginalScene = cv2.resize(imgOriginalS, dimensi, interpolation=cv2.INTER_AREA)

    if imgOriginalScene is None: 
        print("\nerror: citra tidak terbaca \n\n")  
        os.system("pause")
        return

    listOfPossiblePlates = Hasil_Plat.detectPlatesInScene(imgOriginalScene)  
    listOfPossiblePlates = Hasil_Karakter.detectCharsInPlates(listOfPossiblePlates)  

    #cv2.imshow("Citra Plat Original", imgOriginalScene)  

    if len(listOfPossiblePlates) == 0:  
        print("\nTidak ada nomor plat yang terdeteksi\n")
        main(count)
    else:
        listOfPossiblePlates.sort(key=lambda possiblePlate: len(possiblePlate.strChars), reverse=True)

        licPlate = listOfPossiblePlates[0]

        #cv2.imshow("Citra Plat", licPlate.imgPlate)
        #cv2.imshow("Citra Threshold", licPlate.imgThresh)

        if len(licPlate.strChars) == 0:  
            print("\nTidak ada karakter yang terdeteksi\n\n")
            main(count)
            return

        drawRedRectangleAroundPlate(imgOriginalScene, licPlate)
        print("--------------------")
        print("Plat Nomor = " + licPlate.strChars)
        
        writeLicensePlateCharsOnImage(imgOriginalScene, licPlate)
        
        read_database(count_tampil,licPlate.strChars,count_tampil)
        
        print("--------------------")
        #kirim_data(licPlate.strChars)

        #cv2.imshow("Citra Plat Hasil", imgOriginalScene)

        cv2.imwrite("/home/pi/Project_TA/ANPR_KNN/Hasil_Image/Hasil%d.jpg"%count_tampil, imgOriginalScene)
        #count+=1
        
        main(count)
        
        cv2.waitKey(0)
        
    return

def drawRedRectangleAroundPlate(imgOriginalScene, licPlate):
    p2fRectPoints = cv2.boxPoints(licPlate.rrLocationOfPlateInScene)  
    cv2.line(imgOriginalScene, tuple(p2fRectPoints[0]), tuple(p2fRectPoints[1]), SCALAR_RED, 5)
    cv2.line(imgOriginalScene, tuple(p2fRectPoints[1]), tuple(p2fRectPoints[2]), SCALAR_RED, 5)
    cv2.line(imgOriginalScene, tuple(p2fRectPoints[2]), tuple(p2fRectPoints[3]), SCALAR_RED, 5)
    cv2.line(imgOriginalScene, tuple(p2fRectPoints[3]), tuple(p2fRectPoints[0]), SCALAR_RED, 5)

def writeLicensePlateCharsOnImage(imgOriginalScene, licPlate):
    ptCenterOfTextAreaX = 0
    ptCenterOfTextAreaY = 0

    ptLowerLeftTextOriginX = 0
    ptLowerLeftTextOriginY = 0

    sceneHeight, sceneWidth, sceneNumChannels = imgOriginalScene.shape
    plateHeight, plateWidth, plateNumChannels = licPlate.imgPlate.shape

    intFontFace = cv2.FONT_HERSHEY_SIMPLEX  
    fltFontScale = float(plateHeight) / 55.0
    intFontThickness = int(round(fltFontScale * 2))

    textSize, baseline = cv2.getTextSize(licPlate.strChars, intFontFace, fltFontScale, intFontThickness)

    ((intPlateCenterX, intPlateCenterY), (intPlateWidth, intPlateHeight), fltCorrectionAngleInDeg) = licPlate.rrLocationOfPlateInScene

    intPlateCenterX = int(intPlateCenterX)
    intPlateCenterY = int(intPlateCenterY)

    ptCenterOfTextAreaX = int(intPlateCenterX)

    if intPlateCenterY < (sceneHeight * 0.75):  
        ptCenterOfTextAreaY = int(round(intPlateCenterY)) + int(
            round(plateHeight * 0.7))  
        ptCenterOfTextAreaY = int(round(intPlateCenterY)) - int(
            round(plateHeight * 0.7))

    textSizeWidth, textSizeHeight = textSize

    ptLowerLeftTextOriginX = int(ptCenterOfTextAreaX - (textSizeWidth / 2))
    ptLowerLeftTextOriginY = int(ptCenterOfTextAreaY + (textSizeHeight / 2))

    cv2.putText(imgOriginalScene, licPlate.strChars, (ptLowerLeftTextOriginX, ptLowerLeftTextOriginY), intFontFace, fltFontScale, SCALAR_GREEN, intFontThickness)
    
if __name__ == "__main__":
#     countfile()
#     trigger_sens()
    display_lcd_welcome()
    count = count_file(0)
    main(count)
#     monitoring()
#     count_id(jumlah)

