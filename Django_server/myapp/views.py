from hashlib import new
from django.http import HttpResponseRedirect, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.http import JsonResponse
from .forms import UploadFileForm
from django.views.decorators.csrf import csrf_exempt
import os
import json
#импорт сети
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
import re

from Crypto.Cipher import AES
import base64
from base64 import b64encode

@csrf_exempt 
def upload_file(request):
    #try:
        up_file = request.FILES['picture']
        path = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/content/' + up_file.name
        if os.path.exists(path):
            os.remove(path)
        destination = open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/content/' + up_file.name, 'xb+')
        for chunk in up_file.chunks():
            destination.write(chunk)
        destination.close()
        #os.system("python3 /home/sergey/GPO/for_django_3-0/content/YOLO_EasyOCR.py")
        
        #result = {'success': True, 'description': 'test', 'price': 12}
        result = new_fun(path, up_file.name)
        return JsonResponse(result)
    #except Exception:
    #    return HttpResponseBadRequest()
    
def new_fun(path, filename):
    #file = open(path)
    reader = easyocr.Reader(['ru','en']) # need to run only once to load model into memory
    # демонстрация работы
    sdescriptions = []
    sbarcodes = []
    sprice11 = []
    sprice12 = []
    sprice21 = []
    sprice22 = []
    #os.system("cd /home/pavel/TagAnalyzer-main/Django_server/")
    os.system("./content/darknet/darknet detector test ./content/data/obj.data ./content/data/yolov4-tiny-3l.cfg ./content/data/backup/yolov4-tiny-3l_fine_tuned.weights " + '"' + path + '"' + " -dont_show -ext_output | tee pred.txt")
    #print(path)
    #print(filename)
    #print("./content/darknet/darknet detector test ./content/data/obj.data ./content/data/yolov4-tiny-3l.cfg ./content/data/backup/yolov4-tiny-3l_fine_tuned.weights " + '"' + path + '"' + " -dont_show -ext_output | tee pred.txt")
    #filename = "photo(6).jpg"
    a_file = open("pred.txt", "r")
    lines = a_file.readlines()
    a_file.close()
    last_lines = [line for line in lines if ('width' in line and 'height' in line and 'left_x' in line)]
    #clear_output()
    img = cv2.imread("./content/"+filename)
    #tuple(img.shape[1::-1])
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
            w = img.shape[1]
            #w = 511
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
        if (x > img.shape[1]): x=img.shape[1]
        if (y > img.shape[0]): y=img.shape[0]
        if (w > img.shape[1]): w=img.shape[1]
        if (h > img.shape[0]): h=img.shape[0]
        y2 = y+h
        x2 = x+w
        if (y2 > img.shape[0]): y2 =img.shape[0]
        if (x2 > img.shape[1]): x2 =img.shape[1]
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
    os.remove("./"+filename[:-4]+".txt")
    
    #restxt = open('./content/res.txt', 'w')
    text = ""
    for img in sdescriptions:
        result = reader.readtext(img)
        
        for box in result:
            text = text + " " + box[1]
        
        #restxt.write(text + '\n')
        #print(text)
    description_test = text
    text = ""
    for img in sprice11:
        #print(reader.readtext(img, allowlist='1234567890', detail = 0))
        #restxt.write(str(reader.readtext(img, allowlist='1234567890', detail = 0))+ '\n')
        result = reader.readtext(img, allowlist='1234567890')
        for box in result:
            #text = text + " " + box[1]
            text = text + box[1]
        #restxt.write(text + '\n')
    price11_test = text
    text = ""
    for img in sprice12:
        #print(reader.readtext(img, allowlist='1234567890', detail = 0))
        #restxt.write(reader.readtext(img, allowlist='1234567890', detail = 0)+ '\n')
        result = reader.readtext(img, allowlist='1234567890')
        for box in result:
            #text = text + " " + box[1]
            text = text + box[1]
        #restxt.write(text + '\n')
    price12_test = text
    text = ""
    for img in sprice22:
        #print(reader.readtext(img, allowlist='1234567890', detail = 0))
        #restxt.write(reader.readtext(img, allowlist='1234567890', detail = 0)+ '\n')
        result = reader.readtext(img, allowlist='1234567890')
        for box in result:
            #text = text + " " + box[1]
            text = text + box[1]
        #restxt.write(text + '\n')
    price21_test = text
    text = ""
    for img in sprice21:
        #print(reader.readtext(img, allowlist='1234567890', detail = 0))
        #restxt.write(reader.readtext(img, allowlist='1234567890', detail = 0)+ '\n')
        result = reader.readtext(img, allowlist='1234567890')
        for box in result:
            #text = text + " " + box[1]
            text = text + box[1]
        #restxt.write(text + '\n')
    price22_test = text
    data = ""
    for img in sbarcodes:
        decoded_objects = decode(img)
        for obj in decoded_objects:
            # draw the barcode
        #
            #restxt.write("Type:" + obj.type + '\n')
            #restxt.write("Data:" + obj.data + '\n')
            #restxt.write("test")
            data = str(obj.data)
            #type = obj.type
        #print("Type:", obj.type)
        #print("Data:", obj.data)
        
    #restxt.close()
    #price_per_num = []
    #price_per_num.append(str(Price_per_Num(description_test, price11_test, price12_test, price21_test, price22_test)[0]))
    #price_per_num.append(str(Price_per_Num(description_test, price11_test, price12_test, price21_test, price22_test)[1]))
    #price_per_num.append(str(Price_per_Num(description_test, price11_test, price12_test, price21_test, price22_test)[2]))
    
    price_num_card = str(Price_per_Num(description_test, price11_test, price12_test, price21_test, price22_test)[0])
    price_num_nocard = str(Price_per_Num(description_test, price11_test, price12_test, price21_test, price22_test)[1])
    price_Type = str(Price_per_Num(description_test, price11_test, price12_test, price21_test, price22_test)[2])
    #result = {'success': True, 'description': encrypt(description_test), 'price11': encrypt(price11_test), 'price12': encrypt(price12_test), 'price21': encrypt(price21_test), 'price22': encrypt(price22_test), 'barcode_data': encrypt(data) }
    result = {'success': True, 'description': description_test, 'price11': price11_test, 'price12': price12_test, 'price21': price21_test, 'price22': price22_test, 'barcode_data': data, 'price_num_card': price_num_card, 'price_num_nocard': price_num_nocard , 'Type': price_Type }
    os.system("rm " + path)
    print(result)
    return result
    
def pad(byte_array):
    BLOCK_SIZE = 16
    pad_len = BLOCK_SIZE - len(byte_array) % BLOCK_SIZE
    return byte_array + (bytes([pad_len]) * pad_len)
    
def unpad(byte_array):
    last_byte = byte_array[-1]
    return byte_array[0:-last_byte]
    
def encrypt(message1):
    iv = b'This is a key123'
    key = 'This is a key123'
    byte_array = message1.encode("UTF-8")
    padded = pad(byte_array)
    obj = AES.new(key.encode("UTF-8"), AES.MODE_CBC,iv)
    ciphertext1 = obj.encrypt(padded)
    ct1 = base64.b64encode(ciphertext1).decode("UTF-8")
    return ct1
    
#def Price_per_Num(descryption, price11, price12, price21, price22):
#    x = {'O':0, 'S':5, 'Z':2,'О':0,'б':6,'З':3}
#    prices_per_num = []
#    price_card = float(price11 + '.' + price12)
#    price_nocard = float(price21 + '.' + price22)
#    result2=re.findall(r'(?:(?:\d*\.{1})|(?:\d+\+))?\d+\s*(?:мл|шт|гр|L|литр(?:а|ов)?|кг|мг|г|пар(?:а|ы)?|пак|ш|Л|л)+', multiple_replace(descryption,x))
#    if len(result2)!=0:
#             #print(result2)
#         #print('Число:',get_num_of_type(result2[0]), 'Единица:', get_type(result2[0]))
#         num = get_num_of_type(result2[0])
#         Type = get_type(result2[0])
#         prices_per_num.append(str(price_card/num))
#         prices_per_num.append(str(price_nocard/num))
#         prices_per_num.append(Type)
#    else:
#         print("no metric")

def Price_per_Num(descryption, price11, price12, price21, price22):
    x = {'O':0, 'S':5, 'Z':2,'О':0,'б':6,'З':3}
    prices_per_num = []
    price_nocard = float(price11 + '.' + price21)
    price_card = float(price22 + '.' + price12)
    result2=re.findall(r'(?:(?:\d*\.{1})|(?:\d+\+))?\d+\s*(?:мл|шт|гр|L|литр(?:а|ов)?|кг|мг|г|пар(?:а|ы)?|пак|ш|Л|л)+', multiple_replace(descryption,x))
    if len(result2)!=0:
         num=get_num_of_type(result2[-1])
         Type = ''.join(get_type(result2[-1])[len(get_type(result2[-1]))-1])

         if len(num)!=1:
          num1=0
          for i in num:
            num1=num1+int(i)
         else:
          try: 
            num1=int(num[0])
          except Exception:
            num1=float(num[0])
         print("num " + str(num1))
         print("Type " + str(Type))
         print("price_card " + str(price_card))
         print("price_nocard " + str(price_nocard))
         print(descryption)
         print(str(result2))
         prices_per_num.append(str(round(price_card/num1, 4)))
         prices_per_num.append(str(round(price_nocard/num1, 4)))
         prices_per_num.append(str(Type))
         
         print("card " + str(prices_per_num[0]))
         print("nocard " + str(prices_per_num[1]))
         print("ctype " + str(prices_per_num[2]))
         return (prices_per_num)
                 
    else:
         prices_per_num.append("no metric")
         prices_per_num.append("no metric")
         prices_per_num.append("no metric")
         return (prices_per_num)

def get_num_of_type(string_to_split):
    return(re.findall(r'(?:\d*\.{1})?\d+\s*', string_to_split))

def get_type(string_to_split):
    return(re.findall(r'(?:мл|шт|гр|L|литр(?:а|ов)?|кг|мг|г|пар(?:а|ы)?|пак|ш|Л)+', string_to_split))
    
def multiple_replace(target_str, replace_values):
    for key in replace_values.keys():
      target_str = target_str.replace(key, str(replace_values[key]))
    return target_str
