from deepface import DeepFace
import json

def load_model():
    model = DeepFace.build_model("Emotion")
    metadata = {
        "model_name": "DeepFace-Emotion",
        "loaded": True
    }
    with open("model_metadata.json", "w") as f:
        json.dump(metadata, f)
    print("Model loaded and metadata saved.")

if __name__ == "__main__":
    load_model()
