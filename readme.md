# Face Recognition Attendance System

This project is a Face Recognition Attendance System developed using Python, `OpenCV`, and `face_recognition`. The system recognizes faces through your webcam and marks attendance for registered users. It saves the attendance data in a CSV file with timestamps and provides a GUI interface for user interaction.

## Features

- **User Registration**: Register a new user by uploading their photo.
- **Face Recognition**: The system captures faces in real-time using a webcam and matches them with registered users.
- **Attendance Logging**: Attendance is logged with a timestamp whenever a registered user's face is recognized.
- **View Attendance**: View the recorded attendance in a CSV format.
- **Download Attendance**: Download the attendance data as a CSV file.
- **Start/Stop Recognition**: Start and stop the real-time face recognition process with buttons.

## Requirements

- Python 3.x
- Libraries:
  - `opencv-python`
  - `face_recognition`
  - `numpy`
  - `tkinter`
  - `os`
  - `datetime`
  - `csv`
  - `logging`
  - `platform`
  - `subprocess`
  - `PIL` (for image file handling)

You can install the necessary libraries using pip:

```bash
pip install opencv-python face_recognition numpy Pillow
```

## Setup

1. **Create `known_faces` Directory**: 
   Create a directory named `known_faces` in the project root directory. This is where the photos of registered users will be stored.

2. **Register New Users**:
   - Enter the user name in the provided text field.
   - Select an image file (JPEG/PNG) containing the user's face when prompted.
   - The image will be saved in a folder named after the user inside the `known_faces` directory.

3. **Run the System**:
   - Press the **Start Attendance** button to begin the face recognition process.
   - The system will continuously monitor for faces, and when a registered user's face is detected, their attendance will be recorded with a timestamp.
   - To stop the process, press the **Stop Attendance** button.

4. **View Attendance**:
   - Click on **View Attendance** to open a window that displays the recorded attendance.

5. **Download Attendance**:
   - Click on **Download Attendance** to download the attendance data as a CSV file to your local machine.

## Directory Structure

```
Face_Recognition_Attendance_System/
├── known_faces/            # Folder containing user photos
│   └── JohnDoe/            # Subfolder for each registered user
│       └── john_doe.jpg    # User's photo for recognition
├── attendance.csv          # File to store attendance data
├── attendance_system.py    # Main Python script (this file)
└── attendance_system.log   # Log file to track system activity
```

## How It Works

1. **User Registration**: When a user registers, their face encoding is extracted and stored in the `known_faces` directory. Each user has their own folder, and photos are saved inside it.
2. **Face Recognition**: The system uses the webcam to capture frames, performs face detection, and compares the detected faces with the stored face encodings. When a match is found, the user's attendance is logged in the `attendance.csv` file.
3. **Attendance**: The system records the user's name and timestamp in the CSV file every time they are recognized.

## Dependencies

- `opencv-python`: Used for capturing video frames from the webcam.
- `face_recognition`: Used for face detection and encoding.
- `numpy`: Required by `face_recognition` for array manipulations.
- `tkinter`: Used for building the graphical user interface (GUI).
- `Pillow`: For handling images.

## Troubleshooting

- **Unable to access camera**: Make sure your webcam is connected and not being used by another application. On macOS, you may need to adjust camera permissions.
- **No face recognized**: Ensure the image is clear and the person's face is fully visible. The system may require good lighting and a clear view of the face to work effectively.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- `face_recognition`: The `face_recognition` library provides a simple API for face detection and recognition.
- `OpenCV`: The `opencv-python` library helps to capture frames from the webcam and process the video.
