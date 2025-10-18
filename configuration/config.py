import os
from dotenv import load_dotenv

load_dotenv()


TOKEN = os.getenv("BOT_TOKEN", "")
API_BASE_URL = os.getenv("API_BASE_URL", "")
