import cv2
import face_recognition
import numpy as np
import os
from datetime import datetime
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import csv
import logging
import threading
import platform
import subprocess
from PIL import Image, ImageTk

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
            recorded_names = {}
            for line in lines:
                stored_name, stored_time, stored_exit_time = line.strip().split(',')
                recorded_names[stored_name] = (stored_time, stored_exit_time)

            if name in recorded_names:
                # If the person has already checked in, check if they are checking out
                check_in_time, exit_time = recorded_names[name]
                if not exit_time:  # No exit time recorded yet
                    check_in_datetime = datetime.strptime(check_in_time, '%Y-%m-%d %H:%M:%S')
                    if (now - check_in_datetime).total_seconds() >= 8 * 3600:  # 8 hours later
                        # Mark exit time
                        recorded_names[name] = (check_in_time, timestamp)
                        logging.info(f"Marked exit time for {name}")
                        messagebox.showinfo("Success", f"Exit time marked for {name} at {timestamp}")
                    else:
                        messagebox.showinfo("Info", f"{name} cannot check out before 8 hours.")
                else:
                    messagebox.showinfo("Info", f"Exit time already marked for {name} at {exit_time}")
            else:
                # First time marking attendance (entry time)
                recorded_names[name] = (timestamp, "")
                logging.info(f"Marked entry time for {name}")
                messagebox.showinfo("Success", f"Entry time marked for {name} at {timestamp}")

            # Write updated attendance records back to the file
            f.seek(0)
            f.truncate()
            f.write("Name,Timestamp,ExitTime\n")
            for name, (entry_time, exit_time) in recorded_names.items():
                f.write(f"{name},{entry_time},{exit_time}\n")

    except FileNotFoundError:
        with open('attendance.csv', 'w') as f:
            f.write("Name,Timestamp,ExitTime\n")
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
    attendance_window.geometry("800x400")

    columns = ("Name", "Entry Time", "Exit Time", "Status")
    tree = ttk.Treeview(attendance_window, columns=columns, show="headings")
    tree.heading("Name", text="Name")
    tree.heading("Entry Time", text="Entry Time")
    tree.heading("Exit Time", text="Exit Time")
    tree.heading("Status", text="Status")
    tree.pack(fill="both", expand=True)

    try:
        with open("attendance.csv", "r") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                name, entry_time, exit_time = row
                status = "Complete Shift" if exit_time else "Incomplete Shift"
                tree.insert("", "end", values=(name, entry_time, exit_time, status))
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
    global is_running, video_capture, camera_label
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

    # Create a label to display the camera feed
    global camera_label
    camera_label = tk.Label(root)
    camera_label.pack()

    # Start updating the camera feed
    update_camera_feed()

def update_camera_feed():
    global is_running, video_capture, camera_label
    if not is_running:
        return

    try:
        ret, frame = video_capture.read()
        if ret:
            # Resize the frame for better performance
            small_frame = cv2.resize(frame, (0, 0), fx=0.5, fy=0.5)
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)

            # Perform face recognition on the frame
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

                # Draw rectangles and labels on the frame
                top *= 2
                right *= 2
                bottom *= 2
                left *= 2
                cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)
                cv2.putText(frame, name, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2)

            # Convert the frame to an image compatible with tkinter
            img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
            imgtk = ImageTk.PhotoImage(image=img)

            # Update the label with the new frame
            camera_label.imgtk = imgtk
            camera_label.configure(image=imgtk)

        # Schedule the next frame update
        root.after(10, update_camera_feed)  # Update every 10ms
    except Exception as e:
        logging.error(f"Error updating camera feed: {e}")

# Function to stop face recognition
def stop_face_recognition():
    global is_running, video_capture, camera_label
    is_running = False
    if video_capture.isOpened():
        video_capture.release()  # Ensure video capture is released
        logging.info("Camera released successfully")

    # Remove the camera feed label
    if 'camera_label' in globals():
        camera_label.pack_forget()

    logging.info("Attendance stopped manually")
    messagebox.showinfo("Info", "Attendance has been stopped.")

# GUI Setup
root = tk.Tk()
root.title("Face Recognition Attendance System")
root.geometry("800x600")

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

# Global variable for attendance session
attendance_session = set()

root.mainloop()