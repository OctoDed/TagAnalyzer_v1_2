FROM ubuntu
RUN apt-get update -y
RUN apt-get upgrade -y
RUN apt-get install git -y
RUN git clone https:github.com/OctoDed/TagAnalyzer_v1_2.git
RUN cd TagAnalyzer_v1_2/Django_server/
RUN git checkout SergeyDav
RUN apt-get install python3-pip -y
RUN pip3 install django
RUN pip3 install djangorestframework
RUN pip install opencv-python
RUN apt-get install python3-opencv
RUN pip3 install easyocr
RUN pip3 install pyzbar
RUN apt-get install zbar-tools
RUN pip3 install matplotlib
RUN pip3 install tqdm
RUN pip3 install tensorflow
RUN pip3 install sklearn
RUN pip3 install keras_ocr
RUN pip3 install IPython
RUN pip3 install Crypto
RUN pip3 install pycryptodome
RUN apt-get install snapd
RUN snap install ngrok
RUN pip3 install zeep
RUN wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/cuda-ubuntu2004.pin
RUN mv cuda-ubuntu2004.pin /etc/apt/preferences.d/cuda-repository-pin-600 && sudo apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/7fa2af80.pub
RUN sudo add-apt-repository "deb https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2004/x86_64/ /"
RUN apt-get update && sudo apt-get install -y nvidia-kernel-source-460
RUN apt-get -y install cuda
RUN pip3 install opencv-python-headless==4.5.4.60

