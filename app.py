import cv2
import face_recognition
import numpy as np
import os
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import csv
import logging
import threading
from PIL import Image, ImageTk
from geopy.geocoders import Nominatim
from fpdf import FPDF
import pandas as pd

# Set up logging
logging.basicConfig(
    filename="attendance_system.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

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
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        with open("attendance.csv", "r+") as f:
            lines = f.readlines()
            recorded_names = {}
            for line in lines:
                stored_name, stored_time, stored_exit_time = (
                    line.strip().split(",") if line.strip() else ("", "", "")
                )
                recorded_names[stored_name] = (stored_time, stored_exit_time)

            if name in recorded_names:
                # If the person has already checked in, check if they are checking out
                check_in_time, exit_time = recorded_names[name]
                if not exit_time:  # No exit time recorded yet
                    check_in_datetime = datetime.strptime(check_in_time, "%Y-%m-%d %H:%M:%S")
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
        with open("attendance.csv", "w") as f:
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
        filetypes=[("Image Files", "*.jpg *.jpeg *.png")],
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


# Function to download attendance
def download_attendance():
    save_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV Files", "*.csv")],
        title="Save Attendance As",
    )
    if not save_path:  # User canceled the dialog
        return

    try:
        # Check if the attendance file exists
        if not os.path.exists("attendance.csv"):
            messagebox.showinfo("Info", "No attendance records found.")
            logging.info("No attendance records found during download.")
            return

        # Read the attendance file and write its content to the target file
        with open("attendance.csv", "r") as source_file:
            content = source_file.read()

        with open(save_path, "w") as target_file:
            target_file.write(content)

        # Notify the user that the download was successful
        messagebox.showinfo("Success", f"Attendance downloaded to {save_path}")
        logging.info(f"Attendance downloaded to {save_path}")

    except FileNotFoundError:
        messagebox.showerror("Error", "Attendance file not found.")
        logging.error("Attendance file not found during download.")

    except PermissionError:
        messagebox.showerror("Error", "Permission denied. Please check the save location.")
        logging.error("Permission denied during attendance download.")

    except Exception as e:
        messagebox.showerror("Error", f"Failed to download attendance: {e}")
        logging.error(f"Error downloading attendance: {e}")


# Function to start face recognition
def start_face_recognition():
    global is_running, video_capture, camera_label
    if is_running:
        messagebox.showwarning("Warning", "Attendance is already running.")
        return

    is_running = True

    # Open the camera
    video_capture = cv2.VideoCapture(0)
    if not video_capture.isOpened():
        messagebox.showerror("Error", "Unable to access the camera.")
        logging.error("Unable to access the camera")
        is_running = False
        return

    # Create a frame to hold the camera feed
    global camera_frame
    camera_frame = tk.Frame(root, width=950, height=715, bg="black")
    camera_frame.pack(pady=10)

    # Create a label to display the camera feed
    global camera_label
    camera_label = tk.Label(camera_frame, bg="black")
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
            # Resize the frame to fit the GUI (e.g., 640x480)
            target_width, target_height = 950, 715
            aspect_ratio = frame.shape[1] / frame.shape[0]
            if frame.shape[1] > target_width or frame.shape[0] > target_height:
                new_width = int(target_height * aspect_ratio)
                new_height = target_height
                if new_width > target_width:
                    new_width = target_width
                    new_height = int(target_width / aspect_ratio)
                frame = cv2.resize(frame, (new_width, new_height))

            # Perform face recognition on the resized frame
            small_frame = cv2.resize(frame, (0, 0), fx=0.25, fy=0.25)  # Downscale for faster processing
            rgb_small_frame = cv2.cvtColor(small_frame, cv2.COLOR_BGR2RGB)
            face_locations = face_recognition.face_locations(rgb_small_frame)
            face_encodings = face_recognition.face_encodings(rgb_small_frame, face_locations)

            # Check if any faces were detected
            if len(face_locations) == 0:
                # No faces detected, display "No Face Detected"
                cv2.putText(
                    frame,
                    "No Face Detected",  # Display message
                    (50, 50),  # Position in the top-left corner
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1.0,
                    (0, 0, 255),  # Red color
                    2,
                )
            else:
                # Process each detected face
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

                    # Scale back the face locations to match the resized frame
                    top *= 4
                    right *= 4
                    bottom *= 4
                    left *= 4

                    # Draw a rectangle around the face
                    cv2.rectangle(frame, (left, top), (right, bottom), (0, 255, 0), 2)

                    # Display the name or "Unknown" below the face
                    cv2.putText(
                        frame,
                        name,  # Display the name or "Unknown"
                        (left, bottom + 30),  # Position below the rectangle
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.9,
                        (255, 255, 255),  # White color
                        2,
                    )

            # Convert the frame to RGB for tkinter compatibility
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            # Convert the frame to an image compatible with tkinter
            img = Image.fromarray(rgb_frame)
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
    global is_running, video_capture, camera_label, camera_frame
    is_running = False
    if video_capture.isOpened():
        video_capture.release()  # Ensure video capture is released
        logging.info("Camera released successfully")

    # Remove the camera feed frame and label
    if "camera_frame" in globals():
        camera_frame.pack_forget()
        camera_label.pack_forget()

    logging.info("Attendance stopped manually")
    messagebox.showinfo("Info", "Attendance has been stopped.")


# Function to generate daily summary
def generate_daily_summary():
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        total_checkins = 0
        total_checkouts = 0
        incomplete_shifts = 0

        with open("attendance.csv", "r") as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                name, entry_time, exit_time = row
                if entry_time.startswith(today):
                    total_checkins += 1
                    if exit_time:
                        total_checkouts += 1
                    else:
                        incomplete_shifts += 1

        summary = (
            f"Daily Attendance Summary ({today}):\n"
            f"Total Check-Ins: {total_checkins}\n"
            f"Total Check-Outs: {total_checkouts}\n"
            f"Incomplete Shifts: {incomplete_shifts}"
        )
        messagebox.showinfo("Daily Summary", summary)
    except FileNotFoundError:
        messagebox.showinfo("Info", "No attendance records found.")
    except Exception as e:
        logging.error(f"Error generating daily summary: {e}")
        messagebox.showerror("Error", f"Failed to generate daily summary: {e}")

def get_location():
    geolocator = Nominatim(user_agent="attendance_system")
    location = geolocator.geocode("Your Address Here")  # Replace with dynamic address
    return f"{location.latitude}, {location.longitude}"

# GUI Setup
root = tk.Tk()
root.title("Face Recognition Attendance System")
root.geometry("800x600")

# Register User Section
register_frame = tk.Frame(root, padx=10, pady=10)
register_frame.pack(fill="x")
tk.Label(register_frame, text="Register New User", font=("Arial", 12)).pack(anchor="w")
tk.Label(register_frame, text="Name:").pack(anchor="w")
name_entry = tk.Entry(register_frame)
name_entry.pack(fill="x", pady=8)
register_button = tk.Button(register_frame, text="Register", command=register_user)
register_button.pack(fill="x", pady=8)

# Attendance Controls Section
controls_frame = tk.Frame(root, padx=5, pady=5)  # Define controls_frame here
controls_frame.pack(fill="x")  # Pack it to make it visible

# Add buttons to controls_frame
view_button = tk.Button(controls_frame, text="View Attendance List", command=view_attendance)
view_button.pack(side="left", padx=8)

download_button = tk.Button(controls_frame, text="Download Attendance List", command=download_attendance)
download_button.pack(side="left", padx=8)

start_button = tk.Button(controls_frame, text="Start Taking Attendance", command=start_face_recognition)
start_button.pack(side="left", padx=8)

stop_button = tk.Button(controls_frame, text="Stop Taking Attendance", command=stop_face_recognition)
stop_button.pack(side="left", padx=8)

# Add the summary button to controls_frame
summary_button = tk.Button(controls_frame, text="Generate Daily Summary", command=generate_daily_summary)
summary_button.pack(side="left", padx=8)

# Initialize global variables
video_capture = None
camera_label = None
camera_frame = None
attendance_session = set()

try:
    load_known_faces()
    logging.info("Known faces loaded successfully")
except Exception as e:
    logging.error(f"Error loading known faces: {e}")
    messagebox.showerror("Error", f"Failed to load known faces: {e}")

root.mainloop()