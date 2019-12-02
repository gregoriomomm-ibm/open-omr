#!/usr/bin/python3

# Using Quart to make an api 
# import necessary libraries and functions 
import sys
import os
import argparse
import cv2
from omr import parseImageInfo

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
    ap.add_argument("-i", "--image", required=False,
                    help="path to the input image",default="")
    ap.add_argument("-o", "--output", required=False,
                    help="path to the output folder", default="test/output")
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
