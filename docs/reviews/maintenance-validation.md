# 점검 안내 검증 결과

2026-11-27, 0.3.0 작업본에서 bash scripts/check-quality.sh가 통과했다. 기존 작업공간을 보존한 release-worktrees/foundation-20261127의 독립 체크아웃에서 실행했다.

- Ruff lint/format, strict mypy, pytest 24개, Node의 fetch 실패·입력 유지·POST 비재전송·연결 확인·취소 검사가 통과했다.
- 설치 wheel에서 도구를 만들어 패키지/원본 소스 없이 독립 zipapp을 실행했다. 실제 Nginx와 별도 백엔드 프로세스로 정상→시간 초과→프로세스 종료→복구, 점검 on/off, HTML/API/HEAD/POST/인코딩된 API 경로, 업무 503 보존, no-store와 선택적 Retry-After를 확인했다.
- Chrome에서 내보낸 한국어 페이지의 기본 창과 반응형 360×740 표시를 관찰했다. 다크 모드에서 글자·버튼·안내가 표시됐다. JS 도우미의 실제 브라우저 상호작용, 라이트 모드 수동 관찰과 실기기 iOS/Android는 미실행이다.
- 초기 로컬 Nginx 검사는 macOS 샌드박스의 sysctl 제한으로 실행되지 않았고, 승인된 환경에서 전체 명령을 다시 실행해 통과했다.
- Git diff 공백 검사, actionlint와 Gitleaks 작업 폴더 검사를 통과했다. 운영 서버·CDN·DNS·실제 서비스 배포는 변경하지 않았다. 원격 CI/릴리스 결과는 GitHub 실행/태그가 원본 증거다.

## 0.3.1 검사 도구 보강

게임의 GitHub macOS 실행에서 임시 HTTP 서버가 8초 안에 준비되지 않았다. 지연 원인은 로그만으로 단정하지 않으며, 표준 HTTPServer의 이름 조회를 제거한 loopback 전용 fixture와 최대 30초 준비 대기·자식 프로세스 종료 즉시 보고를 추가했다. DNS 함수를 실패시키고도 fixture가 시작되는 회귀 검사와 조기 종료 보고 검사를 포함한 pytest 26개 및 실제 Nginx 검사를 통과했다. 기존 배포 버전/태그는 보존하고 0.3.1/bundle 1.0.1 패치로 제공한다.
