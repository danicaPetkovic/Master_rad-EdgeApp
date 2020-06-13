import os
import sys
import time
from io import BytesIO

import cv2
from azure.cognitiveservices.vision.face import FaceClient
from azure.cognitiveservices.vision.face.models import TrainingStatusType
from msrest.authentication import CognitiveServicesCredentials

import FTPClient

KEY = '620d5320d80c40e6acf2aaa2b9c95298'
ENDPOINT = 'https://master.cognitiveservices.azure.com/'
PERSON_GROUP_ID = 'microsoft-dataset'

# Create an authenticated FaceClient.
face_client = FaceClient(ENDPOINT, CognitiveServicesCredentials(KEY))
#persons = face_client.person_group_person.list(PERSON_GROUP_ID)


def detect_faces(image_name):
    image = open(image_name, 'r+b')
    imageCrop = cv2.imread(image_name)
    face_ids = []
    detected_names = []
    unknown_images = []
    faces = face_client.face.detect_with_stream(image)
    for face in faces:
        face_ids.append(face.face_id)

    # identify faces
    if face_ids:
        results = face_client.face.identify(face_ids, PERSON_GROUP_ID)
        #if not results:
            #print('No person identified')
        for person in results:
            if len(person.candidates) == 0:
                name = 'unknown'
                box = [f.face_rectangle for f in faces if f.face_id == person.face_id]
                croped = imageCrop[box[0].top:box[0].top+box[0].height, box[0].left:box[0].left+box[0].width]
                unknown_images.append(croped)
                detected_names.append(name)

                break
            personName = face_client.person_group_person.get(PERSON_GROUP_ID, person.candidates[0].person_id)
            #print('Person on the image is ', personName.name)
            detected_names.append(personName.name)

    return detected_names, unknown_images


def process_video(video):
    print('Processing video with Azure Face..')
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

        image_name = 'microsoft.jpg'
        cv2.imwrite(image_name, frame)
        detected_names, unknown_images = detect_faces(image_name)
        i = 0
        for name in detected_names:
            print("Detected person: " + name)
            if name.lower() == "unknown":
                unknownPersonImages.append(unknown_images[i])
            else:
                findedPersons.append(name)
            i=i+1

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