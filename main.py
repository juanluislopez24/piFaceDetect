from faceDetector import FaceDetector

if __name__ == "__main__":
    # execute only if run as a script
    main()

def main():
    detector = FaceDetector()
    detector.stream()