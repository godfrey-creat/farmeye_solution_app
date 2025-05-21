from flask import Blueprint, request, jsonify, current_app
import os
import numpy as np
import base64
import json
from io import BytesIO
from PIL import Image
import traceback
import cv2

# Import YOLO from Ultralytics
try:
    from ultralytics import YOLO
except ImportError:
    current_app.logger.error(
        "Could not import ultralytics YOLO. Make sure it's installed"
    )

feed_bp = Blueprint("feed", __name__, url_prefix="/feed")


class YoloDetector:
    """
    Utility class for YOLO model integration for maize/weed detection.
    Uses the actual YOLOv8 model for inference.
    """

    def __init__(self, model_path=None):
        """Initialize the detector with the given model path"""
        if model_path is None:
            # Default model path
            model_path = os.path.join(
                current_app.root_path, "utils", "maize_weed_detection.pt"
            )

        self.model_path = model_path
        self.model = None
        self.is_loaded = False
        self.class_names = ["maize", "weed"]

        current_app.logger.info(
            f"Initializing YOLO detector with model at: {model_path}"
        )
        self.load_model()

    def load_model(self):
        """Load the YOLO model"""
        try:
            # Load the actual YOLOv8 model
            self.model = YOLO(self.model_path)

            self.is_loaded = True
            current_app.logger.info("YOLO model loaded successfully")
            return True
        except Exception as e:
            current_app.logger.error(f"Error loading YOLO model: {str(e)}")
            traceback.print_exc()
            return False

    def detect(self, image_data):
        """
        Detect objects in the image

        Args:
            image_data: Image data (PIL Image or numpy array)

        Returns:
            List of detections with format:
            [
                {
                    'class': 'class_name',
                    'confidence': float,
                    'bbox': [x, y, width, height]
                },
                ...
            ]
        """
        if not self.is_loaded:
            self.load_model()

        if not self.is_loaded:
            current_app.logger.error("Failed to load model, cannot perform detection")
            return []

        try:
            # Ensure we have numpy array for detection
            if isinstance(image_data, Image.Image):
                # Convert PIL Image to numpy array (RGB)
                img_np = np.array(image_data)
                # Convert to BGR for OpenCV
                img_np = cv2.cvtColor(img_np, cv2.COLOR_RGB2BGR)
            else:
                img_np = image_data

            # Run inference using YOLOv8
            results = self.model(img_np)

            # Process results to the expected format
            detections = self._process_results(results)

            return detections

        except Exception as e:
            current_app.logger.error(f"Error in YOLO detection: {str(e)}")
            traceback.print_exc()
            return []

    def _process_results(self, results):
        """
        Process results from the YOLOv8 model

        Args:
            results: Results from YOLOv8 model.predict()

        Returns:
            List of detection objects in standard format
        """
        detections = []

        # Extract the first result (batch size is 1)
        result = results[0]

        # Get the boxes, confidence scores, and class IDs
        boxes = result.boxes.xyxy.cpu().numpy()  # x1, y1, x2, y2 format
        confs = result.boxes.conf.cpu().numpy()
        cls_ids = result.boxes.cls.cpu().numpy().astype(int)

        # Convert to our detection format
        for i, box in enumerate(boxes):
            x1, y1, x2, y2 = box

            # Convert to top-left corner and width/height format
            x = int(x1)
            y = int(y1)
            width = int(x2 - x1)
            height = int(y2 - y1)

            conf = float(confs[i])
            cls_id = int(cls_ids[i])

            # Ensure class_id is within range
            if cls_id < len(self.class_names):
                cls_name = self.class_names[cls_id]
            else:
                cls_name = f"unknown_{cls_id}"

            detections.append(
                {"class": cls_name, "confidence": conf, "bbox": [x, y, width, height]}
            )

        return detections


# Create a global detector instance
detector = YoloDetector()


@feed_bp.route("/detect", methods=["POST"])
def detect_objects():
    """API endpoint for YOLO object detection"""
    try:
        if "image" not in request.files:
            # Check if image is sent as base64
            if "image_data" in request.form:
                base64_data = request.form["image_data"]
                # Remove data URL prefix if present
                if "," in base64_data:
                    base64_data = base64_data.split(",")[1]

                # Decode base64 to image
                image_data = base64.b64decode(base64_data)
                image = Image.open(BytesIO(image_data))
            else:
                return (
                    jsonify(
                        {
                            "success": False,
                            "error": "No image provided",
                            "detections": [],
                        }
                    ),
                    400,
                )
        else:
            # Get image file
            image_file = request.files["image"]
            image = Image.open(image_file)

        # Perform detection with actual model
        detections = detector.detect(image)

        return jsonify({"success": True, "detections": detections})

    except Exception as e:
        current_app.logger.error(f"Error in detect endpoint: {str(e)}")
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e), "detections": []}), 500


def init_app(app):
    """Register the feed blueprint with the app"""
    app.register_blueprint(feed_bp)
