# app/utils/best_crop_analysis_model.py
import torch
from PIL import Image
from torchvision import transforms
import os
from .. import app

# Load your trained model
MODEL_PATH = os.path.join(app.root_path, 'models', 'best_crop_analysis_model.pth')
model = None  # This would be your loaded PyTorch model
classes = ['Healthy', 'Disease1', 'Disease2', 'Disease3']  # Your actual classes
crop_types = ['Maize', 'Wheat', 'Rice', 'Soybean']  # Your actual crop types

def load_model():
    global model
    if model is None and os.path.exists(MODEL_PATH):
        model = torch.load(MODEL_PATH, map_location='cpu')
        model.eval()

def predict_crop_health(image_path):
    """Predict crop health from image"""
    try:
        load_model()
        if not model or not image_path:
            return "Unknown"
            
        image = Image.open(image_path)
        transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        image_tensor = transform(image).unsqueeze(0)
        
        with torch.no_grad():
            outputs = model(image_tensor)
            _, preds = torch.max(outputs, 1)
            
        return classes[preds[0]]
    except Exception as e:
        app.logger.error(f"Error predicting crop health: {str(e)}")
        return "Unknown"

def predict_crop_type(image_path):
    """Predict crop type from image"""
    try:
        load_model()
        if not model or not image_path:
            return "Unknown"
            
        image = Image.open(image_path)
        transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        image_tensor = transform(image).unsqueeze(0)
        
        with torch.no_grad():
            outputs = model(image_tensor)
            _, preds = torch.max(outputs, 1)
            
        return crop_types[preds[0]]
    except Exception as e:
        app.logger.error(f"Error predicting crop type: {str(e)}")
        return "Unknown"

def predict_disease_class(image_path):
    """Predict disease class from image"""
    try:
        load_model()
        if not model or not image_path:
            return "None detected"
            
        image = Image.open(image_path)
        transform = transforms.Compose([
            transforms.Resize(256),
            transforms.CenterCrop(224),
            transforms.ToTensor(),
            transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
        ])
        image_tensor = transform(image).unsqueeze(0)
        
        with torch.no_grad():
            outputs = model(image_tensor)
            _, preds = torch.max(outputs, 1)
            
        disease = classes[preds[0]]
        return disease if disease != "Healthy" else "None detected"
    except Exception as e:
        app.logger.error(f"Error predicting disease class: {str(e)}")
        return "None detected"