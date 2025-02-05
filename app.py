import cv2
import face_recognition
import numpy as np
import os
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import csv

# Path to the directory containing known faces
KNOWN_FACES_DIR = "known_faces"

# Initialize lists to store known face encodings and their names
known_face_encodings = []
known_face_names = []
attendance_marked = set()  # To track attendance within a session

# Load known faces and encode them
def load_known_faces():
    global known_face_encodings, known_face_names
    known_face_encodings.clear()
    known_face_names.clear()
    for name in os.listdir(KNOWN_FACES_DIR):
        person_dir = os.path.join(KNOWN_FACES_DIR, name)
        if os.path.isdir(person_dir):
            for filename in os.listdir(person_dir):
                image_path = os.path.join(person_dir, filename)
                try:
                    image = face_recognition.load_image_file(image_path)
                    encoding = face_recognition.face_encodings(image)[0]
                    known_face_encodings.append(encoding)
                    known_face_names.append(name)
                except Exception as e:
                    print(f"Error loading {image_path}: {e}")

# Function to mark attendance in a CSV file
def mark_attendance(name):
    if name not in attendance_marked:  # Prevent duplicate entries
        now = datetime.now()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        file_exists = os.path.isfile('attendance.csv')

        with open('attendance.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:  # Add headers if file is new
                writer.writerow(['Name', 'Timestamp'])
            writer.writerow([name, timestamp])

        attendance_marked.add(name)
        print(f"Attendance marked for {name} at {timestamp}")

# Start Face Recognition
def start_face_recognition():
    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        messagebox.showerror("Error", "Unable to access the camera.")
        return

    while True:
        ret, frame = video_capture.read()
        if not ret:
            continue

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        face_locations = face_recognition.face_locations(rgb_frame, model="hog")
        face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)

            if matches[best_match_index] and face_distances[best_match_index] < 0.5:
                name = known_face_names[best_match_index]
                mark_attendance(name)

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
            cv2.putText(frame, name, (left, bottom + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        cv2.imshow('Attendance System', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()

# GUI Setup
root = tk.Tk()
root.title("Face Recognition Attendance System")
root.geometry("400x300")

# Register User Section
tk.Label(root, text="Face Recognition Attendance System", font=("Arial", 14, "bold")).pack(pady=10)

start_button = tk.Button(root, text="Start Attendance", command=start_face_recognition, bg="#4CAF50", fg="white")
start_button.pack(pady=10)

# Load known faces on startup
load_known_faces()

# Run the GUI
root.mainloop()
