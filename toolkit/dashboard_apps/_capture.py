import cv2
import requests
import numpy as np
import time
import sys

def capture_image(url):
    try:
        response = requests.get(url)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Convert the binary image data to a NumPy array
            img_array = np.frombuffer(response.content, dtype=np.uint8)
            # Decode the array into an OpenCV image
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            return img
        else:
            print(f"Error: Unable to fetch image. Status code: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")
    return None

def main(url):
    print(f"--> Init: {url}")

    # Initialize variables for FPS calculation
    frame_count = 0
    total_time_count = 0

    while True:
        # Capture image from the specified URL
        print(f"--> Capture & display loop - received frames: {frame_count}")
        # Capture
        start_time = time.time()
        image = capture_image(url)
        elapsed_time = time.time() - start_time
        # Display the image
        if image is not None:
            # Add FPS counter
            frame_count += 1
            total_time_count += elapsed_time
            fps = frame_count / total_time_count        # average FPS: total frame count / total receive time
            cv2.putText(image, f"FPS: {fps:.2f} {elapsed_time:.1f}s", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            # Display the image
            cv2.imshow(url, image)

        # Break the loop if 'q' is pressed
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Release the OpenCV window and close it
    cv2.destroyAllWindows()

if __name__ == "__main__":
    args = sys.argv
    print("Start python script: {}".format(args[0]))
    devfid = '10.0.1.106'       # Default for test
    if len(args) > 1:
        devfid = args[1]
    url = f"http://{devfid}/cam/"
    main(url=url)

