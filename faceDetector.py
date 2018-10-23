from imutils.video import VideoStream
from imutils.video import FPS
from multiprocessing import Process
from multiprocessing import Queue
import numpy as np
import argparse
import imutils
import time
import cv2
from device import Device

class FaceDetector(object):
    def __init__(self):
        self.inputQueue = Queue(maxsize=1)
        self.outputQueue = Queue(maxsize=1)
        self.face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        self.faces = None
        self.p = Process(target=self.detect_faces, args=(self.face_cascade, self.inputQueue, self.outputQueue))


    def detect_faces(self, classifier, inputQueue, outputQueue):
    # keep looping
        while True:
    # check to see if there is a frame in our input queue
            if (inputQueue.empty() == False):
                frame = inputQueue.get()
                #frame = cv2.resize(frame, (300, 300))
                gray = cv2.cvtColor(frame,cv2.COLOR_BGR2GRAY)
    # write the detections to the output queue
                faces = self.face_cascade.detectMultiScale(gray, 1.1, 5)
                outputQueue.put(faces)
                #print('hey')

    def stream(self):
        print("[INFO] starting process...")
        self.p.start()
        vs = VideoStream(usePiCamera=True).start()
        time.sleep(2.0)
        fps = FPS().start()
        device = Device()
        while True:
            frame = vs.read()
            frame = imutils.resize(frame, width=400)
            (fH, fW) = frame.shape[:2]
            # if the input queue *is* empty, give the current frame to
            # classify
            if self.inputQueue.empty():
                self.inputQueue.put(frame)

            # if the output queue *is not* empty, grab the detections
            if not self.outputQueue.empty():
                self.faces = self.outputQueue.get()

            # check to see if our detectios are not None (and if so, we'll
            # draw the detections on the frame)
            if self.faces is not None:
                #send to our machine learning service
                


                for (x,y,w,h) in self.faces:
                    cv2.rectangle(frame,(x,y),(x+w,y+h),(255,255,0),2)

                # show the output frame
            cv2.imshow("Frame", frame)
            key = cv2.waitKey(1) & 0xFF

            # if the `q` key was pressed, break from the loop
            if key == ord("q"):
                break

            # update the FPS counter
            fps.update()

        # stop the timer and display FPS information
        fps.stop()
        print("[INFO] elapsed time: {:.2f}".format(fps.elapsed()))
        print("[INFO] approx. FPS: {:.2f}".format(fps.fps()))

        # do a bit of cleanup
        cv2.destroyAllWindows()
        vs.stop()