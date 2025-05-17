import os
import openai

def generate_ten_day_advisory(soil_moisture, weather, satellite, model_prediction):
    """
    Generate a ten-day advisory using ChatGPT 3.5 based on input data.
    Returns a dict with action, description, due, and priority.
    """
    openai.api_key = os.getenv("OPENAI_API_KEY")
    prompt = f"""
    You are an agricultural advisor. Based on the following data, generate a 10-day actionable advisory for a farmer, including irrigation, pest control, and general crop management.
    Soil moisture: {soil_moisture}
    Weather forecast: {weather}
    Satellite analysis: {satellite}
    Model predictions: {model_prediction}
    
    Please provide the advice in the following JSON format:
    {{
        "action": "<Action Title>",
        "description": "<Detailed actionable advice for the next ten days. Include irrigation and pest control if relevant.>",
        "due": "<Due date or time frame>",
        "priority": "<High|Medium|Low>"
    }}
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "system", "content": prompt}],
            max_tokens=250,
            temperature=0.7,
        )
        import json
        content = response.choices[0].message['content']
        advisory = json.loads(content)
        return advisory
    except Exception as e:
        # fallback
        return dict(
            action="General Advisory",
            description="Could not generate advisory at this time.",
            due="N/A",
            priority="Low"
        )