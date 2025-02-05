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

# Load known faces and encode them
def load_known_faces():
    global known_face_encodings, known_face_names
    print("Loading known faces...")
    known_face_encodings.clear()
    known_face_names.clear()
    for name in os.listdir(KNOWN_FACES_DIR):
        person_dir = os.path.join(KNOWN_FACES_DIR, name)
        if os.path.isdir(person_dir):  # Ensure it's a directory
            for filename in os.listdir(person_dir):
                image_path = os.path.join(person_dir, filename)
                try:
                    image = face_recognition.load_image_file(image_path)
                    encoding = face_recognition.face_encodings(image)[0]
                    known_face_encodings.append(encoding)
                    known_face_names.append(name)
                    print(f"Loaded face for {name} from {image_path}")
                except Exception as e:
                    print(f"Error loading image {image_path}: {e}")
    print(f"Loaded {len(known_face_encodings)} known faces.")

# Function to mark attendance in a CSV file
def mark_attendance(name):
    with open('attendance.csv', 'a') as f:
        now = datetime.now()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        f.writelines(f'\n{name},{timestamp}')
        print(f"Attendance marked for {name} at {timestamp}")

# Function to register a new user
def register_user():
    name = name_entry.get().strip()
    if not name:
        messagebox.showerror("Error", "Please enter a name.")
        return

    # Open file dialog to select an image
    file_path = filedialog.askopenfilename(
        title="Select Image",
        filetypes=[("Image Files", "*.jpg *.jpeg *.png")]
    )
    if not file_path:
        messagebox.showerror("Error", "No image selected.")
        return

    # Save the image to the known_faces directory
    person_dir = os.path.join(KNOWN_FACES_DIR, name)
    os.makedirs(person_dir, exist_ok=True)
    image_path = os.path.join(person_dir, os.path.basename(file_path))
    os.rename(file_path, image_path)

    # Reload known faces
    load_known_faces()
    messagebox.showinfo("Success", f"User '{name}' registered successfully!")

# Function to view attendance records
def view_attendance():
    attendance_window = tk.Toplevel(root)
    attendance_window.title("Attendance Records")
    attendance_window.geometry("600x400")

    # Create a treeview to display attendance records
    columns = ("Name", "Timestamp")
    tree = ttk.Treeview(attendance_window, columns=columns, show="headings")
    tree.heading("Name", text="Name")
    tree.heading("Timestamp", text="Timestamp")
    tree.pack(fill="both", expand=True)

    # Load attendance records from the CSV file
    try:
        with open("attendance.csv", "r") as f:
            reader = csv.reader(f)
            for row in reader:
                tree.insert("", "end", values=row)
    except FileNotFoundError:
        messagebox.showinfo("Info", "No attendance records found.")

# Function to download attendance as CSV
def download_attendance():
    save_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv")],
        title="Save Attendance As"
    )
    if not save_path:
        return

    try:
        with open("attendance.csv", "r") as source, open(save_path, "w") as target:
            target.write(source.read())
        messagebox.showinfo("Success", f"Attendance downloaded to {save_path}")
    except FileNotFoundError:
        messagebox.showinfo("Info", "No attendance records found.")

# Start Face Recognition
import time

def start_face_recognition():
    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        messagebox.showerror("Error", "Unable to access the camera.")
        return

    # Set lower resolution for better performance
    video_capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Set width to 640 pixels
    video_capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)  # Set height to 480 pixels

    frame_count = 0  # To skip frames
    while True:
        ret, frame = video_capture.read()
        if not ret:
            print("Failed to grab frame. Retrying...")
            continue

        frame_count += 1
        if frame_count % 3 != 0:  # Process every 3rd frame
            continue

        rgb_frame = frame[:, :, ::-1]

        # Debug: Measure time for face detection
        start_time = time.time()
        face_locations = face_recognition.face_locations(rgb_frame, model="hog")  # Use HOG for faster detection
        print(f"Face detection took {time.time() - start_time:.2f} seconds")
        print(f"Detected {len(face_locations)} face(s).")

        if len(face_locations) == 0:
            print("No faces detected. Skipping encoding.")
            continue

        # Debug: Measure time for face encoding
        start_time = time.time()
        try:
            face_encodings = face_recognition.face_encodings(rgb_frame, known_face_locations=face_locations)
        except Exception as e:
            print(f"Error during face encoding: {e}")
            continue
        print(f"Face encoding took {time.time() - start_time:.2f} seconds")

        for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
            matches = face_recognition.compare_faces(known_face_encodings, face_encoding)
            name = "Unknown"

            face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
            best_match_index = np.argmin(face_distances)

            # Debug: Print matching details
            print(f"Best match index: {best_match_index}, Matches: {matches}, Face distances: {face_distances}")

            threshold = 0.6  # Adjust threshold if needed
            if face_distances[best_match_index] <= threshold:
                name = known_face_names[best_match_index]
                mark_attendance(name)
                print(f"Attendance marked for {name}.")
            else:
                print("No match found for the detected face.")

            cv2.rectangle(frame, (left, top), (right, bottom), (0, 0, 255), 2)
            cv2.rectangle(frame, (left, bottom - 35), (right, bottom), (0, 0, 255), cv2.FILLED)
            font = cv2.FONT_HERSHEY_DUPLEX
            cv2.putText(frame, name, (left + 6, bottom - 6), font, 0.5, (255, 255, 255), 1)

        cv2.imshow('Face Recognition Attendance System', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()

# GUI Setup
root = tk.Tk()
root.title("Face Recognition Attendance System")
root.geometry("400x300")

# Suppress macOS camera deprecation warning
import os
os.environ["OPENCV_VIDEOIO_PRIORITY_MSMF"] = "0"

# Register User Section
tk.Label(root, text="Register New User", font=("Arial", 14)).pack(pady=10)
tk.Label(root, text="Name:").pack()
name_entry = tk.Entry(root)
name_entry.pack()

register_button = tk.Button(root, text="Register", command=register_user)
register_button.pack(pady=10)

# View Attendance Section
view_button = tk.Button(root, text="View Attendance", command=view_attendance)
view_button.pack(pady=10)

# Download Attendance Section
download_button = tk.Button(root, text="Download Attendance", command=download_attendance)
download_button.pack(pady=10)

# Start Face Recognition Button
start_button = tk.Button(root, text="Start Face Recognition", command=start_face_recognition)
start_button.pack(pady=10)

# Load known faces on startup
load_known_faces()

# Run the GUI
root.mainloop()