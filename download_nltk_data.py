import nltk

def download_nltk_data():
    """Download required NLTK data."""
    print("Downloading NLTK data...")
    nltk.download('stopwords')
    nltk.download('wordnet')
    nltk.download('punkt')
    print("NLTK data downloaded successfully!")

if __name__ == "__main__":
    download_nltk_data() 