import os
import requests
from translate import Translator
from dotenv import load_dotenv
import telegram
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.constants import ParseMode, ChatAction
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime

# .env 파일을 로드합니다.
load_dotenv()

# 텔레그램 봇 토큰을 환경 변수에서 가져옵니다.
bot_token = os.getenv("BOT_TOKEN")

# 번역기를 초기화합니다.
translator = Translator(to_lang="ko")

# 날짜와 시간 함수
get_current_datetime = lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S")

# 텍스트를 Telegram Markdown V2 형식으로 이스케이프하는 함수
escape_markdown_v2 = lambda text: "".join(
    ["\\" + char if char in r"\`*_{}[]()#+-.!|>=" else char for char in text]
)

# 응답을 나누어 마크다운 V2 형식으로 포맷팅하는 함수
split_response = lambda response: [
    escape_markdown_v2(part) if i % 2 == 0 else f"```{part}```"
    for i, part in enumerate(response.split("```"))
]

# 명언을 가져오고 번역하는 함수
def get_translated_quote():
    url = "https://api.forismatic.com/api/1.0/?method=getQuote&key=457653&format=json&lang=en"
    response = requests.get(url)
    data = response.json()
    quote_text = data.get('quoteText', '')
    quote_author = data.get('quoteAuthor', 'Unknown')

    translated_quote_text = translator.translate(quote_text)
    translated_quote_author = translator.translate(quote_author)

    return translated_quote_text, translated_quote_author

# 봇의 /start 명령에 대한 핸들러 함수
chat_ids = set()

async def start(update, context):
    chat_id = update.effective_chat.id
    chat_ids.add(chat_id)
    await context.bot.send_message(
        chat_id=chat_id, text="안녕하세요, Daily 챗봇입니다! 🧑‍💻"
    )

# 텔레그램 메시지에 대한 응답을 생성하는 핸들러 함수
async def send_daily_quote(context):
    try:
        translated_quote_text, translated_quote_author = get_translated_quote()
        response = f"{translated_quote_text}\n\n*저자: {translated_quote_author}*"
        formatted_response_parts = split_response(response)

        for chat_id in chat_ids:
            for part in formatted_response_parts:
                if part.strip():  # part가 비어있지 않은 경우에만 메시지 전송
                    await context.bot.send_message(
                        chat_id=chat_id,
                        text=part,
                        parse_mode=ParseMode.MARKDOWN_V2,
                    )
    except Exception as e:
        await context.bot.send_message(
            chat_id=chat_id, text=f"오류가 발생했습니다: {str(e)}"
        )

# 사용자 메시지 핸들러 함수
async def chat_bot(update, context):
    message = update.message.text
    user = update.message.from_user
    user_identifier = (
        user.username
        if user.username
        else f"{user.first_name} {user.last_name if user.last_name else ''}"
    )
    date_time = get_current_datetime()

    print(f"\n[User_Info] uid: {user.id}, name: {user_identifier}, date: {date_time}")
    print(f"\n[Question] {message}\n[Answer]\n")

    loading_message = await context.bot.send_message(
        chat_id=update.effective_chat.id, text="처리 중입니다... 🧑‍💻"
    )
    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id, action=ChatAction.TYPING
    )

    try:
        response = "여기에 당신의 응답 생성 로직을 추가하세요."  # 예시로 응답을 고정
    except Exception as e:
        await context.bot.delete_message(
            chat_id=update.effective_chat.id, message_id=loading_message.message_id
        )
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text=f"오류가 발생했습니다: {str(e)}"
        )
        return

    await context.bot.delete_message(
        chat_id=update.effective_chat.id, message_id=loading_message.message_id
    )
    formatted_response_parts = split_response(response)

    for part in formatted_response_parts:
        if part.strip():  # part가 비어있지 않은 경우에만 메시지 전송
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=part,
                parse_mode=ParseMode.MARKDOWN_V2,
            )

# 텔레그램 봇 애플리케이션 생성 및 핸들러 추가
application = Application.builder().token(bot_token).build()
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_bot))

# 스케줄러 설정
scheduler = AsyncIOScheduler()
scheduler.add_job(send_daily_quote, 'cron', hour=8, args=[application])
scheduler.start()

# 봇 실행
application.run_polling()