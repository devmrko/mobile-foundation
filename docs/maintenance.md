# 서비스 중단 중에도 사용자에게 다음 행동 안내하기

앱이 내려간 동안 Nginx가 독립 정적 페이지를 제공합니다. `/api`와 상태 확인 경로는 JSON 503을 유지하고, 점검 모드는 배포 파일의 플래그로 전환합니다. 운영 서버를 자동 변경하지 않으므로 다음 설정을 배포 진입점에 연결하세요.

```sh
python -m mobile_foundation.maintenance export /absolute/deploy/maintenance --upstream http://127.0.0.1:8000 --service '내 서비스'
nginx -t -c /absolute/deploy/maintenance/nginx.conf
nginx -c /absolute/deploy/maintenance/nginx.conf -g 'daemon off;'
python -m mobile_foundation.maintenance mode /absolute/deploy/maintenance on
# 배포와 실제 readiness 확인 후
python -m mobile_foundation.maintenance mode /absolute/deploy/maintenance off
```

현재 저장소 기준 명령입니다. Python/Spring 생성 앱에서는 도구가 `deploy/maintenance/maintenance.pyz`에 포함됩니다. 기본 수신 주소는 127.0.0.1:8080이며 외부 접근/TLS는 배포 환경에 맞게 구성합니다. 앱을 종료하고 진입점의 HTML 및 API JSON 503을 확인한 뒤 재기동해 원래 응답으로 복구되는지 확인하세요.

[전체 옵션·기존 Nginx·클라이언트 연결](../src/mobile_foundation/maintenance_assets/README.md) · [설계와 검증 경계](design/maintenance.md)

설치된 FastAPI 정적 경로에서 `/static/mf/availability.js`의 `createAvailability`를 가져오세요. 기존 프레임·폼을 교체하지 않고 앱의 fetch 호출을 감쌉니다.
