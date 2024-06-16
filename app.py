import streamlit as st
from openai import OpenAI
import pandas as pd
import os.path
import json
import base64
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
# OpenAI API 키 설정
os.environ["OPENAI_API_KEY"] = st.secrets['API_KEY']
client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)
# Gmail API 설정
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
creds = None
credentials_info = json.loads(st.secrets["gcp_service_account"])

# Gmail API 인증
if os.path.exists('token.json'):
    creds = Credentials.from_authorized_user_file('token.json', SCOPES)
if not creds or not creds.valid:
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_secrets_file(
            credentials_info, SCOPES)
        creds = flow.run_local_server(port=0)
    with open('token.json', 'w') as token:
        token.write(creds.to_json())

service = build('gmail', 'v1', credentials=creds)
# Streamlit 페이지 구성
st.title('Gmail 내용을 요약하는 애플리케이션')
# query = "is:starred"


results = service.users().messages().list(userId='me', labelIds=['INBOX'],q="is:starred", maxResults=1).execute()
messages = results.get('messages', [])

if not messages:
    st.write("검색된 이메일이 없습니다.")
else:
    emails = []
    for msg in messages:
        msg = service.users().messages().get(userId='me', id=msg['id']).execute()
        msg_data = msg['payload']['parts'][0]['body']['data']
        headers = msg['payload']['headers']
        sender = next((header['value'] for header in headers if header['name'] == 'From'), None)
        subject = next((header['value'] for header in headers if header['name'] == 'Subject'), None)
        date = next((header['value'] for header in headers if header['name'] == 'Date'), None)
        # msg_sender = msg['payload']['headers'][0]dd
        msg_data = base64.urlsafe_b64decode(msg_data.encode('UTF-8')).decode('UTF-8')
        emails.append(msg_data)

    # 이메일 내용을 하나의 텍스트로 결합
    email_text = " ".join(emails)

    # OpenAI API를 사용하여 텍스트 요약
    response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": f"다음 텍스트의 주요 내용을 한줄로 요약해 주세요: {email_text}"}
    ],
    max_tokens=50
)
summary = response.choices[0].message.content
# 결과 출력

from streamlit_calendar import calendar

import pandas as pd
print(sender) 
print(subject)
print(date)
# selected_senders = st.multiselect('발송자 이메일을 선택하세요 (필터링 옵션):', sender)

st.write(" ")
sample_email=[
    {"이메일":sender,
     "제목" :subject,
     "날짜" :date,
     "내용":summary
    }
]

# 샘플 이메일 데이터를 데이터프레임으로 변환
email_df = pd.DataFrame(sample_email, columns=["이메일","제목","날짜", "내용"])

# if selected_senders:
    # email_df = email_df[email_df['이메일'].isin(selected_senders)]

# '발송시간' 열을 datetime 형식으로 변환 후 날짜만 표시
# email_df['발송시간'] = pd.to_datetime(email_df['발송시간']).dt.date

# '내용'을 GPT 모델을 사용하여 요약
# def summarize_text(text):
#     with st.spinner('AI가  작성중'):
#         response = client.chat.completions.create(
#             messages=[
#                 {
#                     "role": "user",
#                     "content": f"email_df 에 있는 {email_df['내용']} 을 100자 내 한 문장으로 요약해줘.",
#                 }
#             ],
#             model="gpt-4o",)
#         summary = response.choices[0].message.content
#         return summary

# email_df['요약'] = email_df['내용'].apply(summarize_text)

# 결과 출력
# st.write("이메일 원본:")
st.write(email_df)
st.title('Calendar Input Example')

# Streamlit calendar component for input
date_input = st.text_input('Enter date (1-31)', '')
month_input = st.text_input('Enter month (1-12)', '')
year_input = st.text_input('Enter year', '')
hour_input = st.text_input('Enter hour', '')
minute_input = st.text_input('Enter minute', '')
day=''
month=''
year=''
hour=''
minute=''

# Display selected date
if st.button('Submit'):
    try:
        # Convert inputs to integers
        day = int(date_input)
        month = int(month_input)
        year = int(year_input)
        hour = int(hour_input)
        minute = int(minute_input)
        #   Validate inputs
        if day < 1 or day > 31:
            st.error('Invalid day. Enter a day between 1 and 31.')
        elif month < 1 or month > 12:
            st.error('Invalid month. Enter a month between 1 and 12.')
        else:
            # Display the selected date
            selected_date = f'{year}-{month:02}-{day:02}'
            st.success(f'Selected Date: {selected_date}')
    except ValueError:
        st.error('Please enter valid numeric inputs for day, month, and year.')

# st.subheader("요약 결과:")
# st.write(email_df)
start=str(year_input)+"-"+str(month_input)+"-"+str(date_input)+"T"+str(hour_input)+":"+str(minute_input)+":"+"00"
end=str(year_input)+"-"+str(month_input)+"-"+str(date_input)+"T"+str(hour_input)+":"+str(minute_input)+":"+"30"
print(start)

calendar_options = {
    "editable": "true",
    "selectable": "true",

}
calendar_events = [
    {
        "title": "Event 1",
        "start": start,
        "end": end
    },
]
custom_css="""
    .fc-event-past {
        opacity: 0.8;
    }
    .fc-event-time {
        font-style: italic;
    }
    .fc-event-title {
        font-weight: 700;
    }
    .fc-toolbar-title {
        font-size: 2rem;
    }
"""


calendar = calendar(events=calendar_events, options=calendar_options, custom_css=custom_css)

