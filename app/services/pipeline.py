from app.services.model import detect_car, classify_view, detect_plate, read_plate

def process_image(image):
    # Step 1: detect car
    car_crop = detect_car(image)

    if car_crop is None:
        return {"is_car": False}

    # Step 2: front vs rear
    view = classify_view(car_crop)

    result = {
        "is_car": True,
        "view": view
    }

    # Step 3: if rear → plate detection
    if view == "rear":
        plate_img = detect_plate(car_crop)

        if plate_img is not None:
            plate_text = read_plate(plate_img)
            result["license_plate"] = plate_text
        else:
            result["license_plate"] = None

    return result