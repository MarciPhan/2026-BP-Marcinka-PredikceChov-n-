import os




SECRET_KEY = os.getenv("DASHBOARD_SECRET_KEY")
ACCESS_TOKEN = os.getenv("DASHBOARD_ACCESS_TOKEN")
SESSION_EXPIRY_HOURS = 24


SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = "support@metricord.app"
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")  
SMTP_FROM = "Metricord Dashboard <support@metricord.app>"


ALLOWED_EMAIL_DOMAIN = "@metricord.app"
OTP_LENGTH = 6
OTP_EXPIRY_SECONDS = 300
OTP_MAX_ATTEMPTS = 5
OTP_RATE_LIMIT = 3


# Port settings
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", 8093))

# Discord OAuth
DISCORD_CLIENT_ID = os.getenv("DISCORD_CLIENT_ID", "1227269599951589508")
DISCORD_CLIENT_SECRET = os.getenv("DISCORD_CLIENT_SECRET")

# Use configured redirect URI or construct from port
DISCORD_REDIRECT_URI = os.getenv("DISCORD_REDIRECT_URI")
if not DISCORD_REDIRECT_URI:
    DISCORD_REDIRECT_URI = f"http://localhost:{DASHBOARD_PORT}/auth/callback"


ADMIN_USER_IDS = [471218810964410368]  
BOT_TOKEN = os.getenv("BOT_TOKEN")
