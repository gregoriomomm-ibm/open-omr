#!/usr/bin/python3

# Using flask to make an api 
# import necessary libraries and functions 
import io
import numpy as np
import argparse
import imutils
import cv2
import statistics as st
import sys
import os
from flask import Flask, flash, request, redirect, url_for, jsonify, send_file, abort
from werkzeug.utils import secure_filename
from pyzbar import pyzbar
from imutils.perspective import four_point_transform
from imutils import contours
from collections import namedtuple
from flask_swagger import swagger
from flask_cors import CORS, cross_origin
from swagger_ui import flask_api_doc
from omr import parseImageInfo

# creating a Flask api 
api = Flask(__name__) 
cors = CORS(api)
api.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024
api.config['CORS_HEADERS'] = 'Content-Type'
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])


flask_api_doc(api, config_url='/api/omr/openapi.json', url_prefix='/doc/omr', title='OMR Grader doc')

@api.route('/api/omr/openapi.json')
@cross_origin()
def spec():
    swag = swagger(api)
    swag['info']['version'] = "1.0"
    swag['info']['title'] = "OMR-grader"
    return jsonify(swag)

# A simple function to calculate the square of a number 
# the number to be squared is sent in the URL when we use GET 
# on the terminal type: curl http://127.0.0.1:5000 / home / 10 
# this returns 100 (square of 10) 
# curl -X POST -F 'image=@./images/test-09.jpg ' http://127.0.0.1:5000/omr/parseType/dialogos/1000
@api.route('/api/omr/parseType/<string:form>/<int:id>', methods = ['POST']) 
def getParsedType(form,id):
    """ en=Analyzes a questionnarie image according to the template (Ie: /omr/getTemplate/dialogos) pt-br=Analiza uma imagem de um questionário de acordo com o modelo (Ex: /omr/getTemplate/dialogos)
        ---
        tags:
          - omr
        consumes:
         - multipart/form-data
        parameters:
          - in: path
            name: form
            type: string
            description:  en=The name of the form; pt-br=O nome do formulário.
            required: true
          - in: path
            name: id
            type: integer
            description: json / image - en=The response type expected; pt-br=O tipo de resposta esperado.
            required: true
          - in: formData
            name: formImage
            type: file
            description: en=The image to be analyzed; pt-br= A imagem a ser analizada.
            required: true
          - in: formData
            name: responseType
            type: string
            description: json / image - en=The response type expected; pt-br=O tipo de resposta esperado.
            required: false
          - in: formData
            name: nQuestions
            type: integer
            description: en=The number of questions; pt-br= O número de questões, default 6.
            required: false
          - in: formData
            name: nAnswers
            type: integer
            description: en=The number of answers; pt-br= O número de respostas, default 7.
            required: false        
        responses:
          200:
            description: en=Return the answers as json text or image; pt-br=Retorna as respostas em formato json. [(q,a),...] ou imagem 
            schema:
                type: object
                properties:
                    answers: 
                        items:
                            items:
                                type: integer
                            type: array
                        type: array
                example: "{ 'answers': [[1, 7], [2, 5], [3, 6], [4, 7], [5, 6], [6, 5]]}"

    """
    responseType = request.form['responseType']

    if isinstance(responseType, type(None)):
        responseType='image'

    # Treat image
    imageReturn, answers, elapsedTime = parseInfo(request, form, id)
    

    if isinstance(answers, type(None)):
        print('No answers')

    if responseType.strip().lower() == 'json':
        if isinstance(elapsedTime, type(None)):
            return jsonify({"answers": answers})
        else:
            return jsonify({"answers": answers, "elapsedTimeImage":elapsedTime})


    if isinstance(imageReturn, type(None)):
        print('No image')
        abort(404)

    if isinstance( imageReturn , type(None)):
        print(f'As questões não puderam ser capturadas por essa foto, tente deixá-la mais paralela à camera.')
        return 'As questões não puderam ser capturadas por essa foto, tente deixá-la mais paralela à camera.', 404

    warped = imutils.resize(imageReturn, height=300)
    data = cv2.imencode('.jpg', warped)[1].tobytes()    

    return send_file (io.BytesIO(data),
                    attachment_filename='result.jpeg',
                    mimetype='image/jpg')

# A simple function to calculate the square of a number 
# the number to be squared is sent in the URL when we use GET 
# on the terminal type: curl http://127.0.0.1:5000 / omr / getTemplate / Name
@api.route('/api/omr/getTemplate/<string:form>', methods = ['GET']) 
def getTemplate(form):
    """ en=Get the template Word document used as base for the questionnaire; pt-br=Obtém o documento word de modelo usado como base do questionário.
        ---
        tags:
          - omr
        parameters:
          - in: path
            name: form
            type: string
            description:  en=The name of the form; pt-br=O nome do formulário.
            required: true

        responses:
          200:
            description: en= Return the form template; pt-br= Retorna um modelo de formulário. 
    """
    templateFilename="template/template.docx"

    return send_file(templateFilename,
                     attachment_filename='template.docx',
                     mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document')

@api.route('/api/omr/parseJSON/<string:form>/<int:id>', methods = ['POST']) 
def getParsedJson(form, id):
    """ en=Analyzes a questionnarie image according to the template (Ie: /omr/getTemplate/dialogos); pt-br:Analiza uma imagem de um questionário de acordo com o modelo (Ex: /omr/getTemplate/dialogos).
        ---
        tags:
          - omr
        consumes:
         - multipart/form-data
        parameters:
          - in: path
            name: form
            type: string
            description:  en=The name of the form; pt-br=O nome do formulário.
            required: true
          - in: path
            name: id
            type: integer
            description: json / image - en=The response type expected; pt-br=O tipo de resposta esperado.
            required: true
          - in: query
            name: nQuestions
            type: integer
            description: en= The number of questions; pt-br= O número de questões, default 6.
            required: false
          - in: query
            name: nAnswers
            type: integer
            description: en= The number of answers; pt-br= O número de respostas, default 7.  
            required: false  
          - in: formData
            name: formImage
            type: file
            description: en= The image to be analyzed; pt-br= A imagem a ser analizada.
            required: true
          - in: formData
            name: responseType
            type: string
            description: json / image - en=The response type expected; pt-br=O tipo de resposta esperado.
            required: false

        responses:
          200:
            description: en=Return the answers as json text or image; pt-br=Retorna as respostas em formato json. [(q,a),...] ou imagem 
            schema:
                type: object
                properties:
                    answers: 
                        items:
                            items:
                                type: integer
                            type: array
                        type: array
                example: "{ 'answers': [[1, 7], [2, 5], [3, 6], [4, 7], [5, 6], [6, 5]]}"
    """
    # Treat image
    imageReturn, answers, elapsedTime = parseInfo(request, form, id)

    if isinstance(answers, type(None)):
        return redirect('/') # (request.url)

    # use this in production
    # for a in answers:
    #    print(f"question_no:{a[0]} a:{a[1]}")     
    return jsonify({"answers": answers})


# general parameter parse function
# that treat the files and send image
# to get read, returning both image and json
# answers
def parseInfo(req, form, id): 
    # Answer Key
    # each question has 7 possible answers, to loop over the
    # question in batches of 7
    nAnswers = 7
    nQuestions = 6

    if isinstance(req, type(None)):
        print("Sem arquivo selecionado.")
        return redirect(request.url)

    myFiles = None
    try:
        myFiles = request.files
    except:
        print("Not adequated.")
        return redirect(request.url)   

    if isinstance(myFiles, type(None)):
        print("Sem arquivo selecionado.")
        return redirect(request.url)   

    # check if the post request has the file part
    if 'formImage' not in request.files:
        print("sem arquivo.")
        return redirect(request.url)


    try:
       frmQuestions = request.form['nQuestions']
       nQuestions = int(frmQuestions)
    except:
       try:
          frmQuestions =  request.args.get('nQuestions')
          nQuestions = int(frmQuestions)
       except:           
          pass

    try:
       
       frmAnswers = request.form['nAnswers']
       nAnswers = int(frmAnswers)
    except:
       try:
          frmAnswers =  request.args.get('nAnswers')
          nAnswers = int(frmAnswers)
       except:           
          pass

    file = request.files['formImage']

    # if user does not select file, browser also
    # submit an empty part without filename
    if file.filename == '':
        print("Sem arquivo selecionado.")
        return redirect(request.url)
    if file and allowed_file(file.filename):
        
        print("Verificando nome do arquivo:" + file.filename)        
        filename = secure_filename(file.filename)
        print("Arquivo selecionado:" + file.filename)
        imageName = filename.split('/')[-1]           
        #read image file string data
        filestr = file.read()
        #convert string data to numpy array
        npimg = np.frombuffer(filestr, np.uint8)
        # convert numpy array to image
        orig = cv2.imdecode(npimg, cv2.IMREAD_UNCHANGED )

        return parseImageInfo(orig, nQuestions, nAnswers, imageName)

    print("Arquivo invalido.")
    return None, None, None 

def bound_rect_area(bra_contour):
    (_, _, bra_w, bra_h) = cv2.boundingRect(bra_contour)
    return bra_w * bra_h


def xytable(contour, minx, miny, maxx):
    (x, y, w, h) = cv2.boundingRect(contour)
    n = ( int((x - minx)/50) + 10) + ( int((y - miny)/50) + 10) * maxx 
    return n


def parseImageInfo(orig, nQuestions, nAnswers, imageName):
        
    try:        
        Point = namedtuple('Point', ['x', 'y'])

        image = orig.copy()

        # gray it
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        gray = imutils.resize(gray, height = 800) 
        ratio = image.shape[0]/gray.shape[0]

        # blur it
        gray = cv2.GaussianBlur(gray, (5, 5), 0)

        # canny edge detection
        edged = cv2.Canny(gray, 20, 50)

        dilated = cv2.dilate(edged, np.ones((5, 5)))
        eroded = cv2.erode(dilated, np.ones((5, 5)))

        # Find the contours
        (contours, _) = cv2.findContours(eroded.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        sorted_contour = sorted(contours, key=cv2.contourArea, reverse=True)
        c = sorted_contour[0]

        # compute the rotated bounding box of the largest contour
        c = c.astype("float")
        c *= ratio
        c = c.astype("int")

        rect = cv2.minAreaRect(c)
        box = np.int0(cv2.boxPoints(rect))

        # apply the four point tranform to obtain a "birds eye view" of
        # the image
        warped = four_point_transform(image, box)
        height, width, channels = warped.shape
        ratio = 1

        if height > width:
            warped = imutils.rotate_bound(warped, 90)
        
        height, width, channels = warped.shape
        final_width = width
        (qch, qcw ) = (height, width)
        origgray = qcgray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        qcgray = cv2.bilateralFilter(qcgray,7,240,255)
        orig = qcgray
        qcgray = imutils.resize(origgray, height=2000)
        ratio = qcgray.shape[0] / float(origgray.shape[0])           
        barcodes = pyzbar.decode(qcgray, symbols=[pyzbar.ZBarSymbol.QRCODE ] )
        qcgray = origgray
        (qch, qcw ) = qcgray.shape 
      
        if len(barcodes) == 0:
            qcgray = cv2.adaptiveThreshold(qcgray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 7, 2)
            barcodes = pyzbar.decode(qcgray, symbols=[pyzbar.ZBarSymbol.QRCODE ] )


        point2 = Point(150,700) 
        point4 = Point(1200,300)

        barcodeData = "not found"
        barcodeType = "not found"

        upsideDown = False 
        # loop over the detected barcodes
        for barcode in barcodes:
            # extract the bounding box location of the barcode and draw the
            # bounding box surrounding the barcode on the image
            (x, y, w, h) = barcode.rect 
            x = int(x / ratio)
            y = int(y / ratio)
            w = int(w / ratio)
            h = int(h / ratio)
            
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 0, 255), 2)
            point = barcode.polygon[0]
            point2 = barcode.polygon[1]
            point4 = barcode.polygon[3]
            pos = 0

            point = Point( int(point.x / ratio), int(point.y / ratio))
            point2 = Point( int(point2.x / ratio), int(point2.y / ratio))
            point4 = Point( int(point4.x / ratio), int(point4.y / ratio))

            upsideDown = ((float(point.x)/qcw) > 0.5) 
            if upsideDown:
                point2 = Point( max(qcw - point4.x, 0), max(qch - point4.y, 0))
            
            # the barcode data is a bytes object so if we want to draw it on
            # our output image we need to convert it to a string first
            barcodeData = barcode.data.decode("utf-8")
            barcodeType = barcode.type
        
            # print the barcode type and data to the terminal
            print(f"[INFO] Encontrado {barcodeType} barcode: {barcodeData}")

        if upsideDown:
            warped = imutils.rotate_bound(warped, 180)

        ratio = 1 
        if warped.shape[0] < 1600: 
            nwarped = imutils.resize(warped, height=1600)
            ratio = nwarped.shape[0]/warped.shape[0]
            warped = nwarped
        (wh, ww, _ )= warped.shape

        cv2.imwrite(f'test/output/warped-{imageName}', warped)

        point2 = Point( max(int(point2.x * ratio), 0),\
                        max(int(point2.y * ratio) , 0) )
        cropped = warped[point2.y:int(wh * ratio), point2.x:int(ww * ratio)]

        cv2.imwrite(f'test/output/warped-{imageName}', warped)

        lab=cv2.cvtColor(cropped, cv2.COLOR_BGR2LAB)

        #-----Splitting the LAB image to different channels-------------------------
        l, a, b = cv2.split(lab)

        #-----Applying CLAHE to L-channel-------------------------------------------
        clahe = cv2.createCLAHE(clipLimit=1.0, tileGridSize=(8,8))
        cl = clahe.apply(l)

        #-----Merge the CLAHE enhanced L-channel with the a and b channel-----------
        limg = cv2.merge((cl,a,b))

        #-----Converting image from LAB Color model to RGB model--------------------
        final = cv2.cvtColor(limg, cv2.COLOR_LAB2BGR)

        warped = final[int(wh*0.030):int(wh),int(0.006*ww):ww-int(0.006*ww)]

        gray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        gray = cv2.bilateralFilter(gray,7,240,255)

        gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)
        (_, gray) = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)

        gray = cv2.erode(gray, np.ones((3, 3)))
        gray = cv2.dilate(gray, np.ones((3, 3)))

        """
        # Vertical Filtering ******************************************
        vertical = np.copy(gray)

        # [vert]
        # Specify size on vertical axis
        rows = vertical.shape[0]
        verticalsize = rows // 20
        # Create structure element for extracting vertical lines through morphology operations
        verticalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (3, verticalsize))
        # Apply morphology operations
        vertical = cv2.erode(vertical, verticalStructure)
        vertical = cv2.dilate(vertical, verticalStructure)

        vertical = cv2.dilate(vertical, np.ones((1,9)))

        (_, vertical) = cv2.threshold(vertical, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)


        # Horizontal Filtering ******************************************
        horizontal = np.copy(gray)
        # [vert]
        # Specify size on vertical axis
        cols = horizontal.shape[1]
        horizontal_size  = cols // 20
        # Create structure element for extracting horizontal lines through morphology operations
        horizontalStructure = cv2.getStructuringElement(cv2.MORPH_RECT, (horizontal_size, 1))
        # Apply morphology operations
        horizontal = cv2.erode(horizontal, horizontalStructure)
        horizontal = cv2.dilate(horizontal, horizontalStructure)

        # Inverse vertical image
        vertical_inv = cv2.bitwise_not(vertical)
        minusvertical = cv2.bitwise_and(gray, gray, mask=vertical_inv)

        horizontal_inv =  cv2.bitwise_not(horizontal)
        minushorizontal = cv2.bitwise_and(minusvertical, minusvertical, mask=horizontal_inv)

        gray = minushorizontal.copy()
        # ********************************************************************
        """

        (contours, _) = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        answerCnts = []

        (th, tw) = gray.shape

        ct=0

        xs = []
        ys = []
        hs = []
        ws = []

        # loop over the contours
        for c in contours:
            # compute the bounding box of the contour, then use the
            # bounding box to derive the aspect ratio
            (x, y, w, h) = cv2.boundingRect(c)

            ar = w / float(h)
            
            circh = ( float(h) / th )
            circw = ( float(w) / tw )

            # in order to label the contour as a question, region
            # should be sufficiently wide, sufficiently tall, and
            # have an aspect ratio approximately equal to 1
            if  0.035 <= circw <= 0.075 and 0.08 <= circh <= 0.14:                
                if 0.75 <= ar <= 1.25:
                    ct += 1
                    xs.append(x)
                    ys.append(y)
                    hs.append(h)
                    ws.append(w)
                    answerCnts.append(c)

        minx = min(xs)
        miny = min(ys)
        maxx = max(xs)
        maxy = max(ys)

        answerCnts = sorted(answerCnts, key=lambda contour: xytable(contour, minx, miny, maxx) )
        nAnswerCnts = len(answerCnts)

        modeH = int(st.median_grouped(hs))
        modeW = int(st.median_grouped(ws))
                    
        wSpace = ( maxx - minx ) / (nAnswers - 1)
        hSpace = ( maxy - miny ) / (nQuestions - 1)

        tbx = minx
        tby = miny
        tbw = ( maxx - minx ) + modeW
        tbh = ( maxy - miny ) + modeH      
                
        # apply the four point tranform to obtain a "birds eye view" of
        # the image

        threshes = []
        ct = 0 
        w = modeW
        h = modeH
        radius_thresh = int(w * 0.3)
        aQuestions = []          
        for q in range(nQuestions):
            y = int(round(miny + (q * hSpace),0))
            acy = y
            acx = int(round(minx + (0 * wSpace),0))
            aAnswers = [] 
            aQuestions.append(aAnswers)
            for a in range(nAnswers):
                x = int(round(minx + (a * wSpace),0))
                
                if ct < nAnswerCnts:
                    ac = answerCnts[ct]
                (ax, ay, aw, ah) = cv2.boundingRect(ac)
                cah = int(ax+(aw/2))
                cav = int(ay+(ah/2))
                
                center, radius = ((cah, cav), int((aw/2)*1.05))
                cv2.putText(warped,  f"{ct+1}", (int(ax), int(ay)), \
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)  

                if acx < cah < acx + w and acy < cav < acy + h:
                   center, radius = ((cah, cav), int((aw/2)*1.05))
                   acx = int(ax)
                   acy = int(ay)
                   ptText = (int(acx+w*0.15), int(acy+(3*h/5)))
                   acx += int(wSpace)
                   ct+=1 
                else:
                   cah = int(acx+(w/2))
                   cav = int(acy+(h/2))                     
                   center, radius = ((cah, cav), int((w/2)*1.05))
                   ptText = (int(acx+w*0.15), int(acy+(3*h/5)))
                   acx += int(wSpace)

                aAnswers.append((center,radius,ptText))
                cv2.circle(warped, center, int(radius), (255, 0, 0), 2) 

                mask2 = np.zeros(gray.shape, dtype='uint8')
                cv2.circle(mask2, center, int(radius_thresh), 255, -1) 


                mask2 = cv2.bitwise_and(gray, gray, mask=mask2)
                total2 = cv2.countNonZero(mask2)
                
                if total2 > 0 :
                    threshes.append(total2)
            

        if len(threshes) > 0 :             
            bubbled_thresh = int(0.4 * max(threshes))
        else:
            bubbled_thresh = 100

        answers = []
        bubbles = [] 
        iq = 0
        for q in aQuestions:
            iq += 1
            ia = 0
            for a in q:
                ia += 1
                center, radius, ptText = a
                mask = np.zeros(gray.shape, dtype='uint8')                
                cv2.circle(mask, center, int(radius_thresh), 255, -1) 
                
                # apply the mask to the thresholded image, then
                # count the number of non-zero pixels in the
                # bubble area
                mask = cv2.bitwise_and(gray, gray, mask=mask)
                total = cv2.countNonZero(mask)
                    
                if total >= bubbled_thresh:
                    bubbles.append((bubbled_thresh, iq, ia, center))
                    cv2.putText(warped,  f"{iq},{ia}", ptText, \
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 3)  
                    cv2.circle(warped, center, int(radius), (0, 255, 0), 6)
                    answers.append((iq, ia))
            

        # draw the barcode data and barcode type on the image
        text = "{} ({})".format(barcodeData, barcodeType)        
        font =  cv2.FONT_HERSHEY_SIMPLEX
        fontScale = 0.5
        thickness = 2

        # get the width and height of the text box
        (text_width, text_height) = cv2.getTextSize(text, font, fontScale=fontScale, thickness=thickness)[0]

        # set the text start position
        text_offset_x = 10
        text_offset_y = 40
        rectangle_bgr = (255, 255, 255)

        # make the coords of the box with a small padding of two pixels
        box_coords = ((text_offset_x, text_offset_y + 10 ), (text_offset_x + text_width , text_offset_y - text_height - 10 ))
        cv2.rectangle(warped, box_coords[0], box_coords[1], rectangle_bgr, cv2.FILLED)
        cv2.putText(warped, text, (text_offset_x, text_offset_y), font, fontScale=fontScale, color=(255, 0, 0), thickness=thickness)

        return warped, answers 

    except:
        print("Unexpected error:", sys.exc_info()[0])
        return None, None

# on the terminal type: curl http://127.0.0.1:5000/ 
# returns hello world when we use GET. 
# returns the data that we send when we use POST. 
@api.route('/', methods = ['GET']) 
def home(): 
    return 
    '''
        <!doctype html>
        <title>Envie uma foto para avaliação</title>
        <head>
            <script> 
            //vars 
            var  timing ;
            var  increment = 100; 
            var  timepass = 0;
            var  maxtime = 20000;
            var  fnTimeout ;

            function update(timepass) { 

                val = ("00" + Math.floor(timepass / 1000)).slice(-2)
                val = val + "." 
                val = val + ("000" +  (timepass % 1000)).slice(-3)
                
                timing.value = val
                if (timepass == 0 ) { 
                    timing.style.color="black" 
                } else if (timepass > maxtime ){
                    timing.style.color="red" 
                }
            } 
    
            function countup() { 
                timepass = timepass + increment; 
                update(timepass)  
            } 

            function reset() { 
                timepass = 0; 
                update(timepass)  
            } 

            //start function is evoked when form is submit 
            function start() { 
                if (document.getElementById) { 
                    timing = document.getElementById("timing"); 
                }
                reset()
                fnTimeout = setInterval('countup()', increment); 
            } 

            //stop function is evoked when form is loaded
            function stop() { 
                clearInterval(fnTimeout);                
            } 

            </script> 
        </head> 
        <div class="holder-logo" valign=middle >
            <a href="/" class="logo-banner">
                <svg  width="70" height="70" version="1.0" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 3400 2700" preserveAspectRatio="xMidYMid meet" >
                    <g id="layer101">
                        <path d="M1410 2283 c-162 -225 -328 -455 -370 -513 -422 -579 -473 -654 -486 -715 -7 -33 -50 -247 -94 -475 -44 -228 -88 -448 -96 -488 -9 -40 -14 -75 -11 -78 2 -3 87 85 188 196 165 180 189 202 231 215 25 7 129 34 230 60 100 26 184 48 185 49 4 4 43 197 43 212 0 10 -7 13 -22 9 -13 -3 -106 -25 -208 -49 -102 -25 -201 -47 -221 -51 l-37 -7 8 42 c4 23 12 45 16 49 5 4 114 32 243 62 129 30 240 59 246 66 10 10 30 132 22 139 -1 2 -110 -24 -241 -57 -131 -33 -240 -58 -242 -56 -6 6 13 98 22 107 5 4 135 40 289 80 239 61 284 75 307 98 14 15 83 90 153 167 70 77 132 140 139 140 7 0 70 -63 141 -140 70 -77 137 -150 150 -163 17 -19 81 -39 310 -97 159 -41 292 -78 296 -82 8 -9 29 -106 24 -111 -1 -2 -112 24 -245 58 -134 33 -245 58 -248 56 -6 -7 16 -128 25 -136 5 -4 112 -30 238 -59 127 -29 237 -54 246 -57 11 -3 20 -23 27 -57 6 -28 9 -53 8 -54 -1 -1 -38 7 -81 17 -274 66 -379 90 -395 90 -16 0 -16 -6 3 -102 11 -57 21 -104 22 -106 1 -1 96 -27 211 -57 115 -31 220 -60 234 -66 14 -6 104 -101 200 -211 95 -111 175 -197 177 -192 1 5 -40 249 -91 542 l-94 532 -145 203 c-220 309 -446 627 -732 1030 -143 201 -265 366 -271 367 -6 0 -143 -183 -304 -407z m10 -819 l-91 -161 -209 -52 c-115 -29 -214 -51 -219 -49 -6 1 32 55 84 118 l95 115 213 101 c116 55 213 98 215 94 1 -3 -38 -78 -88 -166z m691 77 l214 -99 102 -123 c56 -68 100 -125 99 -127 -4 -3 -435 106 -447 114 -4 2 -37 59 -74 126 -38 68 -79 142 -93 166 -13 23 -22 42 -20 42 2 0 101 -44 219 -99z"/>
                        <path d="M1126 2474 c-198 -79 -361 -146 -363 -147 -2 -3 -70 -410 -133 -805 -12 -73 -20 -137 -18 -143 2 -6 26 23 54 63 27 40 224 320 437 622 213 302 386 550 385 551 -2 2 -165 -62 -362 -141z"/>
                        <path d="M1982 2549 c25 -35 159 -230 298 -434 139 -203 283 -413 319 -465 37 -52 93 -134 125 -182 59 -87 83 -109 73 -65 -5 20 -50 263 -138 747 -17 91 -36 170 -42 176 -9 8 -571 246 -661 280 -14 6 -7 -10 26 -57z"/>
                        <path d="M1679 1291 c-8 -11 -71 -80 -141 -153 l-127 -134 -95 -439 c-52 -242 -92 -442 -90 -445 6 -5 38 28 218 223 l99 107 154 0 c85 0 163 -4 173 -10 10 -5 78 -79 151 -162 73 -84 136 -157 140 -162 18 -21 18 4 -2 85 -11 46 -58 248 -105 448 l-84 364 -87 96 c-108 121 -183 201 -187 201 -2 0 -10 -9 -17 -19z m96 -488 c33 -102 59 -189 57 -192 -2 -6 -244 -2 -251 4 -5 6 120 375 127 375 4 0 34 -84 67 -187z"/>
                    </g>
                </svg>
            </a>            
            <form action="/api/omr/getTemplate/dialogos" method=get >
            Documento modelo: <input type=submit value="Obtenha o modelo">
            <a href="/doc/omr?url=/api/omr/openapi.json">Especificação da api.</a>
            </form>        
        </div>
        <HR>        
        <p>Envie uma foto para avaliação</p>
        <table border=1 width="100%" >
        <tr>
        <td>
        <P style="font-size:12px;" ><b>Versão de testes 1.0:</b></p>
        <P style="font-size:12px;" >1. Quanto maior a foto, maior o tempo para realizar o envio e processamento da imagem, ainda faltam otimizações, portanto pode demorar um pouco o processamento</P>     
        <P style="font-size:12px;" >2. Os testes foram realizados com cerca de 10 imagens de tamanhos similares, podem ocorrer erros no tratamento dessas imagens</P>     
        <P style="font-size:12px;" >3. Procure manter a camera paralela ao papel, mas evite diferenças de luz com sombra</P>    
        </td>
        </tr>
        <tr><td style="font-size:12px;" width="350" align="left" valign="top">
        <form action="/api/omr/parseType/dialogos/1000" onsubmit="start()" method=post enctype="multipart/form-data" target="result">        
        <p  style="font-size:12px;">Tipo de resposta:
        <select name="responseType" >
            <option selected value="image">Imagem</option>
            <option value="json">Json</option>
        </select>
        </p>
        <BR>
        <input style="font-size:12px;" type=file name=formImage class="filepond" accept-br:"image/*;capture=camera" >      
        <input style="font-size:12px;" type=submit value=Upload>
        <p style="font-size:12px;" >Time => 
        <input id="timing" type="text" value="--.---" style="width: 60px; 
                        border: none; font-size: 16px; 
                        font-weight: bold; color: black;">segundos
        </p>
        </form>
        </td>
        <tr>
        <td colspan=2 width="100%" >
           <iframe onload="stop()"  src="" name="result" id="result" frameborder=0 width="100%" height=450>
               <p>iframes are not supported by your browser.</p>
           </iframe>
        </td>        
        </tr>
        </table>
    '''

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS




###############################################################################
#   MAIN
###############################################################################
if __name__ == '__main__':

    # If you pass a input file (see -i), you will process a image locally
    # If not it will start Flask application so you can at the given port (defaul to 5000)
    # and local ipAddresses binding (defaul 0.0.0.0 it will bind to all ip interfaces)
    # you can access at your browser (Example http://localhost:5000 or the given ip and port)
    # it will bring a very simple for to be used as test, or you can directly at the api routes

    # Answer Key
    # each question has 7 possible answers, to loop over the
    # question in batches of 7
    nAnswers = 7
    nQuestions = 6

    # construct the argument parser
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", required=False,
                    help="path to the input image",default="")
    ap.add_argument("-H", "--host", required=False,
                    help="host address",default="0.0.0.0")
    ap.add_argument("-P", "--port", required=False,
                    help="listening port",default="5000")
    ap.add_argument("-D", "--debug", required=False,
                    help="Debug mode",default="False")
    ap.add_argument("-o", "--output", required=False,
                    help="path to the output folder", default="test/output")
    ap.add_argument("-Q", "--questions", required=False,
                    help="Number of questions (lines)",default="6")
    ap.add_argument("-A", "--answers", required=False,
                    help="Number of answers (colunms)",default="7")
    ap.add_argument("-C", "--certfile", required=False,
                    help="Certificate file",default="")
    ap.add_argument("-K", "--keyfile", required=False,
                    help="Key file",default="")


    args = vars(ap.parse_args())
    image_path = args['image']

    sQuestions = args['questions']
    sAnswers = args['answers']

    if not (isinstance(sQuestions, type(None)) or sQuestions == ''):
        try:
            nQuestions = int(sQuestions)
        except:
            pass

    if not (isinstance(sAnswers, type(None)) or sAnswers == ''):
        try:
            nAnswers = int(sAnswers)
        except:
            pass

    certfile = args['certfile']
    keyfile = args['keyfile']
    if isinstance(image_path, type(None)) or image_path == '':
        # driver function 
        port = int(args['port'])
        if port <= 1024:
            print(f"Port has to be greater than 1024 for this service.")
            port = 5000

        debugParam = False
        debugArg = args['debug']
        if ( args['debug'].strip().lower() != 'false'):
            debugParam = True
        
        host = args['host']
        if not (isinstance(certfile, type(None)) or certfile == '' or isinstance(keyfile, type(None)) or keyfile == ''):            
            api.run(host=args['host'] ,port=int(port), debug = debugParam, certfile=certfile, keyfile=keyfile ) 
        else:
            api.run(host=host,port=int(port), debug = debugParam) 

        print(' after run')
        sys.exit(0)

    imageName = image_path.split('/')[-1]   
    # load the image
    orig = cv2.imread(image_path)

    if isinstance( orig , type(None)):
        print(f'Foto não encontrada.')
        sys.exit(1)

    image = orig.copy()
    imageReturn, answers, elapsedTime = parseImageInfo(image, nQuestions, nAnswers, imageName)

    if isinstance( answers , type(None)):
        print(f'As questões não puderam ser capturadas por essa foto, tente deixá-la mais paralela à camera.')
    else:
        # use this in production
        for a in answers:
            print(f"question_no:{a[0]} a:{a[1]}")

        output_folder = args['output']
        if not output_folder.endswith('/'):
            output_folder = output_folder + '/'
        output_image = output_folder + imageName

        # print('Saving Image to', output_image)
        directory = os.path.dirname(output_image)

        try:
            # comment it out in production
            os.stat(directory)
        except:
            os.mkdir(directory)

        cv2.imwrite(output_image, imageReturn)
