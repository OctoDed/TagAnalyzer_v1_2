import shutil
import os
import cv2
import easyocr
from pyzbar.pyzbar import decode
import matplotlib.pyplot as plt
import zipfile
import datetime
import string
import glob
import math
import random
import tqdm
import matplotlib.pyplot as plt
import tensorflow as tf
import sklearn.model_selection
import keras_ocr
from IPython.display import clear_output 

#reader = easyocr.Reader(['ru','en']) # need to run only once to load model into memory

# демонстрация работы
sdescriptions = []
sbarcodes = []
sprice11 = []
sprice12 = []
sprice21 = []
sprice22 = []
#os.system("./darknet/darknet detector test ./data/obj.data ./data/yolov4-tiny-3l.cfg ./data/backup/yolov4-tiny-3l_fine_tuned.weights " +'"./test1.jpg"'+" -dont_show -ext_output | tee pred.txt")
os.system("/home/sergey/GPO/for_django_3-0/content/darknet/darknet detector test /home/sergey/GPO/for_django_3-0/content/data/obj.data /home/sergey/GPO/for_django_3-0/content/data/yolov4-tiny-3l.cfg /home/sergey/GPO/for_django_3-0/content/data/backup/yolov4-tiny-3l_fine_tuned.weights " + '"./test1.jpg"' + " -dont_show -ext_output | tee pred.txt")
filename = "photo(6).jpg"
a_file = open("pred.txt", "r")
lines = a_file.readlines()
a_file.close()
last_lines = [line for line in lines if ('width' in line and 'height' in line and 'left_x' in line)]
clear_output()
img = cv2.imread("./data/obj/"+filename)
res = []
for line in last_lines:
  spl = line.split()
  cords = {"class":spl[0][:-1], "conf_value":spl[1][:-1], "left_x":int(spl[3]), "top_y":int(spl[5]), 'width':int(spl[7]), 'height':int(spl[9][:-1])}
  res.append(cords)
for box in res:
  x = box['left_x']
  y = box['top_y']
  w = box['width']
  h = box['height']
  if box['class'] == 'description': 
    x = 0
    w = 511
  if box['class'] == 'barcode':
    x = x - 15
    w = w + 30
  if (box['class'] == 'price11'):
    x = x - 5
    w = w + 10
    h = h + 10
    y = y - 5
  if (box['class'] == 'price12'):
    x = x - 7
    w = w + 12
    h = h + 10
    y = y - 5
  if (box['class'] == 'price21'):
    x = x - 2
    w = w + 4
    h = h + 4
    y = y - 2
  if (box['class'] == 'price22'):
    x = x - 3
    w = w + 6
    h = h + 6
    y = y - 3
  if (x < 0): x=0
  if (y < 0): y=0
  if (w < 0): w=0
  if (h < 0): h=0
  if (x > 511): x=511
  if (y > 511): y=511
  if (w > 511): w=511
  if (h > 511): h=511
  y2 = y+h
  x2 = x+w
  if (y2 > 511): y2 =511
  if (x2 > 511): x2 =511
  if (y > y2): y = y2
  if (x > x2): x = x2
  crop_img = img[y:y+h, x:x+w]
  apps = {
          'description':sdescriptions.append,
          'barcode':sbarcodes.append,
          'price11':sprice11.append,
          'price12':sprice12.append,
          'price21':sprice21.append,
          'price22':sprice22.append
        }
  apps[box['class']](crop_img)
os.remove("pred.txt")
f = open(filename[:-4]+".txt", "w")
for line in last_lines:
  f.write(line)
f.close()
#os.remove("./predictions.jpg")
#os.remove("./"+filename[:-4]+".txt")
for img in sdescriptions:
  result = reader.readtext(img)
  text = ""
  for box in result:
    text = text + " " + box[1]
  print(text)
for img in sprice11:
  print(reader.readtext(img, allowlist='1234567890', detail = 0))
for img in sprice12:
  print(reader.readtext(img, allowlist='1234567890', detail = 0))
for img in sprice22:
  print(reader.readtext(img, allowlist='1234567890', detail = 0))
for img in sprice21:
  print(reader.readtext(img, allowlist='1234567890', detail = 0))
for img in sbarcodes:
  decoded_objects = decode(img)
  for obj in decoded_objects:
        # draw the barcode
        print("Type:", obj.type)
        print("Data:", obj.data)
