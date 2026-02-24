import os
import datetime
from google.oauth2.credentials import Credentials   
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from googleapiclient.http import MediaInMemoryUpload


# 구글 드라이브 접근 권한 범위
SCOPES = ['https://www.googleapis.com/auth/drive.file']

def get_gdrive_service():
    creds = None
    # 이전에 인증한 토큰이 있다면 로드
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    
    # 인증 정보가 없거나 만료된 경우 재인증
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not os.path.exists('credentials.json'):
                print("에러: 'credentials.json' 파일이 없습니다.")
                print("구글 클라우드 콘솔(https://console.cloud.google.com/)에서")
                print("OAuth 2.0 클라이언트 ID를 생성하고 JSON을 다운로드하여")
                print("이 파일과 같은 폴더에 'credentials.json' 이름으로 저장해주세요.")
                return None
            
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    return build('drive', 'v3', credentials=creds)

def save_md_to_drive(title, content, folder_id=None):
    """
    마크다운 내용을 구글 드라이브에 파일로 저장합니다.
    """
    service = get_gdrive_service()
    if not service:
        return None
    
    # 파일 메타데이터 설정
    file_metadata = {
        'name': f"{title}.md",
        'mimeType': 'text/markdown'
    }
    if folder_id:
        file_metadata['parents'] = [folder_id]

    # 메모리 내 데이터를 업로드 스트림으로 변환
    media = MediaInMemoryUpload(content.encode('utf-8'), mimetype='text/markdown')

    # 파일 생성
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id'
    ).execute()
    
    print(f"파일이 저장되었습니다. File ID: {file.get('id')}")
    return file.get('id')

# --- 사용 예시 ---
if __name__ == "__main__":
    # 대화 제목과 내용 (제미나이 대화에서 복사한 내용이라고 가정)
    chat_title = f"Gemini_Conversation_{datetime.date.today()}"
    chat_content = """# 제미나이와의 대화 기록
    
## 질문: 파이썬 코드를 작성해주세요
## 답변: 네, 구글 드라이브 API를 활용한 코드를 작성해 드립니다...
    
---
*저장 일시: {}*
""".format(datetime.datetime.now())

    # 실행 (folder_id가 없다면 루트 디렉토리에 저장됩니다)
    save_md_to_drive(chat_title, chat_content)