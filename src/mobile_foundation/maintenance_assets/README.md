# 앱 중단·점검 중에도 다음 행동 안내하기

앱보다 바깥의 Nginx가 정적 503 안내를 제공합니다. 이 디렉터리는 Python 패키지·DB·외부 CDN 없이 동작합니다. Python 3.10+는 내보내기와 점검 플래그 관리에, Nginx는 실제 응답에 사용합니다.

## 시작하기

원본 도구를 `TOOL`로 표기합니다. 설치 패키지는 `python -m mobile_foundation.maintenance`, 독립 파일은 `python3 maintenance.pyz`입니다.

```sh
TOOL export /absolute/deploy/maintenance --upstream http://127.0.0.1:8000 --service '내 서비스'
nginx -t -c /absolute/deploy/maintenance/nginx.conf
nginx -c /absolute/deploy/maintenance/nginx.conf -g 'daemon off;'
```

기본 진입점은 127.0.0.1:8080입니다. 외부 진입은 `--listen 0.0.0.0:8080`과 별도 TLS/접근 정책을 설정하세요. 앱 포트를 진입점으로 그대로 사용하면 이 기능을 거치지 않습니다. 경로는 내보낸 위치에 고정됩니다. 컨테이너/원격 경로가 다르면 내보낼 때 `--runtime-root /opt/maintenance`를 지정하고 해당 위치로 파일을 복사합니다. 재내보내기로 기존 설정이나 점검 상태를 덮어쓰지 않습니다. Nginx 사용자는 public 파일 읽기·상위 경로 탐색 권한, 설정의 임시/로그 디렉터리 쓰기 권한이 필요합니다.

```sh
TOOL mode /absolute/deploy/maintenance on
# 배포·실제 앱 readiness 확인
TOOL mode /absolute/deploy/maintenance off
```

플래그 전환에는 reload가 필요 없습니다. `--retry-after 60`은 운영자가 재시도 간격을 정할 때만 지정합니다. 복구 시각 보장이 아닙니다. 건강 상태 요청을 성공으로 위장하지 않습니다. 이미 연결된 WebSocket은 플래그가 종료하지 않으므로 서버의 graceful shutdown/클라이언트 재접속 정책을 함께 사용하세요.

## 기존 Nginx에 연결하기

`http.conf`는 http 블록에서 **한 번만**, `server.conf`는 대상 server 블록에서 include합니다. 앱 프록시 location에서 `proxy.conf`를 include하면 guard·프록시·WebSocket 설정이 적용됩니다. 독자적인 proxy_pass를 유지한다면 `guard.conf`, `proxy_intercept_errors off`, `proxy_next_upstream off`를 해당 location에 연결합니다. 정적 게임의 / 및 자산 location에도 guard를 적용합니다. server 레벨 guard는 내부 오류 페이지까지 가로막으므로 사용하지 마세요.

API location에는 `error_page 502 503 504 =503 /__foundation_unavailable.json;`을 설정합니다. 생성된 `locations.conf`가 기본 예제입니다. API 접두사를 바꾸면 명시적으로 추가하세요. 백엔드가 직접 반환한 업무 503과 인증 오류는 보존합니다. 다단 프록시에서 안쪽 프록시가 만든 502/503은 바깥쪽에서 가로채지 않으므로, 이 구성을 연결 실패를 직접 관측하는 프록시에 적용하세요. 호스트/Nginx/DNS 자체 장애는 외부 LB/CDN 구성이 필요합니다.

## 이미 열린 화면의 입력 유지

`public/availability.js`를 앱의 정적 자산으로 제공하고 ES module로 가져옵니다. CSS는 기존 mf-notice/mf-btn을 사용하거나 앱에서 지정합니다. 앱의 기존 fetch 호출 경계에 한 번 연결하세요.

```js
import {createAvailability} from '/static/availability.js';
const availability = createAvailability({probeUrl: '/actuator/health'});
const response = await availability.request('/api/orders', options);
// 기존 응답·업무 오류 처리 유지. 종료 시 availability.dispose().
```

공개하고 읽기 전용인 실제 readiness 경로를 지정하세요. offline 이벤트나 502/503/504는 안내를 표시하며 성공 응답을 확인해야 사라집니다. 요청 중단(AbortError)은 장애로 취급하지 않습니다. 입력 DOM을 교체하거나 자동 재전송·새로고침하지 않습니다. 모든 fetch를 전역 패치하지 않으며 이미 별도 연결 상태 UI가 있는 게임에는 그 흐름을 유지하세요. 이 도우미는 입력의 영속 저장이나 서버 저장 성공을 보장하지 않습니다.

## 확인하기

`TOOL verify --nginx nginx`가 실제 임시 서버·Nginx로 중단/복구와 점검 전환을 검사합니다. 운영 서버에 접속하지 않습니다. 페이지의 시각·실기기 확인은 별도로 수행하세요.
