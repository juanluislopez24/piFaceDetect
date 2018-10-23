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
import base64
import json

# [END iot_mqtt_includes]

# The initial backoff time after a disconnection occurs, in seconds.
minimum_backoff_time = 1



class FaceDetector(object):
    def __init__(self, args):
        self.inputQueue = Queue(maxsize=1)
        self.outputQueue = Queue(maxsize=1)
        self.face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
        self.faces = None
        self.p = Process(target=self.detect_faces, args=(self.face_cascade, self.inputQueue, self.outputQueue))
        self.args = args
        

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


        global minimum_backoff_time

        #Topic used to send img data to
        mqtt_img_topic = '/devices/{}/events/imgtopic'.format(args.device_id)

        device = Device()

        jwt_iat = datetime.datetime.utcnow()
        jwt_exp_mins = self.args.jwt_expires_minutes
        client = device.get_client(
            self.args.project_id, self.args.cloud_region, self.args.registry_id, self.args.device_id,
            self.args.private_key_file, self.args.algorithm, self.args.ca_certs,
            self.args.mqtt_bridge_hostname, self.args.mqtt_bridge_port)

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
                # Process network events.
                client.loop()

                # Wait if backoff is required.
                if should_backoff:
                    # If backoff time is too large, give up.
                    if minimum_backoff_time > MAXIMUM_BACKOFF_TIME:
                        print('Exceeded maximum backoff time. Giving up.')
                        break

                    # Otherwise, wait and connect again.
                    delay = minimum_backoff_time + random.randint(0, 1000) / 1000.0
                    print('Waiting for {} before reconnecting.'.format(delay))
                    time.sleep(delay)
                    minimum_backoff_time *= 2
                    client.connect(args.mqtt_bridge_hostname, args.mqtt_bridge_port)


                #prepare to our machine learning service
                basejpg =cv2.imencode('.jpg', baseImage)[1]
                base64_bytes = base64.b64encode(basejpg)
                base64_imgstr = base64_bytes.decode('utf-8')


                # [START iot_mqtt_jwt_refresh]
                seconds_since_issue = (datetime.datetime.utcnow() - jwt_iat).seconds
                if seconds_since_issue > 60 * jwt_exp_mins:
                    print('Refreshing token after {}s').format(seconds_since_issue)
                    jwt_iat = datetime.datetime.utcnow()
                    client = device.get_client(
                        args.project_id, args.cloud_region,
                        args.registry_id, args.device_id, args.private_key_file,
                        args.algorithm, args.ca_certs, args.mqtt_bridge_hostname,
                        args.mqtt_bridge_port)
                # [END iot_mqtt_jwt_refresh]


                # Build JSON Payload
                payload = json.dumps({
                    #device info
                    'registry_id': args.registry_id,
                    'device_id': args.device_id,
                    #img base85 in utf-8
                    'img': base64_imgstr,
                    #timestamp
                    'timestamp_local': datetime.datetime.now(),
                    'timestamp_utc': datetime.datetime.utcnow(),
                }, indent=4, default=str)

                # Publish image payload to imgtopic
                print('Publishing image payload encoded to base64 over JSON')
        
                client.publish(mqtt_img_topic, payload, qos=1)
                


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
        exit()