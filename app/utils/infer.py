from ultralytics import YOLO
import cv2  # Import OpenCV for video handling
import time
import os


def run_inference_on_video(
    video_path,
    model_path=r"C:\Users\snmax\OneDrive\Desktop\farmeye_solution_app\app\utils\farmeye_final.pt",
    show_predictions=True,
    save_predictions=False,
    save_path="predictions.mp4",
):
    """
    Runs inference on a video using a YOLO model, with options to display and save the results.

    Args:
        video_path (str): Path to the video file.
        model_path (str, optional): Path to the YOLO model file (.pt).
            Defaults to 'C:\\Users\\snmax\\OneDrive\\Desktop\\farmeye_solution_app\\app\\utils\\farmeye_final.pt'.
        show_predictions (bool, optional): Whether to display the video with
            predictions in real-time. Defaults to True.
        save_predictions (bool, optional): Whether to save the video with
            predictions to a file. Defaults to False.
        save_path (str, optional): Path to save the output video file.
    """
    # Load the YOLO model
    model = YOLO(model_path)

    # Check if the video file exists
    if not os.path.exists(video_path):
        print(f"Error: Video file not found at {video_path}")
        return

    # Open the video file
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"Error: Could not open video file: {video_path}")
        return

    # Get video properties for saving
    if save_predictions:
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fourcc = cv2.VideoWriter_fourcc(
            *"mp4v"
        )  # Use 'mp4v' for .mp4, other codecs may be used
        out = cv2.VideoWriter(save_path, fourcc, fps, (frame_width, frame_height))

    frame_count = 0
    start_time = time.time()

    try:
        while True:
            # Read a frame from the video
            ret, frame = cap.read()
            if not ret:
                print("End of video or error reading frame.")
                break  # Exit the loop if no frame is read

            frame_count += 1

            # Perform inference on the frame
            results = model(frame)  # YOLOv8 infers on the frame

            # Process and display/save results
            annotated_frame = results[0].plot()  # Annotate the frame with predictions

            if show_predictions:
                cv2.imshow("Video with Predictions", annotated_frame)
                # Press 'q' to quit the video display
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            if save_predictions:
                out.write(annotated_frame)  # Write the frame to the output video

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:  # Use a finally block to ensure resources are released
        # Release the video capture and writer objects
        cap.release()
        if save_predictions:
            out.release()
        cv2.destroyAllWindows()  # Ensure window is closed

    end_time = time.time()
    duration = end_time - start_time
    print(f"Processed {frame_count} frames in {duration:.2f} seconds.")
    if frame_count > 0:
        fps = frame_count / duration
        print(f"Average FPS: {fps:.2f}")
    else:
        print("No frames were processed.")
    print("Inference complete.")


if __name__ == "__main__":
    # Get the video path from the user (you can change this to a fixed path for testing)
    video_path = input("Enter the path to your video file: ")

    # Run inference on the video
    run_inference_on_video(
        video_path,
        show_predictions=True,  # Set to False to disable showing video
        save_predictions=False,  # Set to True to save the output video
        save_path="output.mp4",
    )  # Change the output path as needed.
