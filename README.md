# 음악 분석 및 Suno 프롬프트 생성기

MP3 또는 WAV 음악 파일을 분석하여 Suno AI 음악 생성기를 위한 텍스트 프롬프트를 만들어주는 Windows용 데스크톱 애플리케이션입니다.

Google Gemini 1.5 Pro API를 사용하여 음악의 장르, 코드 진행, BPM, 감정 등을 분석합니다.

## 사전 준비 사항

1.  **Python 3**: Windows PC에 Python 3가 설치되어 있어야 합니다. ([python.org](https://www.python.org/)에서 다운로드)
2.  **Google AI API 키**: Google AI Studio에서 발급받은 API 키가 필요합니다. ([여기](https://aistudio.google.com/app/apikey)에서 무료로 받을 수 있습니다.)

## 설치 및 설정 방법

Windows PC의 명령 프롬프트(`cmd`)나 파워쉘(`PowerShell`)에서 아래 단계를 따라주세요.

### 1. API 키 설정하기

프로그램을 실행하기 전, 반드시 API 키를 환경 변수로 설정해야 합니다.

**cmd 에서:**
```sh
set GEMINI_API_KEY="YOUR_API_KEY"
```

**PowerShell 에서:**
```sh
$env:GEMINI_API_KEY="YOUR_API_KEY"
```
`"YOUR_API_KEY"` 부분을 실제 발급받은 키로 교체해주세요.

### 2. 필요 라이브러리 설치하기

`main.py`와 `requirements.txt` 파일이 있는 폴더로 이동한 뒤, 아래 명령어를 실행하여 필요한 라이브러리를 설치합니다.
```sh
pip install -r requirements.txt
```

## 사용 방법

두 가지 방법으로 프로그램을 실행할 수 있습니다.

### 방법 1: Python 스크립트로 직접 실행

소스 코드를 직접 실행하여 프로그램을 사용할 수 있습니다.
```sh
python main.py
```
이 명령을 실행하면 GUI 창이 나타납니다.

### 방법 2: 독립 실행 파일(.exe) 만들기

다른 PC에서도 쉽게 실행할 수 있는 `.exe` 파일을 만들려면, 터미널에서 아래 명령어를 실행하세요.
```sh
pyinstaller --onefile --windowed --name MusicAnalyzer main.py
```
명령이 완료되면 `dist`라는 폴더가 생성되고, 그 안에 `MusicAnalyzer.exe` 파일이 들어있습니다. 이 파일을 직접 실행하면 됩니다.

## 애플리케이션 공유에 관하여

생성하신 `MusicAnalyzer.exe` 파일은 자유롭게 공유하셔도 괜찮습니다. 다만, 아래 내용을 꼭 기억해주세요.

*   **사용자 각자의 `GEMINI_API_KEY`가 필요합니다.** 이 키가 없으면 프로그램이 동작하지 않습니다.
*   API 사용량에 따라 Google 정책에 따라 요금이 부과될 수 있습니다.

다른 사람에게 파일을 공유할 때는 이 두 가지 사항을 함께 알려주시는 것이 좋습니다.
