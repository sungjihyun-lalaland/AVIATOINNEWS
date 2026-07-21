import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import feedparser
from google import genai

# 1. 구글 뉴스 RSS 수집
def fetch_aviation_news():
    rss_url = (
        "https://news.google.com/rss/search?"
        "q=aviation+OR+airline+OR+Boeing+OR+Airbus+when:1d&hl=en-US&gl=US&ceid=US:en"
    )
    feed = feedparser.parse(rss_url)
    
    articles = []
    for entry in feed.entries[:10]:
        articles.append(f"- 제목: {entry.title}\n  링크: {entry.link}\n")
    
    return "\n".join(articles)

# 2. Gemini API 뉴스 요약
def summarize_news(news_text):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY가 설정되지 않았습니다.")

    client = genai.Client(api_key=api_key)
    
    prompt = f"""
다음은 지난 24시간 동안 수집된 글로벌 항공 업계 뉴스 헤드라인과 링크 목록입니다.

[뉴스 목록]
{news_text}

위 뉴스들을 분석하여 한국어로 깔끔한 '일간 글로벌 항공 뉴스 브리핑' 리포트를 작성해 주세요.
HTML 형식(이메일 발송용)으로 작성해야 하며, 다음 규칙을 따라주세요:
1. 가독성 높은 깔끔한 HTML 태그 사용 (<h2>, <ul>, <li>, <a> 등 사용, <html>/<body> 제외).
2. 카테고리별 분류 (예: 항공사 동향, 제조사/기술, 규제/시장 트렌드 등).
3. 각 뉴스별로 2-3줄의 명확한 핵심 요약 제공.
4. 원문 링크를 클릭 가능한 <a> 태그 형태로 제공.
"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return response.text

# 3. 이메일 전송
def send_email(subject, html_content):
    sender_email = os.environ.get("SENDER_EMAIL")
    sender_password = os.environ.get("SENDER_PASSWORD")
    receiver_email = os.environ.get("RECEIVER_EMAIL")

    if not all([sender_email, sender_password, receiver_email]):
        raise ValueError("이메일 관련 환경 변수(SENDER_EMAIL, SENDER_PASSWORD, RECEIVER_EMAIL)를 확인해 주세요.")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = receiver_email

    html_part = MIMEText(html_content, "html", "utf-8")
    msg.attach(html_part)

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, msg.as_string())

if __name__ == "__main__":
    news_data = fetch_aviation_news()
    if news_data:
        summary_html = summarize_news(news_data)
        send_email("[매일 브리핑] 전날 글로벌 항공 업계 주요 뉴스", summary_html)
    else:
        print("수집된 뉴스가 없습니다.")
