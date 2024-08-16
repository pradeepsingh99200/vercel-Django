from django.shortcuts import render
from django.http import JsonResponse, StreamingHttpResponse
from .forms import BlinkForm
import cv2 as cv
import mediapipe as mp
import threading
import math
import time

# Define global variables for blink detection
frame_counter = 0
CEF_COUNTER = 0
TOTAL_BLINKS = 0
CLOSED_EYES_FRAME = 3
camera = None

# Eye landmarks indices
LEFT_EYE = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
RIGHT_EYE = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]

# Initialize MediaPipe face mesh
mp_face_mesh = mp.solutions.face_mesh

# Euclidean distance function
def euclideanDistance(point, point1):
    x, y = point
    x1, y1 = point1
    return math.sqrt((x1 - x) ** 2 + (y1 - y) ** 2)

# Blink Ratio function
def blinkRatio(landmarks):
    rh_right = landmarks[RIGHT_EYE[0]]
    rh_left = landmarks[RIGHT_EYE[8]]
    rv_top = landmarks[RIGHT_EYE[12]]
    rv_bottom = landmarks[RIGHT_EYE[4]]

    lh_right = landmarks[LEFT_EYE[0]]
    lh_left = landmarks[LEFT_EYE[8]]
    lv_top = landmarks[LEFT_EYE[12]]
    lv_bottom = landmarks[LEFT_EYE[4]]

    rhDistance = euclideanDistance(rh_right, rh_left)
    rvDistance = euclideanDistance(rv_top, rv_bottom)
    lvDistance = euclideanDistance(lv_top, lv_bottom)
    lhDistance = euclideanDistance(lh_right, lh_left)

    reRatio = rhDistance / rvDistance
    leRatio = lhDistance / lvDistance

    return (reRatio + leRatio) / 2

def generate_frames():
    global frame_counter, CEF_COUNTER, TOTAL_BLINKS, camera
    with mp_face_mesh.FaceMesh(min_detection_confidence=0.5, min_tracking_confidence=0.5) as face_mesh:
        start_time = time.time()

        while True:
            ret, frame = camera.read()
            if not ret:
                break

            frame = cv.resize(frame, None, fx=1.5, fy=1.5, interpolation=cv.INTER_CUBIC)
            rgb_frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)
            results = face_mesh.process(rgb_frame)

            if results.multi_face_landmarks:
                mesh_coords = [(int(point.x * frame.shape[1]), int(point.y * frame.shape[0])) for point in
                               results.multi_face_landmarks[0].landmark]

                # Calculate blink ratio
                ratio = blinkRatio(mesh_coords)

                # Blink detection logic
                if ratio > 5.5:
                    CEF_COUNTER += 1
                else:
                    if CEF_COUNTER > CLOSED_EYES_FRAME:
                        TOTAL_BLINKS += 1
                        CEF_COUNTER = 0

                # Draw the blink count and ratio on the frame
                cv.putText(frame, f'Ratio: {round(ratio, 2)}', (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
                cv.putText(frame, f'Total Blinks: {TOTAL_BLINKS}', (10, 60), cv.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

            # Encode the frame as JPEG
            ret, buffer = cv.imencode('.jpg', frame)
            frame = buffer.tobytes()

            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

def blink_detection():
    global camera
    time.sleep(30)  # Wait for 30 seconds for the detection
    camera.release()

def index(request):
    global camera, TOTAL_BLINKS
    if request.method == 'POST':
        form = BlinkForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name']
            camera_access = form.cleaned_data['camera_access']

            if camera_access:
                camera = cv.VideoCapture(0)
                TOTAL_BLINKS = 0  # Reset blink count for each session
                threading.Thread(target=blink_detection).start()
                return JsonResponse({'status': 'success', 'message': f'Starting blink detection for 30 seconds.'})

    else:
        form = BlinkForm()

    return render(request, 'blink/index.html', {'form': form})

def get_final_message(request):
    global TOTAL_BLINKS
    if TOTAL_BLINKS < 8:
        message = "Your eyes are unhealthy."
    else:
        message = "Thank you, your eyes are healthy."
    return JsonResponse({'message': message})

def video_feed(request):
    return StreamingHttpResponse(generate_frames(), content_type='multipart/x-mixed-replace; boundary=frame')
