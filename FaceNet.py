import os

from PIL import Image
from numpy import asarray, expand_dims, load
from mtcnn.mtcnn import MTCNN
from keras.models import load_model
from sklearn.preprocessing import LabelEncoder, Normalizer
from sklearn.svm import SVC
import cv2

import FTPClient


def process_video(video):
    print('Processing video file with FaceNet..')
    embeddingModel, predictionModel, out_encoder = set_models()
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

        array_images = extract_faces(frame)
        for i in range(len(array_images)):
            image_embeddings = get_embedding(predictionModel, array_images[i])
            image_dim = expand_dims(image_embeddings, axis=0)
            yhat_class = embeddingModel.predict(image_dim)
            # get name
            predict_names = out_encoder.inverse_transform(yhat_class)
            print("Detected person: " + predict_names[0])

            if predict_names[0] == 'Unknown':
                unknownPersonImages.append(array_images[i])
            else:
                findedPersons.append(predict_names[0])

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


def extract_faces(picture, required_size=(160, 160)):
    image = cv2.cvtColor(picture, cv2.COLOR_BGR2RGB)
    pixels = asarray(image)  # convert to array

    detector = MTCNN()  # create the detector, using default weights
    results = detector.detect_faces(pixels)  # detect faces in the image

    faces_array = []
    for i in range(len(results)):
        x1, y1, width, height = results[i]['box']  # extract the bounding box from the first face, only one face
        # bug fix
        x1, y1 = abs(x1), abs(y1)
        x2, y2 = x1 + width, y1 + height

        face = pixels[y1:y2, x1:x2]  # extract the face

        image = Image.fromarray(face)  # resize pixels to the model size
        image = image.resize(required_size)
        face_array = asarray(image)
        faces_array.append(face_array)

    return faces_array


def set_models():
    data = load('dataset.npz')
    testX_faces = data['arr_2']
    # load face embeddings
    data = load('dataset-embeddings.npz')
    trainX, trainy, testX, testy = data['arr_0'], data['arr_1'], data['arr_2'], data['arr_3']
    # normalize input vectors
    in_encoder = Normalizer(norm='l2')
    trainX = in_encoder.transform(trainX)
    testX = in_encoder.transform(testX)
    # label encode targets
    out_encoder = LabelEncoder()
    out_encoder.fit(trainy)
    trainy = out_encoder.transform(trainy)
    testy = out_encoder.transform(testy)
    # fit model
    embeddingModel = SVC(kernel='linear', probability=True)
    embeddingModel.fit(trainX, trainy)
    predictionModel = load_model('facenet_keras.h5')

    return embeddingModel, predictionModel, out_encoder


def get_embedding(model, face_pixels):
    # scale pixel values
    face_pixels = face_pixels.astype('float32')
    # standardize pixel values across channels (global)
    mean, std = face_pixels.mean(), face_pixels.std()
    face_pixels = (face_pixels - mean) / std
    # transform face into one sample
    samples = expand_dims(face_pixels, axis=0)
    # make prediction to get embedding
    yhat = model.predict(samples)
    return yhat[0]