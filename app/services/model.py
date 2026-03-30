from ultralytics import YOLO
import easyocr

model = YOLO("yolov8n.pt")
reader = easyocr.Reader(['en'])


def detect_car(image):
    results = model(image)
    
    for r in results:
        for box in r.boxes:
            cls = int(box.cls[0])
            if cls == 2:  # car class
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                return image[y1:y2, x1:x2]

    return None
def classify_view(car_img):
    # TODO: plug in GitHub model
    return "rear"  # fake output

def detect_plate(car_img):
    # TODO: real plate detection
    return car_img


def read_plate(img):
    result = reader.readtext(img)
    if result:
        return result[0][-2]
    return None