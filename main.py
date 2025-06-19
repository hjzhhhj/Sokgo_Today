import datetime
import os
import re
import requests
from dotenv import load_dotenv
from instagrapi import Client
from PIL import Image, ImageDraw, ImageFont

NEIS_API_KEY = os.getenv("NEIS_API_KEY")
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")

ATPT_OFCDC_SC_CODE = "K10"
SD_SCHUL_CODE = "7801152"
NEIS_API_BASE_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

FONT_PATH = os.path.join(ASSETS_DIR, "Pretendard-Bold.otf")
BACKGROUND_IMAGE_PATH = os.path.join(ASSETS_DIR, "sokgo.png")

SESSION_FILE_PATH = os.path.join(BASE_DIR, "session.json")

TITLE_FONT_SIZE = 40
DATE_FONT_SIZE = 30
MEAL_TYPE_FONT_SIZE = 36
BODY_FONT_SIZE = 32
TEXT_COLOR = "black"

TITLE_Y_POS = 150
DATE_Y_OFFSET_FROM_TITLE = 20
MEAL_TYPE_Y_OFFSET_FROM_DATE = 50
MEAL_CONTENT_Y_OFFSET_FROM_MEAL_TYPE = 40
MEAL_LINE_SPACING = 45

os.makedirs(OUTPUTS_DIR, exist_ok=True)


load_dotenv()
