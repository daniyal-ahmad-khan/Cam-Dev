import cv2
import socket
import pickle
import struct
from ultralytics import YOLO



model = YOLO("yolov8n.pt")
# Create a socket object
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# Get local machine name
host = socket.gethostname()

# Port for your service
port = 12345

client_socket.connect((host, port))

data = b""
payload_size = struct.calcsize("L")

while True:
    while len(data) < payload_size:
        packet = client_socket.recv(4096)  # 4K
        if not packet: break
        data += packet

    packed_msg_size = data[:payload_size]
    data = data[payload_size:]
    msg_size = struct.unpack("L", packed_msg_size)[0]

    while len(data) < msg_size:
        data += client_socket.recv(4096)

    frame_data = data[:msg_size]
    data = data[msg_size:]

    # Extract frame
    frame = pickle.loads(frame_data)
    results = model(frame, device=0)
    annotated_frame = results[0].plot()
    cv2.imshow("YOLO Inference", annotated_frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

client_socket.close()
cv2.destroyAllWindows()
