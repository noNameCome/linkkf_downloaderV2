# 🎬 LinkKF 비디오 다운로더

kr.linkkf.net 사이트에서 비디오를 다운로드하는 GUI 다운로더입니다.

## 🚀 사용법

### 1단계: 실행
**`LinkKF_다운로더.bat`** 파일을 더블클릭하세요.

### 2단계: 다운로드
1. GUI 창이 열리면 LinkKF URL을 입력
2. 저장 폴더 선택
3. "🚀 다운로드 시작" 버튼 클릭

## 📝 지원하는 URL 형식
```
https://kr.linkkf.net/player/v[번호]-sub-[번호]/
```

**예시:**
```
https://kr.linkkf.net/player/v401148-sub-1/
https://kr.linkkf.net/player/v401148-sub-2/
```

## 📋 필요한 프로그램
- Python 3.7 이상
- FFmpeg (비디오 병합용)

**설치**: 배치 파일이 자동으로 필요한 것들을 설치해줍니다.

## 🎯 기능
- ✅ 자동 URL 감지
- ✅ 배치 다운로드 (여러 URL 동시 처리)  
- ✅ 이미지 기반 스트림 지원
- ✅ 자막 파일 추출
- ✅ 실시간 진행률 표시

## 🛠️ 문제 해결
1. **Python 없음**: https://www.python.org/downloads/ 파이썬 설치
2. **FFmpeg 없음**: https://ffmpeg.org 에서 다운로드
3. **다운로드 실패**: URL 형식 확인
