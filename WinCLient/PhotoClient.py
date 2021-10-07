from tkinter import *
import json
import os
from pathlib import Path
from pip._vendor import requests
from tkinter import filedialog
from tkinter import scrolledtext  
from tkinter.filedialog import askopenfilename
from PIL import ImageTk, Image
from tkinter import filedialog


def clicked():  
    global url 
    url = txt.get()
    print(url)

def ChosePicture():  
    global filename
    filename1 = askopenfilename()
    filename2 = Path(filename1).resolve()
    filename =str(filename2)

    img = Image.open(filename2)
    img = img.resize((250, 250), Image.ANTIALIAS)
    img = ImageTk.PhotoImage(img)
    #img = ImageTk.PhotoImage(Image.open(filename2))
    
    picture = Label(window, image = img)
    picture.grid(column=2, row=5)
    picture.image = img
    #picture.configure(image=img1)
    window.update()

def magic():
    txt1.delete(1.0, END)
    files = {
    'picture': open(filename, 'rb')
    }
    r = requests.post(url,  files=files)
    r.headers
    returned_data = r.json()
    txt1.insert(INSERT, "Описание: " + returned_data.get("description") + "\nРубли без карты: " + returned_data.get("price11") +
    "\nКопейки без карты: " + returned_data.get("price21") + 
    "\nРубли по карте: " + returned_data.get("price22") + "\nКопейки по карте: " + returned_data.get("price12") +
    "\nЦена за единицу по карте: " + returned_data.get("price_num_card") + "\nЦена за единицу без карты: " + returned_data.get("price_num_nocard") + 
    "\nТип единицы: " + returned_data.get("type") + "\nЕдиницы вместе с ценой: " + returned_data.get("numType"))
    
    #img1=PhotoImage(file='tmp.png')
    #picture = Label(window, image=img1)
    #picture.grid(column=2, row=5)
    #picture.configure(image=img1)
    #window.update()

window = Tk()
window.title("Отдыхаем от телефонов")
window.geometry('800x600')
lbl = Label(window, text="Ip")  
lbl.grid(column=0, row=0) 
txt = Entry(window, width=40)
txt.grid(column=1, row=0)
btn = Button(window, text="Клик!", command=clicked)  
btn.grid(column=2, row=0) 
btn1 = Button(window, text="Выбрать картинку", command=ChosePicture)  
btn1.grid(column=1, row=4) 
txt1 = scrolledtext.ScrolledText(window,width=60,height=30)
txt1.grid(column=1, row=5) 
btn1 = Button(window, text="Магия", command=magic)  
btn1.grid(column=2, row=4) 
##картинка
#img = PhotoImage(file="coconut.png")      
#picture = Label(window, image=img)
#picture.grid(column=2, row=5)
window.mainloop()