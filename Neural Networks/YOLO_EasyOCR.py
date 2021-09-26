# -*- coding: utf-8 -*-
"""Копия блокнота "sams_fin"

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1YDwSo2W5j61zilOpVKdGwu-EPUeRm0Wv
"""

from IPython.display import clear_output

# Commented out IPython magic to ensure Python compatibility.
!pip install -U git+https://github.com/faustomorales/keras-ocr.git#egg=keras-ocr
!pip install -U 'opencv-python==4.5.1.48' # We need the most recent version of OpenCV.
!pip install easyocr
!sudo apt-get install libzbar0
!pip install pyzbar
# %tensorflow_version 2.x
clear_output()

!pip install pyzbar

import shutil
import os
import cv2
import easyocr
from pyzbar.pyzbar import decode
import matplotlib.pyplot as plt
from google.colab.patches import cv2_imshow
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
from google.colab import drive
import keras_ocr

tf.config.list_physical_devices('GPU')

# clone darknet repo
!git clone https://github.com/AlexeyAB/darknet

# Commented out IPython magic to ensure Python compatibility.
# change makefile to have GPU and OPENCV enabled
# %cd darknet
!sed -i 's/OPENCV=0/OPENCV=1/' Makefile
!sed -i 's/GPU=0/GPU=1/' Makefile
!sed -i 's/CUDNN=0/CUDNN=1/' Makefile

# verify CUDA
!/usr/local/cuda/bin/nvcc --version

# make darknet (build)
!make
clear_output()

# Commented out IPython magic to ensure Python compatibility.
# %cd /content

# dont forget to upload data.zip to /content via gui
# download url https://drive.google.com/file/d/1kGc4-lt51hNfn2McBqH1ydheBpoK3mLI/view?usp=sharing
# file structure
# /content------
#  |___/data----
#       |___/obj
#       |___ ....
#  |___/darknet-
#  |___data.zip

#%cd /content
!unzip data.zip -d /content/data 
clear_output()

# training from scratch / weights saved in /content/data/backup - best weights on validation and last weights from each n iterations
!./darknet/darknet detector train ./data/obj.data ./data/yolov4-tiny-3l.cfg ./data/yolov4-tiny.conv.29 -map -dont_show

# continue to train best
#!./darknet/darknet detector train ./data/obj.data ./data/yolov4-tiny-3l.cfg ./data/backup/yolov4-tiny-3l_last.weights -dont_show -map

# continue to train fine tuned
#!./darknet/darknet detector train ./data/obj.data ./data/yolov4-tiny-3l.cfg ./data/backup/yolov4-tiny-3l_fine_tuned.weights -dont_show -map

!rm -rf /content/data/results
!mkdir /content/data/results

descriptions = []
barcodes = []
price11 = []
price12 = []
price21 = []
price22 = []

# save results to /content/results
for filename in os.listdir("/content/data/obj"):
  if filename.endswith("jpg"):
    !./darknet/darknet detector test ./data/obj.data ./data/yolov4-tiny-3l.cfg ./data/backup/yolov4-tiny-3l_fine_tuned.weights "./data/obj/{filename}" -dont_show -ext_output | tee pred.txt
    a_file = open("pred.txt", "r")
    lines = a_file.readlines()
    a_file.close()
    last_lines = [line for line in lines if ('width' in line and 'height' in line and 'left_x' in line)]
    clear_output()
    img = cv2.imread("/content/data/obj/"+filename)
    cv2_imshow(img)
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
              'description':descriptions.append,
              'barcode':barcodes.append,
              'price11':price11.append,
              'price12':price12.append,
              'price21':price21.append,
              'price22':price22.append
             }
      cv2_imshow(crop_img)
      apps[box['class']](crop_img)

    os.remove("pred.txt")
    f = open(filename[:-4]+".txt", "w")
    for line in last_lines:
      f.write(line)
    f.close()
    shutil.move("/content/predictions.jpg", "/content/data/results/"+filename)
    shutil.move("/content/"+filename[:-4]+".txt", "/content/data/results/"+filename[:-4]+".txt")

import easyocr

reader = easyocr.Reader(['ru','en']) # need to run only once to load model into memory

for img in descriptions:
  cv2_imshow(img)
  result = reader.readtext(img)
  text = ""
  for box in result:
    text = text + " " + box[1]
  print(text)

for img in price11:
  cv2_imshow(img)
  #print(reader.readtext(img, allowlist='1234567890'))
  result = reader.readtext(img, allowlist='1234567890')
  text = ""
  for box in result:
    text = text + " " + box[1]
  print(text)

for img in price12:
  cv2_imshow(img)
  #print(reader.readtext(img, allowlist='1234567890'))
  result = reader.readtext(img, allowlist='1234567890')
  text = ""
  for box in result:
    text = text + " " + box[1]
  print(text)

for img in price21:
  cv2_imshow(img)
  #print(reader.readtext(img, allowlist='1234567890'))
  result = reader.readtext(img, allowlist='1234567890')
  text = ""
  for box in result:
    text = text + " " + box[1]
  print(text)

for img in price22:
  cv2_imshow(img)
  #print(reader.readtext(img, allowlist='1234567890'))
  result = reader.readtext(img, allowlist='1234567890')
  text = ""
  for box in result:
    text = text + " " + box[1]
  print(text)

for img in barcodes:
  cv2_imshow(img)
  decoded_objects = decode(img)
  for obj in decoded_objects:
        # draw the barcode
        #print("detected barcode:", obj)
        #image = draw_barcode(obj, img)
        # print barcode type & data
        print("Type:", obj.type)
        print("Data:", obj.data)
  #s = decode(img)
  #data = s.data
  print()
  #print(data)

# демонстрация работы
sdescriptions = []
sbarcodes = []
sprice11 = []
sprice12 = []
sprice21 = []
sprice22 = []
!./darknet/darknet detector test ./data/obj.data ./data/yolov4-tiny-3l.cfg ./data/backup/yolov4-tiny-3l_fine_tuned.weights "./data/obj/photo(6).jpg" -dont_show -ext_output | tee pred.txt
filename = "photo(6).jpg"
a_file = open("pred.txt", "r")
lines = a_file.readlines()
a_file.close()
last_lines = [line for line in lines if ('width' in line and 'height' in line and 'left_x' in line)]
clear_output()
img = cv2.imread("/content/data/obj/"+filename)
cv2_imshow(img)
cv2_imshow(cv2.imread("predictions.jpg"))
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
  cv2_imshow(crop_img)
  apps[box['class']](crop_img)
os.remove("pred.txt")
f = open(filename[:-4]+".txt", "w")
for line in last_lines:
  f.write(line)
f.close()
os.remove("/content/predictions.jpg")
os.remove("/content/"+filename[:-4]+".txt")
for img in sdescriptions:
  cv2_imshow(img)
  result = reader.readtext(img)
  text = ""
  for box in result:
    text = text + " " + box[1]
  print(text)
for img in sprice11:
  cv2_imshow(img)
  print(reader.readtext(img, allowlist='1234567890'))
for img in sprice12:
  cv2_imshow(img)
  print(reader.readtext(img, allowlist='1234567890'))
for img in sprice22:
  cv2_imshow(img)
  print(reader.readtext(img, allowlist='1234567890'))
for img in sprice21:
  cv2_imshow(img)
  print(reader.readtext(img, allowlist='1234567890'))
for img in sbarcodes:
  cv2_imshow(img)
  s = decode(img)
  print(s)

from google.colab import files
!zip -r /content/data.zip /content/data/
files.download('data.zip')
#clear_output()