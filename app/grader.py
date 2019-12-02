#!/usr/bin/python3

# Using Quart to make an api 
# import necessary libraries and functions 
import asyncio
import io
import numpy as np
import argparse
import imutils
import cv2
import statistics as st
import sys
import os
import time

from time import perf_counter

from typing import List
from collections import namedtuple

from pyzbar import pyzbar
from imutils.perspective import four_point_transform
from imutils import contours


from fastapi import Body, FastAPI, File, UploadFile
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from starlette.responses import FileResponse, JSONResponse, Response, RedirectResponse, HTMLResponse
from starlette.requests import Request 

from http import HTTPStatus
# Python program to show time by perf_counter()  
from omr import parseImageInfo
from secure import SecureHeaders, SecureCookie

secure_headers = SecureHeaders()
secure_cookie = SecureCookie()

# creating a Fast API
api = FastAPI()
# api.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# on the terminal type: curl http://127.0.0.1:5000/ 
# returns hello world when we use GET. 
# returns the data that we send when we use POST. 
@api.get("/", response_class=HTMLResponse)
async def home(): 
    ''' Test page
    '''
    return '''
    <!doctype html>
    <title>Envie uma foto para avaliação</title>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <!-- Pure CSS stylesheet -->
        <link rel="stylesheet" href="https://unpkg.com/purecss@1.0.1/build/pure-min.css" integrity="sha384-oAOxQR6DkCoMliIh8yFnu25d7Eq/PHS21PClpwjOTeU2jRSq11vu66rf90/cZr47" crossorigin="anonymous">
        <!--[if lte IE 8]>
            <link rel="stylesheet" href="https://unpkg.com/purecss@1.0.1/build/grids-responsive-old-ie-min.css">
        <![endif]-->
        <!--[if gt IE 8]><!-->
            <link rel="stylesheet" href="https://unpkg.com/purecss@1.0.1/build/grids-responsive-min.css">
        <!--<![endif]-->
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
        Especificação da api:
        <a href="/docs"> formato swagger,</a>
        <a href="/redoc"> formato redoc.</a>
        </form>        
    </div>
    <HR>        
    <p>Envie uma foto para avaliação</p>
    <p> (Para enviar várias e retornar JSON: <a href="/bulkJSON"> BULK MODE JSON</a>)</p>
    <p> (Para enviar várias e retornar imagens: <a href="/bulkimage"> BULK MODE IMAGES</a>)</p>
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
    <p style="font-size:12px;" >Time => 
    <input id="timing" type="text" value="--.---" style="width: 60px; 
                    border: none; font-size: 16px; 
                    font-weight: bold; color: black;">segundos</p>
    <form action="/api/omr/parseType/dialogos/1000" onsubmit="start()" method=post enctype="multipart/form-data" target="result">        
    <input style="font-size:12px;" type=file name=formImage accept-br:"image/*;capture=camera" >      
    <input style="font-size:12px;" type=submit value="Retorna Imagem">
    </form>
    <form action="/api/omr/parseType/dialogos/1000?responseType=JSON" onsubmit="start()" method=post enctype="multipart/form-data" target="result">  
    <input style="font-size:12px;" type=file name=formImage accept-br:"image/*;capture=camera" >      
    <input style="font-size:12px;" type=submit value="Retorna JSON">
    </form>
    </td>
    <tr>
    <td colspan=2 width="100%" >
        <div id="result" style="width='100%' height=450>
            
        </div>
    </td>        
    </tr>
    </table>
    
'''


# on the terminal type: curl http://127.0.0.1:5000/ 
# returns hello world when we use GET. 
# returns the data that we send when we use POST. 
@api.get("/bulkJSON", response_class=HTMLResponse)
async def home(): 
    ''' Test page for bulk
    '''
    return '''
    <!doctype html>
    <title>Envie várias fotos para avaliação</title>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <!-- Pure CSS stylesheet -->
        <link rel="stylesheet" href="https://unpkg.com/purecss@1.0.1/build/pure-min.css" integrity="sha384-oAOxQR6DkCoMliIh8yFnu25d7Eq/PHS21PClpwjOTeU2jRSq11vu66rf90/cZr47" crossorigin="anonymous">
        <!--[if lte IE 8]>
            <link rel="stylesheet" href="https://unpkg.com/purecss@1.0.1/build/grids-responsive-old-ie-min.css">
        <![endif]-->
        <!--[if gt IE 8]><!-->
            <link rel="stylesheet" href="https://unpkg.com/purecss@1.0.1/build/grids-responsive-min.css">
        <!--<![endif]-->
        <!-- Filepond stylesheet -->
        <link href="https://unpkg.com/filepond/dist/filepond.css" rel="stylesheet">
        <link href="https://unpkg.com/filepond-plugin-image-preview/dist/filepond-plugin-image-preview.css" rel="stylesheet">
        <link href="https://unpkg.com/filepond-plugin-file-poster/dist/filepond-plugin-file-poster.css" rel="stylesheet">

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
        Especificação da api:
        <a href="/docs"> formato swagger,</a>
        <a href="/redoc"> formato redoc.</a>
        </form>        
    </div>
    <HR>        
    <p>Envie várias fotos para avaliação</p>
    <HR>
    <input style="font-size:12px;" type=file multiple name=formImage class="filepond" accept-br:"image/*;capture=camera" >      
    <div id="result" style="width='100%' height=450">
        
    </div>

    <!-- add before </body> -->
    <!-- include FilePond plugins -->
    <script src="https://unpkg.com/filepond/dist/filepond.js" ></script>
    <script src="https://unpkg.com/filepond-plugin-image-preview/dist/filepond-plugin-image-preview.min.js"></script>
    <script>
        FilePond.registerPlugin(FilePondPluginImagePreview);
        FilePond.setOptions({
            server: {
                url: '/api/omr/',
                timeout: 30000,
                process: {
                    url: 'parseFile/dialogos/1000?responseType=JSON',
                    method: 'POST',
                    responseType: 'text',
                    // Should call the load method when done and pass the returned server file id
                    // this server file id is then used later on when reverting or restoring a file
                    // so your server knows which file to return without exposing that info to the client
                    onload: (response) => {  
                        var div = document.getElementById('result');
                        var para = document.createElement("P");           // Create a <p> node
                        var t = document.createTextNode(response);        // Create a text node
                        para.appendChild(t);                              // Append the text to <p>
                        div.appendChild(para);                            // Append <p> to <div> with id="result"                      
                        return response;
                    }                
                }
            }
        });
        FilePond.parse(document.body);
    </script>
    
'''


# on the terminal type: curl http://127.0.0.1:5000/ 
# returns hello world when we use GET. 
# returns the data that we send when we use POST. 
@api.get("/bulkimage", response_class=HTMLResponse)
async def home(): 
    ''' Test page for bulk
    '''
    return '''
    <!doctype html>
    <title>Envie várias fotos para avaliação</title>
    <head>
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <!-- Pure CSS stylesheet -->
        <link rel="stylesheet" href="https://unpkg.com/purecss@1.0.1/build/pure-min.css" integrity="sha384-oAOxQR6DkCoMliIh8yFnu25d7Eq/PHS21PClpwjOTeU2jRSq11vu66rf90/cZr47" crossorigin="anonymous">
        <!--[if lte IE 8]>
            <link rel="stylesheet" href="https://unpkg.com/purecss@1.0.1/build/grids-responsive-old-ie-min.css">
        <![endif]-->
        <!--[if gt IE 8]><!-->
            <link rel="stylesheet" href="https://unpkg.com/purecss@1.0.1/build/grids-responsive-min.css">
        <!--<![endif]-->
        <!-- Filepond stylesheet -->
        <link href="https://unpkg.com/filepond/dist/filepond.css" rel="stylesheet">
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
        Especificação da api:
        <a href="/docs"> formato swagger,</a>
        <a href="/redoc"> formato redoc.</a>
        </form>        
    </div>
    <HR>        
    <p>Envie várias fotos para avaliação</p>
    <HR>
    <input style="font-size:12px;" type=file multiple name=formImage class="filepond" accept-br:"image/*;capture=camera" >      
    <div id="result" style="width='100%' height=450">
        
    </div>

    <script src="https://unpkg.com/filepond/dist/filepond.js" >
    </script>
    <script>
        FilePond.setOptions({
            server: {
                url: '/api/omr/',
                timeout: 30000,
                process: {
                    url: 'parseFile/dialogos/1000?responseType=image',
                    method: 'POST',
                    responseType: 'blob',
                    // Should call the load method when done and pass the returned server file id
                    // this server file id is then used later on when reverting or restoring a file
                    // so your server knows which file to return without exposing that info to the client
                    onload: (response) => {  
                        var urlCreator = window.URL || window.webkitURL;
                        var imageUrl = urlCreator.createObjectURL( response );
                        const img = new Image();
                        img.src = imageUrl;
                        var div = document.getElementById('result');
                        div.appendChild(img);
                        return response;
                    }                
                }
            }
        });
        FilePond.parse(document.body);
    </script>
    
'''

# A simple function to calculate the square of a number 
# the number to be squared is sent in the URL when we use GET 
# on the terminal type: curl http://127.0.0.1:5000 / omr / getTemplate / Name
# @api.route('/api/omr/getTemplate') 
@api.get('/api/omr/getTemplate/{form}') 
async def getTemplate(form: str):
    ''' Get Template
        <p>en:Get the template Word document used as base for the questionnaire;</p>
        <p>pt-br:Obtém o documento word de modelo usado como base do questionário.</p>
    '''
    templateFilename="./template/template.docx"
    return FileResponse(templateFilename, media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document") 

class ErrorMessage(BaseModel):
    message: str

# 'example': "{ 'answers': [[1, 7], [2, 5], [3, 6], [4, 7], [5, 6], [6, 5]]}"
class AnswersModel(BaseModel):
    answers: List[List[int]] = [[]]

# #
# curl -X POST -F 'image=@./images/test-09.jpg ' http://127.0.0.1:5000/omr/parseType/dialogos/1000
@api.post('/api/omr/parseType/{form}/{formId}', # tags=['omr'],
        response_model=AnswersModel,
        responses={
            HTTPStatus.NOT_FOUND: {
            "model": ErrorMessage,
            "description": "Image not found"},
            HTTPStatus.OK: {
                "description": "<p>en:Return the answers as json text or image</p><p>pt-br:Retorna as respostas em formato json. [(q,a),...] ou imagem</p>",
                "content": {
                    "application/json": {
                        "example": {'answers': [[1, 7], [2, 5], [3, 6], [4, 7], [5, 6], [6, 5]]}
                    }
                },
            },
        },) 
async def parseType(
    form: str = "dialogos",            # <p>en:Form type key</p><p>pt-br:Chave do tipo de formulario</p>
    formId: int = 1000,                # <p>en:Form Version id;</p><p>pt-br:Identicador da versão do formulário</p>
    formImage: UploadFile = File(...), # <p>en:The image to be analyzed;</p><p>pt-br: A imagem a ser analizada.</p>
    responseType: str = 'image',       # json / image <p>en:The response type expected;</p><p>pt-br:O tipo de resposta esperado.</p>
    nQuestions: int = 6,               # <p>en:The number of questions;</p><p>pt-br: O número de questões.</p>
    nAnswers: int = 7,                 # <p>en:The number of answers;</p><p>pt-br: O número de respostas.</p>
    nThreads: int = 4,                 # <p>en:The number of threads;</p><p>pt-br: O número de threads.</p>
    ):
    ''' Parses image to answers
        <p>en:Analyzes a questionnarie image according to the template (ie: /omr/getTemplate/dialogos)</p>
        <p>pt-br:Analiza uma imagem de um questionário de acordo com o modelo (Ex: /omr/getTemplate/dialogos)</p>            
    ''' 
    # Treat image
    imageReturn, answers, elapsedTime = await parseInfo(formImage, form, formId, nQuestions, nAnswers, nThreads )

    if isinstance(answers, type(None)):
        print('No answers')

    print(f'responseType={responseType}')
    if responseType.strip().lower() == 'json':            
        if  isinstance(elapsedTime, type(None)):
            return jsonable_encoder({"answers": answers})
        else:
            return jsonable_encoder({"answers": answers, 'elapsedTimeImage': elapsedTime})

    if isinstance(imageReturn, type(None)):
        print('No image')
        return JSONResponse(status_code=404, content={"message": "No image"})

    if isinstance( imageReturn , type(None)):
        print(f'As questões não puderam ser capturadas por essa foto, tente deixá-la mais paralela à camera.')
        return JSONResponse(status_code=404, content={"message": "As questões não puderam ser capturadas por essa foto, tente deixá-la mais paralela à camera."})

    warped = imutils.resize(imageReturn, height=400)
    data = cv2.imencode('.jpg', warped)[1].tobytes()    

    buf = io.BytesIO(data)

    response = Response(buf.getvalue(), status_code=200, media_type='image/jpg')
    response.headers['Accept']='Ranges=bytes'
    return response

@api.post('/api/omr/parseJSON/{form}/{formId}', # tags=['omr'],
        response_model=AnswersModel,
        responses={
            HTTPStatus.NOT_FOUND: {
            "model": ErrorMessage,
            "description": "Image not found"},
            HTTPStatus.OK: {
                "description": "<p>en:Return the answers as json text</p><p>pt-br:Retorna as respostas em formato json. [(q,a),...]</p>",
                "content": {
                    "application/json": {
                        "example": {'answers': [[1, 7], [2, 5], [3, 6], [4, 7], [5, 6], [6, 5]]}
                    }
                },
            },
        },) 
async def parseJSON(
    form: str = "dialogos",      # <p>en:Form type key</p><p>pt-br:Chave do tipo de formulario</p>
    formId: int = 1000,              # <p>en:Form Version id;</p><p>pt-br:Identicador da versão do formulário</p>
    formImage: UploadFile = File(...), # <p>en:The image to be analyzed;</p><p>pt-br: A imagem a ser analizada.</p>
    nQuestions: int = 6,         # <p>en:The number of questions;</p><p>pt-br: O número de questões.</p>
    nAnswers: int = 7,            # <p>en:The number of answers;</p><p>pt-br: O número de respostas.</p>
    nThreads: int = 4,            # <p>en:The number of threads;</p><p>pt-br: O número de threads.</p>
    ):
    ''' Parses image to answers
        <p>en:Analyzes a questionnarie image according to the template (ie: /omr/getTemplate/dialogos)</p>
        <p>pt-br:Analiza uma imagem de um questionário de acordo com o modelo (Ex: /omr/getTemplate/dialogos)</p>            
    ''' 
    # Treat image
    imageReturn, answers, elapsedTime = await parseInfo(formImage, form, formId, nQuestions, nAnswers, nThreads )

    if isinstance(answers, type(None)):
        return None, None, None

    # use this in production
    # for a in answers:
    #    print(f"question_no:{a[0]} a:{a[1]}")     
    return jsonable_encoder({"answers": answers})

# 'example': "{ 'answe
# \]
# lk?rs': [[1, 7], [2, 5], [3, 6], [4, 7], [5, 6], [6, 5]]}"
class FileAnswersModel(BaseModel):
    fileName: str
    answers: List[List[int]] = [[]]

class FilesAnswersModel(BaseModel):
    files : List[FileAnswersModel] = []

# curl -X POST -F 'image=@./images/test-09.jpg ' http://127.0.0.1:5000/omr/parseType/dialogos/1000
@api.post('/api/omr/parseFile/{form}/{formId}', # tags=['omr'],
        # response_model=FilesAnswersModel,
        responses={
            HTTPStatus.NOT_FOUND: {
            "model": ErrorMessage,
            "description": "Image not found"},
            HTTPStatus.OK: {
                "description": "<p>en:Return the answers as json text or image</p><p>pt-br:Retorna as respostas em formato json. [(q,a),...] ou imagem</p>",
                "content": {
                    "application/json": {
                        "example": {'answers': [[1, 7], [2, 5], [3, 6], [4, 7], [5, 6], [6, 5]]}
                    }
                },
            },
        },) 
async def parseFiles(
    form: str = "dialogos",                   # <p>en:Form type key</p><p>pt-br:Chave do tipo de formulario</p>
    formId: int = 1000,                       # <p>en:Form Version id;</p><p>pt-br:Identicador da versão do formulário</p>
    formImage: UploadFile = File(...),        # <p>en:The image to be analyzed;</p><p>pt-br: A imagem a ser analizada.</p>
    itemId: str = '',                         # json / image <p>en:The response type expected;</p><p>pt-br:O tipo de resposta esperado.</p>
    responseType: str = 'image',              # json / image <p>en:The response type expected;</p><p>pt-br:O tipo de resposta esperado.</p>
    nQuestions: int = 6,                      # <p>en:The number of questions;</p><p>pt-br: O número de questões.</p>
    nAnswers: int = 7,                        # <p>en:The number of answers;</p><p>pt-br: O número de respostas.</p>
    nThreads: int = 4,                        # <p>en:The number of threads;</p><p>pt-br: O número de threads.</p>
    ):
    ''' Parses image to answers
        <p>en:Analyzes a questionnarie image according to the template (ie: /omr/getTemplate/dialogos)</p>
        <p>pt-br:Analiza uma imagem de um questionário de acordo com o modelo (Ex: /omr/getTemplate/dialogos)</p>            
    ''' 
    # Treat image
    imageReturn, answers, elapsedTime = await parseInfo(formImage, form, formId, nQuestions, nAnswers, nThreads )

    if responseType.lower().strip() == 'image':
        if not isinstance(imageReturn, type(None)):
            warped = imutils.resize(imageReturn, height=400)
            data = cv2.imencode('.jpg', warped)[1].tobytes()    

            buf = io.BytesIO(data)

            response = Response(buf.getvalue(), status_code=200, media_type='image/jpg')
            response.headers['Accept']='Ranges=bytes'
            return response 

    if isinstance(answers, type(None)):
        return jsonable_encoder({"itemId": itemId, "filename": formImage.filename, "answers": []})
    else:
        if isinstance(elapsedTime, type(None)):
            return jsonable_encoder({"itemId": itemId, "filename": formImage.filename, "answers": answers})

    return jsonable_encoder({"itemId": itemId, "filename": formImage.filename, "answers": answers, 'elapsedTimeImage': elapsedTime})

# general parameter parse function
# that treat the files and send image
# to get read, returning both image and jsonkubec
# answers
async def parseInfo(formImage, form, id, nQuestions, nAnswers, nThreads): 
    # Answer Key
    # each question has 7 possible answers, to loop over the
    # question in batches of 7

    if isinstance(formImage, type(None)):
        print("Sem arquivo selecionado.")
        return None, None, None # (request.url)

    file = formImage 
    filename = ''

    if file:
        filename = file.filename

    # if user does not select file, browser also
    # submit an empty part without filename
    if filename == '':
        print("Sem arquivo selecionado.")
        return None, None, None # (request.url)

    if allowed_file(filename):                
        # Start the stopwatch / counter 
        t1_start = perf_counter()  
        imageName = filename.split('/')[-1]           
        #read image file string data
        filestr = formImage.file.read()
        #convert string data to numpy array
        npimg = np.frombuffer(filestr, np.uint8)
        # convert numpy array to image
        orig = cv2.imdecode(npimg, cv2.IMREAD_UNCHANGED )
        # Stop the stopwatch / counter 
        t1_stop = perf_counter()  

        print(f"Elapsed time before the image processing in seconds:{t1_stop-t1_start}") 

        return parseImageInfo(orig, nQuestions, nAnswers, imageName, nThreads)

    print("Arquivo invalido.")
    return None, None, None


@api.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    secure_headers.starlette(response)
    return response

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
    nThreads = 4
    # construct the argument parser
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--image", required=True,
                    help="path to the input image",default="")
    ap.add_argument("-o", "--output", required=False,
                    help="path to the output folder", default=".")
    ap.add_argument("-Q", "--questions", required=False,
                    help="Number of questions (lines)",default="6")
    ap.add_argument("-A", "--answers", required=False,
                    help="Number of answers (colunms)",default="7")
    ap.add_argument("-T", "--threads", required=False,
                    help="Number of threads",default="4")

    args = vars(ap.parse_args())
    image_path = args['image']

    sQuestions = args['questions']
    sAnswers = args['answers']
    sThreads = args['threads']

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

    if not (isinstance(sAnswers, type(None)) or sAnswers == ''):
        try:
            nThreads = int(sThreads)
        except:
            pass

    imageName = image_path.split('/')[-1]   
    # load the image
    orig = cv2.imread(image_path)

    if isinstance( orig , type(None)):
        print(f'Foto não encontrada.')
        sys.exit(1)

    image = orig.copy()
    imageReturn, answers, elapsedTime = parseImageInfo(image, nQuestions, nAnswers, imageName, nThreads)

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
