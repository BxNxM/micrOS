import cv2
import requests
import numpy as np
import time
import sys
import socket

RESOLVED_URLS = {}

def capture_image(url):
    # Resolve and cache hostname (IP address)
    try:
        # Extracting the hostname from the URL
        hostname = url.split('/')[2]
        # Resolving the IP address
        ip_address = socket.gethostbyname(hostname)
        resolved_url = url.replace(hostname, ip_address)
        RESOLVED_URLS[url] = resolved_url
    except Exception as e:
        print(f"URL has no hostname: {url} - fallback to u resolved url: {e}")
        RESOLVED_URLS[url] = url            # fallback
    # Run request...
    try:
        response = requests.get(RESOLVED_URLS[url], timeout=5)
        # Check if the request was successful (status code 200)
        if response.status_code == 200:
            # Convert the binary image data to a NumPy array
            img_array = np.frombuffer(response.content, dtype=np.uint8)
            # Decode the array into an OpenCV image
            img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
            return img
        else:
            print(f"Error: Unable to fetch image. Status code: {response.status_code}")
    except requests.Timeout:
        print("Error: The request timed out")
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
            # Getting the resolution information
            height, width, _ = image.shape
            #print(f"Image resolution: {width}x{height}, Channels: {channels}")
            cv2.putText(image, f"{width}x{height}", (width-70, height-10), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
            cv2.putText(image, "Press q to quit.", (width-110, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
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
    url = f"http://{devfid}.local/cam/snapshot"
    main(url=url)

