from camera_manager import CameraManager
import cv2
import time

def display_cameras():
    with CameraManager() as cam_manager:
        print("Detected cameras:", list(cam_manager.cameras.keys()))
        if list(cam_manager.cameras.keys()):
            try:
                while True:
                    for index in cam_manager.cameras.keys():
                        frame = cam_manager.get_frame(index)
                        if frame is not None:
                            cv2.imshow(f'Camera Index: {index}', frame)
                        
                        # Press 'q' to quit the display
                        if cv2.waitKey(1) & 0xFF == ord('q'):
                            raise KeyboardInterrupt()

                    # Delay to reduce CPU usage
                    time.sleep(0.1)
            except KeyboardInterrupt:
                print("Exiting...")
            finally:
                cv2.destroyAllWindows()

if __name__ == "__main__":
    display_cameras()