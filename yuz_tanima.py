import cv2
import face_recognition
import os
import pickle
import tkinter as tk
from tkinter import simpledialog, filedialog
import pandas as pd
from datetime import datetime

# Function to load face encodings from a file
def load_encodings():
    if os.path.exists('encodings.pickle'):
        with open('encodings.pickle', 'rb') as f:
            encodings = pickle.load(f)
        return encodings
    else:
        return {}

# Function to save face encodings to a file
def save_encodings(encodings):
    with open('encodings.pickle', 'wb') as f:
        pickle.dump(encodings, f)

# Function to get user input using Tkinter
def get_user_input(prompt):
    return simpledialog.askstring("Input", prompt)

# Function to select an image file and encode the face
def add_face_from_image():
    while True:
        image_path = filedialog.askopenfilename(title="Bir fotoğraf seçin ")
        if not image_path:
            return

        # Load the image file and find face encodings
        image = face_recognition.load_image_file(image_path)
        image_face_encodings = face_recognition.face_encodings(image)

        if len(image_face_encodings) > 0:
            # Prompt for the name and student number of the person in the image
            name = get_user_input("Bu yüz için bir isim girin:")
            student_id = get_user_input("Bu yüz için bir öğrenci numarası girin:")
            face_encodings[(name, student_id)] = image_face_encodings[0]
            save_encodings(face_encodings)
            print(f"Face encoding for {name} (ID: {student_id}) added successfully.")
        else:
            print("Yüz bulunamadı.Farklı bir yüz seçin")

        # Ask if the user wants to add another face
        if get_user_input("Yeni bir yüz eklemek istiyor musunuz ?(evet/hayır)") != 'evet':
            break

# Load existing face encodings
face_encodings = load_encodings()

# Set to store names of faces for which attendance has been logged
attendance_logged_faces = set()

# Tkinter setup for initial dialogs
root = tk.Tk()
root.withdraw()  # Hide the main window

# Get the file name using Tkinter
fileName = get_user_input("Yoklama tarihini giriniz:")

# Check if the file exists, create it if not
excel_file = fileName + ' tarihli yoklama.xlsx'
if not os.path.exists(excel_file):
    df = pd.DataFrame(columns=["İsim", "Öğrenci No", "Zaman"])
    df.to_excel(excel_file, index=False)

# Ask if the user wants to add a face from an image file
if get_user_input("Yeni bir yüz eklemek istiyor musunuz ?(evet/hayır)") == 'evet':
    add_face_from_image()

# Open a video capture object (0 for the default camera)
cap = cv2.VideoCapture(0)
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)  # Set width
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480) # Set height

while True:
    # Read a frame from the video capture
    ret, frame = cap.read()

    # Find face locations and encodings in the current frame
    face_locations = face_recognition.face_locations(frame)
    current_face_encodings = face_recognition.face_encodings(frame, face_locations)

    for face_encoding, face_location in zip(current_face_encodings, face_locations):
        # Check if the face is already known
        matches = face_recognition.compare_faces(list(face_encodings.values()), face_encoding)
        name = "Tanimlanmamis yuz"
        student_id = ""

        # If a match is found, use the name and student ID of the known face
        if True in matches:
            first_match_index = matches.index(True)
            name, student_id = list(face_encodings.keys())[first_match_index]

        # Choose the color based on whether the face is known or Tanimlanmamis yuz
        box_color = (0, 255, 0) if name != "Tanimlanmamis yuz" else (0, 0, 255)

        # Draw a rectangle around the face and display the name and student ID (if known)
        top, right, bottom, left = face_location
        cv2.rectangle(frame, (left, top), (right, bottom), box_color, 2)
        display_text = name if name == "Tanimlanmamis yuz" else f"{name} ({student_id})"
        cv2.putText(frame, display_text, (left, top - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, box_color, 2)

        # Log attendance if the face is not in the set and is not Tanimlanmamis yuz
        if name != "Tanimlanmamis yuz" and (name, student_id) not in attendance_logged_faces:
            # Append to Excel file
            current_time = datetime.now().strftime('%d-%m-%y %H:%M:%S')
            new_entry = pd.DataFrame([[name, student_id, current_time]], columns=["İsim", "Öğrenci No", "Zaman"])
            if not new_entry.empty and not new_entry.isna().all(axis=None):
                df = pd.read_excel(excel_file)
                df = pd.concat([df, new_entry], ignore_index=True)
                df.to_excel(excel_file, index=False)
                attendance_logged_faces.add((name, student_id))

    # Display the frame with face detection
    cv2.imshow('Face Recognition', frame)

    # Break the loop when 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the video capture object and close the window
cap.release()
cv2.destroyAllWindows()

