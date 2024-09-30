import cv2

def find_available_cameras(max_index=10):
    # List to hold the indices of available cameras
    available_cameras = []

    # Try to open each camera index from 0 to max_index
    for index in range(max_index):
        # Attempt to create a video capture object
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            # If the camera is available, add the index to the list
            available_cameras.append(index)
            # Release the camera device
            cap.release()
        else:
            print(f"Camera at index {index} is not available.")

    return available_cameras

# Define the maximum index to check
max_camera_index = 10  # You can increase this number based on how many devices you expect

# Get the list of available camera indices
camera_indices = find_available_cameras(max_camera_index)
print("Available camera indices:", camera_indices)
