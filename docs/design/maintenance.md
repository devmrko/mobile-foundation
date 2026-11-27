# 배포 중에도 접근 가능한 사용 불가 안내

앱 프로세스가 중단되어도 방문자가 상태와 다음 행동을 알 수 있게 한다. API 소비자는 HTML 대신 안전한 JSON 503을 받는다. 2026-11-27 사용자 요청에 따른 공개 기능 설계다.

## 공통 계약

- 정적 페이지·표준 Python 내보내기 도구·Nginx 조각의 원본은 mobile-foundation이다. 다른 Foundation은 SHA-256으로 고정한 독립 실행 zipapp을 소비한다. DB·앱·CDN·외부 글꼴·Python 패키지 설치가 필요 없다.
- 브라우저 GET/HEAD의 text/html 요청만 HTML을 받는다. /api, /mcp, /actuator, /health, /readyz, /livez, /race-rooms 경로는 JSON을 유지한다. API 접두사는 새 엔드포인트 추가 시 배포 설정에서 검토한다.
- 프록시 연결 거절·시간 초과와 명시적 점검 모드는 503, Cache-Control: no-store이다. Retry-After는 운영자가 초 단위로 설정할 때만 제공한다. 앱이 직접 반환한 업무 오류·인증·JSON 응답은 가로채지 않는다.
- 점검 플래그는 배포 파일시스템에서만 켜고 끈다. 웹 관리 API는 만들지 않는다. 쓰기·WebSocket 연결을 프록시가 자동 재시도하지 않는다. 페이지의 다시 시도는 사용자가 선택하는 안전한 GET 탐색이다.
- 이미 열린 앱은 기존 DOM·입력·게임 상태를 유지한다. 공통 브라우저 도우미는 fetch의 연결 실패/502/503/504를 표시하고 성공 응답을 확인해야 안내를 해제한다. 요청 재전송·새로고침·저장 성공 가정은 하지 않는다. 게임의 기존 재접속 흐름은 유지한다.
- 프록시 자체 또는 호스트/DNS 장애는 같은 호스트의 페이지로 해결되지 않는다. 외부 CDN/LB는 별도 운영 구성이다. 이 변경에서 실제 운영 서버를 변경하지 않는다.

## 제공 및 검증

설치 패키지와 생성 프로젝트에 동일 도구와 안내를 전달한다. Nginx를 실제 실행해 정상→앱 중단→복구, 점검 on/off, API/브라우저 구분, POST 비재전송, 업무 503 보존, 캐시·재시도 헤더를 검사한다. 이 검사를 각 품질 명령과 CI에 연결한다. 브라우저 화면 확인과 엔진/기기 검사는 별도로 보고한다.

참고: [Nginx proxy_intercept_errors](https://nginx.org/en/docs/http/ngx_http_proxy_module.html#proxy_intercept_errors), [HTTP 503](https://www.rfc-editor.org/rfc/rfc9110.html#name-503-service-unavailable).

검사의 임시 HTTP 백엔드는 loopback만 바인딩하고 호스트 이름/DNS에 의존하지 않는다. 준비 대기는 최대 30초이며 자식 프로세스가 먼저 종료하면 종료 코드를 보고해 즉시 실패한다.
