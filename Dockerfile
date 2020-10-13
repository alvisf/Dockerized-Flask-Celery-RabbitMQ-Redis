FROM python:latest

# add requirements.txt to the image
ADD requirements.txt /app/requirements.txt

# set working directory to /app/
WORKDIR /app/

# install python dependencies
RUN pip install -r requirements.txt

RUN pip install Pillow

# create unprivileged user
RUN adduser --disabled-password --gecos '' app  

