import datetime
import os
import re
import requests
from dotenv import load_dotenv
from instagrapi import Client
from PIL import Image, ImageDraw, ImageFont

load_dotenv()

# --- 설정 ---
NEIS_API_KEY = os.getenv("NEIS_API_KEY")
IG_USERNAME = os.getenv("IG_USERNAME")
IG_PASSWORD = os.getenv("IG_PASSWORD")

ATPT_OFCDC_SC_CODE = "K10"  # 강원도 교육청 코드
SD_SCHUL_CODE = "7380292"   # 속초고등학교 학교 코드
NEIS_API_BASE_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

FONT_PATH = os.path.join(ASSETS_DIR, "Pretendard-Bold.otf")
BACKGROUND_IMAGE_PATH = os.path.join(ASSETS_DIR, "sokgo_background.png")
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

# --- 함수 정의 ---

def clean_meal_text(meal_text: str) -> str:
    """급식 텍스트에서 괄호 내용, 불필요한 공백 제거 및 HTML 줄바꿈 변환."""
    cleaned_text = re.sub(r"\([^)]*\)", "", meal_text)
    cleaned_text = cleaned_text.replace("<br/>", "\n")
    return cleaned_text.strip()

def get_meal_data(date: str) -> dict:
    """NEIS API에서 특정 날짜의 급식 정보를 가져옵니다."""
    params = {
        "KEY": NEIS_API_KEY,
        "Type": "json",
        "ATPT_OFCDC_SC_CODE": ATPT_OFCDC_SC_CODE,
        "SD_SCHUL_CODE": SD_SCHUL_CODE,
        "MLSV_YMD": date
    }

    try:
        res = requests.get(NEIS_API_BASE_URL, params=params)
        res.raise_for_status()
        data = res.json()

        if 'mealServiceDietInfo' not in data:
            print(f"[{date}] 급식 정보가 없습니다.")
            return {"breakfast": "없음", "lunch": "없음", "dinner": "없음"}

        meals_map = {"1": "breakfast", "2": "lunch", "3": "dinner"}
        result = {"breakfast": "", "lunch": "", "dinner": ""}

        for row in data['mealServiceDietInfo'][1]['row']:
            meal_type_code = row['MMEAL_SC_CODE']
            meal_name = meals_map.get(meal_type_code, "")
            
            if meal_name:
                cleaned_menu = clean_meal_text(row['DDISH_NM'])
                result[meal_name] = cleaned_menu

        return result

    except requests.exceptions.RequestException as e:
        print(f"[오류] NEIS API 요청 실패: {e}")
        return {"breakfast": "오류 발생", "lunch": "오류 발생", "dinner": "오류 발생"}
    except ValueError as e:
        print(f"[오류] NEIS API 응답 파싱 실패: {e}")
        return {"breakfast": "오류 발생", "lunch": "오류 발생", "dinner": "오류 발생"}
    except KeyError as e:
        print(f"[오류] NEIS API 응답 구조 오류 (필수 키 없음: {e})")
        return {"breakfast": "오류 발생", "lunch": "오류 발생", "dinner": "오류 발생"}