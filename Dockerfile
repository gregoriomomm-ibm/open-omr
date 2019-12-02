FROM python:3.7-slim

LABEL maintainer="Gregorio Elias Roecker Momm (gregoriomomm@gmail.com)"

ARG BUILD_PACKAGES1="   \
    build-essential     \
    curl                \
    apt-utils           "

ARG BUILD_PACKAGES2="   \
    libzbar0            \
    zlib1g-dev          \
    libopencv-dev       \
    python-opencv       "

# && apt-get upgrade  -y \

RUN apt-get update \
 && apt-get install -y --no-install-recommends $BUILD_PACKAGES1 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* \
 && rm -rf /tmp/workdir/* 

RUN apt-get update \
 && apt-get install -y --no-install-recommends $BUILD_PACKAGES2 \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/* \
 && rm -rf /tmp/workdir/* 

RUN pip3 install --upgrade pip \
 && pip3 install numpy scipy setuptools 

RUN pip3 install opencv-python imutils pyzbar

RUN pip3 install aiohttp aiofiles

RUN pip3 install fastapi email-validator python-multipart

RUN pip3 install hypercorn 

RUN pip3 install hypercorn[uvloop]

RUN pip3 install secure

RUN mkdir -p /tmp/workdir
WORKDIR /tmp/workdir
 
#************************************************************************************************************************#
##########################################################################################################################
#************************************************************************************************************************#

# Add demo app
COPY ./app /app
WORKDIR /app

# Make /app/* available 
ENV PYTHONPATH=/app

# Run the start script provided by the parent image tiangolo/uwsgi-nginx.
# It will check for an /app/prestart.sh script (e.g. for migrations)
# And then will start Supervisor, which in turn will start Nginx and uWSGI

EXPOSE 5000

CMD ["/usr/local/bin/hypercorn","-w", "4", "-k", "uvloop", "-b", "0.0.0.0:5000","grader:api"]