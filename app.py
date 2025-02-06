import cv2
import face_recognition
import numpy as np
import os
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import csv
import logging
import time
import platform
import subprocess

# Set up logging
logging.basicConfig(filename='attendance_system.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Path to the directory containing known faces
KNOWN_FACES_DIR = "known_faces"

# Initialize lists to store known face encodings and their names
known_face_encodings = []
known_face_names = []

# Global flag to control face recognition
is_running = False

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
                    encoding = face_recognition.face_encodings(image)
                    if encoding:  # Check if face encoding is found
                        known_face_encodings.append(encoding[0])
                        known_face_names.append(name)
                        logging.info(f"Loaded face: {name}")
                    else:
                        logging.warning(f"No face encoding found for {name}")
                except Exception as e:
                    logging.error(f"Error loading image {image_path}: {e}")

# Function to mark attendance in a CSV file
def mark_attendance(name):
    try:
        now = datetime.now()
        timestamp = now.strftime('%Y-%m-%d %H:%M:%S')
        with open('attendance.csv', 'r+') as f:
            lines = f.readlines()
            recorded_names = [line.split(',')[0] for line in lines]
            if name not in recorded_names:
                f.writelines(f'\n{name},{timestamp}')
                logging.info(f"Marked attendance for {name}")
                messagebox.showinfo("Success", f"Attendance marked for {name} at {timestamp}")
            else:
                # Find the last attendance for the same user and check time difference
                for line in lines:
                    stored_name, stored_time = line.strip().split(',')
                    if stored_name == name:
                        last_time = datetime.strptime(stored_time, '%Y-%m-%d %H:%M:%S')
                        time_diff = (now - last_time).total_seconds()
                        if time_diff < 60:
                            messagebox.showinfo("Duplicate Attendance", f"Attendance already marked for {name} at {stored_time}")
                        else:
                            f.writelines(f'\n{name},{timestamp}')
                            logging.info(f"Marked attendance for {name}")
                            messagebox.showinfo("Success", f"Attendance marked for {name} at {timestamp}")
                        return
    except FileNotFoundError:
        with open('attendance.csv', 'w') as f:
            f.write("Name,Timestamp\n")
        mark_attendance(name)
    except Exception as e:
        logging.error(f"Error marking attendance: {e}")
        messagebox.showerror("Error", f"Failed to mark attendance: {e}")

# Function to register a new user
def register_user():
    name = name_entry.get().strip()
    if not name:
        messagebox.showerror("Error", "Please enter a name.")
        return
    file_path = filedialog.askopenfilename(
        title="Select Image",
        filetypes=[("Image Files", "*.jpg *.jpeg *.png")]
    )
    if not file_path:
        messagebox.showerror("Error", "No image selected.")
        return
    try:
        person_dir = os.path.join(KNOWN_FACES_DIR, name)
        os.makedirs(person_dir, exist_ok=True)
        image_path = os.path.join(person_dir, os.path.basename(file_path))
        os.rename(file_path, image_path)
        load_known_faces()
        messagebox.showinfo("Success", f"User '{name}' registered successfully!")
        logging.info(f"Registered new user: {name}")
    except Exception as e:
        logging.error(f"Error registering user: {e}")
        messagebox.showerror("Error", f"Failed to register user: {e}")

# Function to view attendance records
def view_attendance():
    attendance_window = tk.Toplevel(root)
    attendance_window.title("Attendance Records")
    attendance_window.geometry("600x400")
    columns = ("Name", "Timestamp")
    tree = ttk.Treeview(attendance_window, columns=columns, show="headings")
    tree.heading("Name", text="Name")
    tree.heading("Timestamp", text="Timestamp")
    tree.pack(fill="both", expand=True)
    try:
        with open("attendance.csv", "r") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                tree.insert("", "end", values=row)
    except FileNotFoundError:
        messagebox.showinfo("Info", "No attendance records found.")
    except Exception as e:
        logging.error(f"Error viewing attendance: {e}")
        messagebox.showerror("Error", f"Failed to view attendance: {e}")

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
        logging.info(f"Attendance downloaded to {save_path}")
    except FileNotFoundError:
        messagebox.showinfo("Info", "No attendance records found.")
    except Exception as e:
        logging.error(f"Error downloading attendance: {e}")
        messagebox.showerror("Error", f"Failed to download attendance: {e}")


# Function to start face recognition
def start_face_recognition():
    global is_running, video_capture
    if is_running:
        messagebox.showwarning("Warning", "Attendance is already running.")
        return
    is_running = True

    if platform.system() == 'Darwin':  # macOS
        try:
            subprocess.run(["codesign", "-d", "--entitlements", ":-", "/Applications/Python 3.x/Python Launcher.app"],
                           check=True, capture_output=True)
        except subprocess.CalledProcessError:
            messagebox.showwarning("Warning",
                                   "This application may not have the necessary permissions to access the camera. Please check your privacy settings.")

    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        messagebox.showerror("Error", "Unable to access the camera.")
        logging.error("Unable to access the camera")
        is_running = False
        return

    attendance_session = set()

    while is_running:  # Use the global flag to control the loop
        try:
            ret, frame = video_capture.read()
            if not ret:
                logging.warning("Failed to capture frame. Attempting to reset camera...")
                video_capture.release()
                time.sleep(1)
                video_capture = cv2.VideoCapture(0)
                continue

            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            for (top, right, bottom, left), face_encoding in zip(face_locations, face_encodings):
                matches = face_recognition.compare_faces(known_face_encodings, face_encoding, tolerance=0.6)
                name = "Unknown"
                face_distances = face_recognition.face_distance(known_face_encodings, face_encoding)
                best_match_index = np.argmin(face_distances)
                if matches[best_match_index]:
                    name = known_face_names[best_match_index]
                    if name not in attendance_session:
                        mark_attendance(name)
                        attendance_session.add(name)
                        logging.info(f"Recognized and marked attendance for {name}")

                top *= 4
                right *= 4
                bottom *= 4
                left *= 4
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

            cv2.imshow('Face Recognition Attendance System', frame)

        except Exception as e:
            logging.error(f"Error in face recognition loop: {e}")
            time.sleep(1)  # Wait a bit before trying again

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    video_capture.release()
    cv2.destroyAllWindows()
    is_running = False  # Reset the flag when the loop ends


# Function to stop face recognition
def stop_face_recognition():
    global is_running, video_capture
    is_running = False
    if video_capture.isOpened():
        video_capture.release()  # Ensure video capture is released
        logging.info("Camera released successfully")
    cv2.destroyAllWindows()  # Close any open windows
    logging.info("Attendance stopped manually")
    messagebox.showinfo("Info", "Attendance has been stopped.")

# GUI Setup
root = tk.Tk()
root.title("Face Recognition Attendance System")
root.geometry("400x400")

# Register User Section
tk.Label(root, text="Register New User", font=("Arial", 14)).pack(pady=10)
tk.Label(root, text="Name:").pack()
name_entry = tk.Entry(root)
name_entry.pack()
register_button = tk.Button(root, text="Register", command=register_user)
register_button.pack(pady=5)

# View Attendance Section
view_button = tk.Button(root, text="View Attendance", command=view_attendance)
view_button.pack(pady=5)

# Download Attendance Section
download_button = tk.Button(root, text="Download Attendance", command=download_attendance)
download_button.pack(pady=5)

# Start and Stop Attendance Buttons
start_button = tk.Button(root, text="Start Attendance", command=start_face_recognition)
start_button.pack(pady=5)
stop_button = tk.Button(root, text="Stop Attendance", command=stop_face_recognition)
stop_button.pack(pady=5)

try:
    load_known_faces()
    logging.info("Known faces loaded successfully")
except Exception as e:
    logging.error(f"Error loading known faces: {e}")
    messagebox.showerror("Error", f"Failed to load known faces: {e}")

root.mainloop()