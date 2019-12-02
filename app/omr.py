#!/usr/bin/python3

# Using Quart to make an api 
# import necessary libraries and functions 
import numpy as np
import imutils
import cv2
import statistics as st
import sys
from pyzbar import pyzbar
from imutils.perspective import four_point_transform
from imutils import contours
from collections import namedtuple
from time import perf_counter


def bound_rect_area(bra_contour):
    (_, _, bra_w, bra_h) = cv2.boundingRect(bra_contour)
    return bra_w * bra_h


def xytable(contour, minx, miny, maxx):
    (x, y, w, h) = cv2.boundingRect(contour)
    n = ( int((x - minx)/50) + 10) + ( int((y - miny)/50) + 10) * maxx 
    return n


def parseImageInfo(orig, nQuestions, nAnswers, imageName, numThreads = 4):

        print(f' Current number of threads: {cv2.getNumThreads()} ')
        cv2.setNumThreads(numThreads)
        print(f' Now number of threads: {cv2.getNumThreads()} ')
        # Start the stopwatch / counter 
        t1_start = perf_counter()  

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

        upsideDown = False 

        origgray = qcgray = cv2.cvtColor(warped, cv2.COLOR_BGR2GRAY)
        qcgray = cv2.bilateralFilter(qcgray,7,240,255)
        orig = qcgray
        qcgray = imutils.resize(origgray, height=2000)
        ratio = qcgray.shape[0] / float(origgray.shape[0])           

        (cropmh,cropmw) = qcgray.shape

        cropx = 100
        cropy = 600
        cropw = 650
        croph = 1200
        
        crop = qcgray[cropy:croph, cropx:cropw]
        barcodes = pyzbar.decode(crop, symbols=[pyzbar.ZBarSymbol.QRCODE ] )

        if len(barcodes)==0:
            crop2x = cropmw - cropw
            crop2y = cropmh - croph
            crop2w = cropmw - cropx
            crop2h = cropmh - cropy
            
            crop2 = qcgray[crop2y:crop2h, crop2x:crop2w]
            barcodes = pyzbar.decode(crop2, symbols=[pyzbar.ZBarSymbol.QRCODE ] )
            upsideDown = len(barcodes)>0 
        
        if len(barcodes)==0:
            cropx = 0
            cropy = 0
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

        # loop over the detected barcodes
        if len(barcodes)>0 :
            barcode = barcodes[0]
            # extract the bounding box location of the barcode and draw the
            # bounding box surrounding the barcode on the image

            point2 = barcode.polygon[1]
            point4 = barcode.polygon[3]
            if cropx == 0:
                point = barcode.polygon[0]
                pos = 0

                point = Point( int(point.x / ratio), int(point.y / ratio))
                point2 = Point( int(point2.x / ratio), int(point2.y / ratio))
                point4 = Point( int(point4.x / ratio), int(point4.y / ratio))
                upsideDown = ((float(point.x)/qcw) > 0.5) 
                if upsideDown:
                    point2 = Point( max(qcw - point4.x, 0), max(qch - point4.y, 0))
            else:            
                if upsideDown:
                    point4 = Point( int((point4.x + cropmw - cropw) / ratio), 
                                    int((point4.y + cropmh - croph)/ ratio))
                    point2 = Point( max(qcw - point4.x, 0), max(qch - point4.y, 0))
                else:
                    point2 = Point( int((cropx + point2.x) / ratio), int((cropy + point2.y) / ratio))

            # the barcode data is a bytes object so if we want to draw it on
            # our output image we need to convert it to a string first
            barcodeData = barcode.data.decode("utf-8")
            barcodeType = barcode.type
        
            # print the barcode type and data to the termina            
            print(f"[INFO] Encontrado {barcodeType} barcode: {barcodeData}")

        if upsideDown:
            warped = imutils.rotate_bound(warped, 180)

        ratio = 1 
        if warped.shape[0] < 1600: 
            nwarped = imutils.resize(warped, height=1600)
            ratio = nwarped.shape[0]/warped.shape[0]
            warped = nwarped
        (wh, ww, _ )= warped.shape

        point2 = Point( max(int(point2.x * ratio), 0),\
                        max(int(point2.y * ratio) , 0) )
        cropped = warped[point2.y:int(wh * ratio), point2.x:int(ww * ratio)]

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
        bb = 0
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
                bb+=1
                if acx < cah < acx + w and acy < cav < acy + h:
                   center, radius = ((cah, cav), int((aw/2)*1.05))
                   acx = int(ax)
                   acy = int(ay)
                   cv2.putText(warped,  f"{bb}", (int(acx), int(acy)), \
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)  
                   ptText = (int(acx+w*0.15), int(acy+(3*h/5)))
                   acx += int(wSpace)
                   ct+=1 
                else:
                   cah = int(acx+(w/2))
                   cav = int(acy+(h/2))                     
                   center, radius = ((cah, cav), int((w/2)*1.05))
                   cv2.putText(warped,  f"{bb}", (int(acx), int(acy)), \
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)  
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
        fontScale = 1
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

        # Stop the stopwatch / counter 
        t1_stop = perf_counter()  

        print(f"Elapsed time during the image processing in seconds:{t1_stop-t1_start}") 

        return warped, answers, (t1_stop-t1_start)

