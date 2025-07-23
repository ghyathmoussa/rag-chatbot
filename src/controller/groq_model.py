from src.models.groq_model import GroqModel

class GroqController:
    def __init__(self):
        self.groq_model = GroqModel()

    def process_and_store(self, file_path: str):
        return self.groq_model.process_and_store(file_path)