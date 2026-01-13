import base64
import cv2
import numpy as np
import re
import mediapipe as mp

def base64_to_image(base64_string):
    # Remove data:image/...;base64, if present
    base64_string = re.sub('^data:image/.+;base64,', '', base64_string)

    try:
        image_bytes = base64.b64decode(base64_string)
        np_arr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        return image
    except Exception:
        return None

def validate_image(image):
    if image is None:
        return False, "Invalid image"

    h, w = image.shape[:2]
    if h < 300 or w < 300:
        return False, "Image resolution too low"

    return True, None



mp_face = mp.solutions.face_detection.FaceDetection(
    model_selection=1,
    min_detection_confidence=0.4
)

def detect_face(image):
    result = mp_face.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    return bool(result.detections)


mp_seg = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=1)

def is_white_background(image):
    seg = mp_seg.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
    mask = seg.segmentation_mask < 0.5  # background

    background_pixels = image[mask]
    if len(background_pixels) == 0:
        return False

    hsv = cv2.cvtColor(background_pixels.reshape(-1,1,3), cv2.COLOR_BGR2HSV)

    lower_white = (0, 0, 200)
    upper_white = (180, 40, 255)

    white_pixels = cv2.inRange(hsv, lower_white, upper_white)
    white_ratio = (white_pixels > 0).mean()

    return white_ratio > 0.50

def is_not_blurry(image, threshold=40):
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    score = cv2.Laplacian(gray, cv2.CV_64F).var()
    return score > threshold

def shadows_ok(image):
    mp_seg = mp.solutions.selfie_segmentation.SelfieSegmentation(model_selection=1)
    seg = mp_seg.process(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))

    background_mask = seg.segmentation_mask < 0.5
    background = image[background_mask]

    if len(background) == 0:
        return False

    hsv_bg = cv2.cvtColor(background.reshape(-1,1,3), cv2.COLOR_BGR2HSV)
    v = hsv_bg[:,0,2]

    dark_ratio = (v < 100).mean()   # relaxed
    return dark_ratio < 0.10        # allow up to 10%