from dotenv import load_dotenv
import os

load_dotenv()

config = {
    "URL_BASE_API": os.getenv("URL_BASE_API"),
    "SECRET_KEY": os.getenv("SECRET_KEY"),
    "TOKEN": os.getenv("TOKEN"),

    # Datos de correo
    "MAIL_SERVER": os.getenv("MAIL_SERVER"),
    "MAIL_PORT": int(os.getenv("MAIL_PORT", "587")),
    "MAIL_USE_TLS": os.getenv("MAIL_USE_TLS", "true").lower() == "true",
    "MAIL_USERNAME": os.getenv("MAIL_USERNAME"),
    "MAIL_PASSWORD": os.getenv("MAIL_PASSWORD"),
    "MAIL_FROM": os.getenv("MAIL_FROM", os.getenv("MAIL_USERNAME")),

}

URL_BASE_API = "https://apitorneo.inacode.cl/api"
  # ajusta el puerto si cambiaste
JWT_COOKIE_NAME = "token"                # si no usas token, da lo mismo
