import os

import boto3
import cv2
from numpy import asarray

import FTPClient

BUCKET = "security-sistem-aws"
COLLECTION = "aws-dataset"

def search_faces_by_image(image, collection_id, threshold=90, region="eu-central-1"):
    is_success, im_buf_arr = cv2.imencode(".jpg", asarray(image))
    image_bytes = im_buf_arr.tobytes()
    rekognition = boto3.client("rekognition", region)
    response = rekognition.search_faces_by_image(
        Image={'Bytes': image_bytes},
        CollectionId=collection_id,
        FaceMatchThreshold=threshold,
    )
    return response['FaceMatches']


def detect_faces(frame, attributes=['DEFAULT'], region="eu-central-1"):
    is_success, im_buf_arr = cv2.imencode(".jpg", frame)
    image_bytes = im_buf_arr.tobytes()
    rekognition = boto3.client("rekognition", region)
    response = rekognition.detect_faces(
        Image={'Bytes': image_bytes},
        Attributes=attributes,
    )
    return response['FaceDetails']



def process_video(video):
    print('Processing video with AWS Face Rekognition..')
    stream = cv2.VideoCapture(video)
    findedPersons = []
    unknownPersonImages = []
    processedImageCount = 0
    processVideo = True

    while processVideo and processedImageCount < 6:
        (grabbed, frame) = stream.read()  # grabbed (true, false) da li je frame uzet pravilno ili ne, frame je uzeta slika
        #print('Obradjuje se prvi frame')
        if not grabbed:  # ako je grabbed false, onda smo stigli do kraja stream-a
            break

        imgHeight, imgWidth, channels = frame.shape

        data = detect_faces(frame)
        for faceDetail in data:
            box = faceDetail['BoundingBox']
            left = abs(int(imgWidth * box['Left']))
            top = abs(int(imgHeight * box['Top']))
            width = abs(int(imgWidth * box['Width']))
            height = abs(int(imgHeight * box['Height']))
            croped_image = frame[top:top+height, left:left+width]
            data = search_faces_by_image(croped_image, COLLECTION)
            if len(data) > 0:
                for record in data:
                    face = record['Face']
                    print("Matched Face ({}%)".format(record['Similarity']))
                    print("  ImageId : {}".format(face['ExternalImageId']))
                    findedPersons.append(face['ExternalImageId'])
            else:
                cv2.imwrite("allaa.jpg", croped_image)
                unknownPersonImages.append(croped_image)

        #print('processedImageCount je', processedImageCount)
        processedImageCount = processedImageCount + 1

        if processedImageCount == 3:
            if len(findedPersons) != 0:
                findedPersons = list(set(findedPersons))
                processVideo = False

        for i in range(9):  # obradjujemo svaki 10-ti frame, sto znaci da preskacemo 10
            (grabbed, frame) = stream.read()
            if not grabbed:  # ako je grabbed false, onda smo stigli do kraja stream-a
                break
        #print('Preskocilo se 9 framova')

    stream.release()
    if len(findedPersons) == 0:
        return False, [], unknownPersonImages
    else:
        return True, findedPersons, []