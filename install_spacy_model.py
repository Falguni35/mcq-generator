import subprocess
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def install_spacy_model():
    """Install the spaCy English model required for MCQ generation"""
    try:
        logger.info("Installing spaCy English model...")
        result = subprocess.run([
            sys.executable, "-m", "spacy", "download", "en_core_web_sm"
        ], capture_output=True, text=True, check=True)
        
        logger.info("spaCy model installed successfully!")
        logger.info(result.stdout)
        
        # Test the model
        import spacy
        nlp = spacy.load("en_core_web_sm")
        logger.info("Model loaded and tested successfully!")
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to install spaCy model: {e}")
        logger.error(f"Error output: {e.stderr}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")

if __name__ == "__main__":
    install_spacy_model()
