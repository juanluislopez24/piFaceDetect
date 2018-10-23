# import the necessary packages
from picamera.array import PiRGBArray
from picamera import PiCamera
import imutils
import time
import cv2
  
# initialize the camera and grab a reference to the raw camera capture
camera = PiCamera()
camera.resolution = (640, 480)
camera.framerate = 32
rawCapture = PiRGBArray(camera, size=(640, 480))
 
 
# allow the camera to warmup
time.sleep(0.1)
 
def capture_loop(age_net, gender_net): 
    font = cv2.FONT_HERSHEY_SIMPLEX
    # capture frames from the camera
    for frame in camera.capture_continuous(rawCapture, format="bgr", use_video_port=True):
        # grab the raw NumPy array representing the image, then initialize the timestamp
        # and occupied/unoccupied text
        image = frame.array
        #/usr/local/share/OpenCV/haarcascades/
        face_cascade = cv2.CascadeClassifier('/usr/local/share/OpenCV/haarcascades/haarcascade_frontalface_alt.xml')
        gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)
        print("Found "+str(len(faces))+" face(s)")
 
        #Draw a rectangle around every found face
        if(len(faces)>0):
            device.update_sensor_data()
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

            with open('cat.jpg', 'rb') as imageFile:
                f = imageFile.read()
                b = bytearray(f)


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

            # Publish "payload" to the MQTT topic. qos=1 means at least once
            # delivery. Cloud IoT Core also supports qos=0 for at most once
            # delivery.

            # Publish image payload to imgtopic
            print('Publishing image payload as bytes', payload)
            client.publish(mqtt_img_topic, b, qos=1)

            # Send events every second. State should not be updated as often
            time.sleep(10 if args.message_type == 'events' else 15)

      
        #cv2.imshow("Image", image)
 
        key = cv2.waitKey(1) & 0xFF
      
        # clear the stream in preparation for the next frame
        rawCapture.truncate(0)
      
        # if the `q` key was pressed, break from the loop
        if key == ord("q"):
            break
 
if __name__ == '__main__':
    capture_loop(age_net, gender_net)