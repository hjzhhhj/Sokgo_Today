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
IG_USERNAME = os.getenv("INSTA_USERNAME")
IG_PASSWORD = os.getenv("INSTA_PASSWORD")

ATPT_OFCDC_SC_CODE = "K10"  # 강원도 교육청 코드
SD_SCHUL_CODE = "7801152"   # 속초고등학교 학교 코드
NEIS_API_BASE_URL = "https://open.neis.go.kr/hub/mealServiceDietInfo"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")

FONT_PATH = os.path.join(ASSETS_DIR, "BMJUA_otf.otf")
BACKGROUND_IMAGE_PATH = os.path.join(ASSETS_DIR, "sokgo.png")
SESSION_FILE_PATH = os.path.join(BASE_DIR, "session.json")

DATE_FONT_SIZE = 40
MEAL_TYPE_FONT_SIZE = 35
BODY_FONT_SIZE = 50

TEXT_COLOR = "#123D6A"

DATE_Y_OFFSET_FROM_TITLE = 0
MEAL_TYPE_Y_OFFSET_FROM_DATE = 30
MEAL_CONTENT_Y_OFFSET_FROM_MEAL_TYPE = 60
MEAL_LINE_SPACING = 80

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
    
def generate_meal_image(meal_type_korean: str, meal_content: str, date_display: str) -> str:
    try:
        image = Image.open(BACKGROUND_IMAGE_PATH).convert("RGB")
    except FileNotFoundError:
        print(f"오류: 배경 이미지 파일 '{BACKGROUND_IMAGE_PATH}'을(를) 찾을 수 없습니다. 경로를 확인하세요.")
        return ""

    draw = ImageDraw.Draw(image)

    try:
        date_font = ImageFont.truetype(FONT_PATH, DATE_FONT_SIZE)
        meal_type_font = ImageFont.truetype(FONT_PATH, MEAL_TYPE_FONT_SIZE)
        body_font = ImageFont.truetype(FONT_PATH, BODY_FONT_SIZE)
    except IOError:
        print(f"오류: 폰트 파일 '{FONT_PATH}'을(를) 찾을 수 없습니다. 기본 폰트를 사용합니다.")
        date_font = ImageFont.load_default()
        meal_type_font = ImageFont.load_default()
        body_font = ImageFont.load_default()

    image_width, image_height = image.size

    # 날짜 텍스트
    date_start_y = 420
    date_bbox = draw.textbbox((0, 0), date_display, font=date_font)
    date_width = date_bbox[2] - date_bbox[0]
    date_x = (image_width - date_width) // 2
    date_y = date_start_y + DATE_Y_OFFSET_FROM_TITLE
    draw.text((date_x, date_y), date_display, font=date_font, fill=TEXT_COLOR)

    # 급식 종류 텍스트
    meal_type_bbox = draw.textbbox((0, 0), meal_type_korean, font=meal_type_font)
    meal_type_width = meal_type_bbox[2] - meal_type_bbox[0]
    meal_type_x = (image_width - meal_type_width) // 2
    meal_type_y = date_y + (date_bbox[3] - date_bbox[1]) + MEAL_TYPE_Y_OFFSET_FROM_DATE
    draw.text((meal_type_x, meal_type_y), meal_type_korean, font=meal_type_font, fill=TEXT_COLOR)

    # 급식 메뉴 내용 텍스트 (여러 줄)
    meal_lines = meal_content.strip().split("\n")
    content_top_y = meal_type_y + (meal_type_bbox[3] - meal_type_bbox[1]) + MEAL_CONTENT_Y_OFFSET_FROM_MEAL_TYPE

    for i, line in enumerate(meal_lines):
        line_bbox = draw.textbbox((0, 0), line, font=body_font)
        line_width = line_bbox[2] - line_bbox[0]
        line_x = (image_width - line_width) // 2
        y = content_top_y + i * MEAL_LINE_SPACING
        draw.text((line_x, y), line, font=body_font, fill=TEXT_COLOR)

    output_filename = f"sokcho_meal_{meal_type_korean.lower()}.jpg"
    output_path = os.path.join(OUTPUTS_DIR, output_filename)
    image.save(output_path)
    return output_path

def login_to_instagram() -> Client:
    cl = Client()

    if os.path.exists(SESSION_FILE_PATH):
        try:
            cl.load_settings(SESSION_FILE_PATH)
            cl.login(IG_USERNAME, IG_PASSWORD)
            print("기존 세션 로드 및 로그인 성공.")
        except Exception as e:
            print(f"세션 로드 실패: {e}. 재로그인 시도 중...")
            cl.set_locale("ko_KR")
            cl.set_timezone_offset(32400)
            try:
                cl.login(IG_USERNAME, IG_PASSWORD)
                cl.dump_settings(SESSION_FILE_PATH)
                print("재로그인 성공 및 세션 저장.")
            except Exception as login_err:
                print(f"[오류] 인스타그램 재로그인 실패: {login_err}")
                exit(1)
    else:
        print("세션 파일 없음. 첫 로그인 시도 중...")
        cl.set_locale("ko_KR")
        cl.set_timezone_offset(32400)
        try:
            cl.login(IG_USERNAME, IG_PASSWORD)
            cl.dump_settings(SESSION_FILE_PATH)
            print("첫 로그인 성공 및 세션 저장.")
        except Exception as first_login_err:
            print(f"[오류] 인스타그램 첫 로그인 실패: {first_login_err}")
            exit(1)

    return cl

def post_story(client: Client, image_path: str, caption: str):
    if not os.path.exists(image_path):
        print(f"[경고] {image_path} 파일이 없습니다. 업로드 건너뜀.")
        return

    try:
        print(f"[업로드 중] {caption} (파일: {image_path})")
        client.photo_upload_to_story(image_path, caption)
        print(f"[업로드 완료] {caption}")
    except Exception as e:
        print(f"[오류] 스토리 업로드 실패: {e}")

def main_routine():
    print("--- 속초고 급식 스토리 봇 실행 시작 ---")

    today_date_ymd = datetime.date.today().strftime("%Y%m%d")
    display_date_str = datetime.date.today().strftime("%Y년 %m월 %d일")
    print(f"오늘 날짜: {display_date_str}")

    print("급식 정보 가져오는 중...")
    meals_data = get_meal_data(today_date_ymd)

    print("인스타그램 로그인 중...")
    instagram_client = login_to_instagram()

    meal_types_korean = {
        "breakfast": "조식",
        "lunch": "중식",
        "dinner": "석식"
    }

    for meal_key, meal_content in meals_data.items():
        meal_type_korean = meal_types_korean.get(meal_key, meal_key)

        if not meal_content or meal_content.strip() == "없음":
            print(f"[건너뜀] {meal_type_korean} 급식 정보가 없습니다.")
            continue

        print(f"'{meal_type_korean}' 급식 이미지 생성 중...")
        image_output_path = generate_meal_image(
            meal_type_korean,
            meal_content,
            display_date_str
        )

        if not image_output_path:
            print(f"[오류] '{meal_type_korean}' 이미지 생성 실패. 업로드 건너뜀.")
            continue

        print(f"'{meal_type_korean}' 이미지 저장 완료: {image_output_path}")

        caption = f"속초고 {meal_type_korean} 🍽️"
        post_story(instagram_client, image_output_path, caption)

    print("--- 속초고 급식 스토리 봇 실행 완료 ---")


if __name__ == "__main__":
    main_routine()