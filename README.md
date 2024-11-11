# 실시간 암호화폐 가격 위젯

이 프로젝트는 실시간으로 암호화폐 가격을 모니터링할 수 있는 PyQt5 기반의 데스크톱 위젯입니다. Binance API를 사용하여 최신 가격 정보를 가져오며, 사용자 친화적인 인터페이스를 제공합니다.

## 주요 기능

- **실시간 가격 업데이트**: 선택한 암호화폐의 가격을 주기적으로 업데이트합니다.
- **커스터마이징 가능한 코인 목록**: 사용자가 원하는 코인을 추가하거나 제거할 수 있습니다.
- **다국어 지원**: 한국어와 영어 인터페이스를 지원합니다.
- **투명도 조절**: 위젯의 투명도를 사용자가 조절할 수 있습니다.
- **항상 위에 표시**: 다른 창 위에 항상 표시되도록 설정할 수 있습니다.
- **창 크기 조절**: 사용자가 위젯의 크기를 조절할 수 있습니다.
- **거래소 페이지 연결**: 코인을 더블클릭하면 해당 코인의 거래소 페이지가 열립니다.
- **설정 저장**: 사용자의 설정을 저장하고 다음 실행 시 불러옵니다.

## 사용 방법

1. 프로그램을 실행합니다.
2. 설정 버튼(⚙)을 클릭하여 설정 창을 엽니다.
3. 원하는 코인을 검색하고 추가합니다.
4. 투명도, 항상 위에 표시 여부, 창 크기 등을 조절합니다.
5. 언어를 선택합니다 (한국어/영어).
6. 메인 화면에서 실시간으로 업데이트되는 코인 가격을 확인합니다.
7. 코인을 더블클릭하여 해당 코인의 거래소 페이지로 이동할 수 있습니다.

## 기술 스택

- Python 3.x
- PyQt5
- Requests 라이브러리
- Win32gui (Windows API)

## 설치 방법

1. 저장소를 클론합니다:
2. 필요한 라이브러리를 설치합니다:
3. 프로그램을 실행합니다:

## 주의사항

- 이 프로그램은 Windows 환경에서 개발되었으며, 일부 기능(예: 항상 위에 표시)은 다른 운영 체제에서 작동하지 않을 수 있습니다.
- Binance API의 사용 제한에 주의하세요. 과도한 요청은 API 제한에 걸릴 수 있습니다.

## 기여 방법

프로젝트에 기여하고 싶으시다면, 다음 절차를 따라주세요:

1. 이 저장소를 포크합니다.
2. 새로운 기능 브랜치를 생성합니다 (`git checkout -b feature/AmazingFeature`).
3. 변경사항을 커밋합니다 (`git commit -m 'Add some AmazingFeature'`).
4. 브랜치에 푸시합니다 (`git push origin feature/AmazingFeature`).
5. Pull Request를 생성합니다.
