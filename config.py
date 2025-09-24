from dotenv import load_dotenv
import os

load_dotenv()

config = {
    "URL_BASE_API": os.getenv("URL_BASE_API"),
    "SECRET_KEY": os.getenv("SECRET_KEY"),
    "TOKEN": os.getenv("TOKEN")
}
    