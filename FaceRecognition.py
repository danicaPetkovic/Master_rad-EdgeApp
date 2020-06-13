import os
import pickle
from collections import Counter
import cv2
import imutils
import face_recognition

import FTPClient

data = pickle.loads(open("encodings.pickle", "rb").read())
knownPersons = list(Counter(data["names"]).values()), list(Counter(data["names"]).keys())


def process_video(video):
    print('Processing video with Face Recognition..')
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

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)  # konvertujemo u rgb i smanjujemo sirinu na 750px zbog brze obrade
        r = frame.shape[1] / float(rgb.shape[1])

        boxes = face_recognition.face_locations(rgb, model="hog")  # model moze da bude hog i cnn, hog je dosta brzi, cnn je precizniji
        encodings = face_recognition.face_encodings(rgb, boxes)  # enkodovanje slike u 128bitni vektor
        matches = []

        for encoding in encodings:
            # attempt to match each face in the input image to our known encodings
            matches.append(face_recognition.compare_faces(data["encodings"], encoding))
            name = "Unknown"
            i = 0

        for match in matches:
            if True in match:  # provera da li je pronadjen face match
                matchedIdxs = [i for (i, b) in enumerate(match) if b]  # pronadjemo indekse za sva podudarna lica
                counts = {}  # dictionary da izbrojimo ukupan broj puta koliko je svako lice podudareno ('glasovi')

                for i in matchedIdxs:  # za svako lice pronadjemo ime brojimo koliko puta je ono ponovljeno kao podudaranje
                    name = data["names"][i]
                    counts[name] = counts.get(name,
                                              0) + 1  # get(name, 0) vraca vrednosti koja se nalazi na polju name, ukoliko ne postoji vraca 0

                name = max(counts, key=counts.get)  # odredjujemo prepoznato lice sa najvecim brojem 'glasova'
                countInitial = knownPersons[0][knownPersons[1].index(name)]
                if countInitial != max(
                        counts.values()):  # ukoliko se prepoznato lice ne podudara sa svim istim licima iz liste knownPersons, onda prepoznato lice oznacavamo da ne znamo tacno ko je
                    name = 'Unknown'
            print('Detected person:', name)

            if name == 'Unknown':
                croped = crop_image(frame, boxes)
                unknownPersonImages = unknownPersonImages + croped
            else:
                findedPersons.append(name)

        #print('processedImageCount je', processedImageCount)
        processedImageCount = processedImageCount + 1

        if processedImageCount == 10:
            if len(findedPersons) != 0:
                findedPersons = list(set(findedPersons))
                processVideo = False

        for i in range(19):  # obradjujemo svaki 10-ti frame, sto znaci da preskacemo 10
            (grabbed, frame) = stream.read()
            if not grabbed:  # ako je grabbed false, onda smo stigli do kraja stream-a
                break
        #print('Preskocilo se 9 framova')

    stream.release()
    if len(findedPersons) == 0:
        return False, [], unknownPersonImages
    else:
        return True, findedPersons, []


def crop_image(frame, boxes):
    images = []
    for box in boxes:
        top = box[0]
        right = box[1]
        bottom = box[2]
        left = box[3]
        image = frame[top:bottom, left:right]
        images.append(image)
    return images


"""
valid, knownPersons, unknownPersons = process_video(os.getcwd() + "\\reolink_files\\" + "videoplayback.mp4")
print("Result is " + str(valid))
print("Known persons: " + str(knownPersons))
print("Unknown persons: " + str(unknownPersons))
if not valid:
    data_sent = FTPClient.send_data_to_server(unknownPersons)
    print(data_sent)
"""

#os.rename('la.av', 'la.mp4')
#process_video("1234.mp4")