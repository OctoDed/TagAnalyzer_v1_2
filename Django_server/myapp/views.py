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
from PIL import Image
from Crypto.Cipher import AES
import base64
from .brom import *
from base64 import b64encode
from .Python1c import *
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

@csrf_exempt 
def upload_file(request):
    up_file = request.FILES['picture']
    pathToPhoto = os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/content/' + up_file.name
    if os.path.exists(pathToPhoto):
            os.remove(pathToPhoto)
    destination = open(os.path.dirname(os.path.dirname(os.path.abspath(__file__))) + '/content/' + up_file.name, 'xb+')
    for chunk in up_file.chunks():
        destination.write(chunk)
    destination.close()
    
    result = new_fun(pathToPhoto, up_file.name)
    return JsonResponse(result)

def convertFindedToTrain(size, box):
    dw = 1./size[0]
    dh = 1./size[1]
    x = (box[0] + box[1])/2.0
    y = (box[2] + box[3])/2.0
    w = box[1] - box[0]
    h = box[3] - box[2]
    x = x*dw
    w = w*dw
    y = y*dh
    h = h*dh
    return (x,y,w,h)

def new_fun(pathToPhoto, photoName):
    reader = easyocr.Reader(['ru','en']) # need to run only once to load model into memory
    # демонстрация работы
    description = []
    barcode = []
    priceRubNoCard = []
    priceKop = []
    priceKopNoCard = []
    priceRub = []
    photoForTraining = Image.open(pathToPhoto)
    width, height = photoForTraining.size
    os.system("./content/darknet/darknet detector test ./content/data/obj.data ./content/data/yolov4-tiny-3l.cfg " + 
    "./content/data/backup/yolov4-tiny-3l_best.weights " + '"' + pathToPhoto + '"' + " -dont_show -ext_output | tee pred.txt")
    predTxt = open("pred.txt", "r")
    lines = predTxt.readlines()
    predTxt.close()
    last_lines = [line for line in lines if ('width' in line and 'height' in line and 'left_x' in line)]
    clear_output()
    img = cv2.imread("./content/"+photoName)
    res = []

    f = open(photoName[:-4]+".txt", "w")
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
            h = h + 10
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
        if box['class'] == 'description': f.write("0 "+str(convertFindedToTrain((width, height),(x,x+w,y,y+h)))[1:-1]+"\n")
        if box['class'] == 'barcode': f.write("1 "+str(convertFindedToTrain((width, height),(x,x+w,y,y+h)))[1:-1]+"\n")
        if box['class'] == 'price11': f.write("2 "+str(convertFindedToTrain((width, height),(x,x+w,y,y+h)))[1:-1]+"\n")
        if box['class'] == 'price12': f.write("5 "+str(convertFindedToTrain((width, height),(x,x+w,y,y+h)))[1:-1]+"\n") #по итогу сранения 3 и 5 поменял местами
        if box['class'] == 'price21': f.write("4 "+str(convertFindedToTrain((width, height),(x,x+w,y,y+h)))[1:-1]+"\n")
        if box['class'] == 'price22': f.write("3 "+str(convertFindedToTrain((width, height),(x,x+w,y,y+h)))[1:-1]+"\n")
        crop_img = img[y:y+h, x:x+w]
        apps = {
                'description':description.append,
                'barcode':barcode.append,
                'price11':priceRubNoCard.append,
                'price12':priceKop.append,
                'price21':priceKopNoCard.append,
                'price22':priceRub.append
                }
        apps[box['class']](crop_img)
    #os.remove("pred.txt")
    file1 = open(photoName[:-4]+"1.txt", "w")
    for line in last_lines:
        file1.write(line)
    file1.close()
    #os.remove("./predictions.jpg")
    os.remove("./"+photoName[:-4]+"1.txt") #файл координат
    f.close()
    #restxt = open('./content/res.txt', 'w')
    answer = ""
    for img in description:
        result = reader.readtext(img)
        for box in result:
            answer = answer + " " + box[1]
    descriptionAnswer = answer
    answer = ""
    for img in priceRubNoCard:
        result = reader.readtext(img, allowlist='1234567890')
        for box in result:
            answer = answer + box[1]
    priceRubNoCardAnswer = answer
    answer = ""
    for img in priceKop:
        result = reader.readtext(img, allowlist='1234567890')
        for box in result:
            answer = answer + box[1]
    priceKopAnswer = answer
    answer = ""
    for img in priceRub:
        result = reader.readtext(img, allowlist='1234567890')
        for box in result:
            answer = answer + box[1]
    priceKopNoCardAnswer = answer
    answer = ""
    for img in priceKopNoCard:
        result = reader.readtext(img, allowlist='1234567890')
        for box in result:
            answer = answer + box[1]
    priceRubAnswer = answer
    barcodeData = ""
    for img in barcode:
        decoded_objects = decode(img)
        for obj in decoded_objects:
            barcodeData = str(obj.data)
    price_num_card = str(PricePerNum(descriptionAnswer, priceRubNoCardAnswer, priceKopAnswer, priceKopNoCardAnswer, priceRubAnswer)[0])
    price_num_nocard = str(PricePerNum(descriptionAnswer, priceRubNoCardAnswer, priceKopAnswer, priceKopNoCardAnswer, priceRubAnswer)[1])
    price_Type = str(PricePerNum(descriptionAnswer, priceRubNoCardAnswer, priceKopAnswer, priceKopNoCardAnswer, priceRubAnswer)[2])
    try:
        numType = str(PricePerNum(descriptionAnswer, priceRubNoCardAnswer, priceKopAnswer, priceKopNoCardAnswer, priceRubAnswer)[3])
    except (Exception):
        numType = 'None found'
    #result = {'success': True, 'description': encrypt(descriptionAnswer), 'price11': encrypt(priceRubNoCardAnswer), 'price12': encrypt(priceKopAnswer), 'price21': encrypt(priceKopNoCardAnswer), 'price22': encrypt(priceRubAnswer), 'barcode_data': encrypt(data) }
    result = {'success': False, 'description': descriptionAnswer, 'price11': priceRubNoCardAnswer, 
    'price12': priceKopAnswer, 'price21': priceKopNoCardAnswer, 'price22': priceRubAnswer, 'barcode_data': barcodeData,
    'price_num_card': price_num_card, 'price_num_nocard': price_num_nocard , 'type': price_Type, 'numType': numType,
    'price1c': 'None', 'description1c': 'None', 'price1cDiscount': 'None', 'Levi': 'None' }
    result = take_barcodes(result) #вызов метода, для связи с базой данных 1С
    result['Levi']=fuzz.WRatio(result['description'],result['description1c']) #вычисление расстояния Левенштейна
    print(result)
    return result

#шифрование
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

#вычисление цены за единицу
def PricePerNum(descryption, price11, price12, price21, price22):
    #словарь для замены букв в предложении на похожие цифры
    dictLetterToNum = {'O':0, 'S':5, 'Б':5, 'Z':2,'О':0,'б':6,'З':3, ' ': '', 'А':4, 'A':4 }
    prices_per_num = []
    #регулярка, которая ищет цену в названии товара, предварительно буквы заменяются на цифры в соответствии со словарём,
    #из названиря убираются все пробелы
    priceValues=re.findall(
        r'(?:(?:\d*\.{1})|(?:\d+\+)+)?\d+\s*(?:мл|шт|гр|L|литр(?:а|ов)?|кг|мг|г|пар(?:а|ы)?|пак|ш|Л|л)+', 
        replaceLetterToNum(descryption,dictLetterToNum)
    )
    if len(priceValues)!=0: #определил хотя бы одну пару число/единица измерения
        num=getNumOfType(priceValues[-1]) #берём последнее значение из списка для цены
        type = getType(priceValues[-1]) #берём последнее значение для единицы
        #type = ''.join(getType(priceValues[-1])[len(getType(priceValues[-1]))-1]) #wtf?
        #обработка маркетологов 2+1
        try: #если нашлась строка с плюсом, то делим и получаем значения из него, формируем новый список с ними
            num=str(num[-1]).split('+')
        except (Exception): #может исключения и не возникает но на всякий случай я сделал отлов
            print("Faker")
        if len(num)!=1: #если нашлось несколько значений (2+1 etc), т.е. результат разделения выше
            finalNum=0 #начальная сумма 0
            for i in num:
                finalNum=finalNum+int(i) #суммируем
        else: #значение всего одно, его и берём (если это десятичное число, то переводим в него)
            try: 
                finalNum=int(num[0])
            except Exception:
                finalNum=float(num[0])
        #вычисление значений цен
        try:
            priceNoCard = float(price11 + '.' + price21)
            priceCard = float(price22 + '.' + price12)
            prices_per_num.append(str(round(priceCard/finalNum, 4))) #цена по карте/единица
            prices_per_num.append(str(round(priceNoCard/finalNum, 4))) #цена без карты/единица
            prices_per_num.append(str(type)) #единицы измерения
            prices_per_num.append(str(priceValues[-1])) #цена вместе с единицей
        except (Exception): #при делении на ноль осознаём, что нейронка ошиблась и пишем, что метрики не найдены
            for i in range(1,4):
                prices_per_num.append("no metric")
        return (prices_per_num)
                 
    else: #нейронка не нашла читаемых единиц, пишем, что метрики не найдены
        for i in range(1,4):
                prices_per_num.append("no metric")
        return (prices_per_num)

def getNumOfType(targetString):
    return(re.findall(r'(?:(?:\d*\.{1})|(?:\d+\+)+)?\d+', targetString))

def getType(targetString):
    return(re.findall(r'(?:мл|шт|гр|L|литр(?:а|ов)?|кг|мг|г|пар(?:а|ы)?|пак|ш|Л|л)+', targetString))
    
def replaceLetterToNum(targetString, replace_values):
    for key in replace_values.keys():
      targetString = targetString.replace(key, str(replace_values[key]))
    return targetString
