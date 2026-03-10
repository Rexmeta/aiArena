# AI Arena MVP (Web App)

AI Arena는 **Human vs AI e-Sports** 컨셉의 멀티 게임 경쟁 플랫폼 MVP입니다.

## 포함 기능

- Duel Mode (사람 vs 단일 AI)
- 기본 게임 6종 (논리, 직관, 창의, 전략, 액션 포함)
- 라운드별 채점 + 경기 종료 리포트
- 리더보드 조회 API
- 데모 웹 화면 (`/`)
- Cloud Run 배포 가능한 컨테이너 구조

## 로컬 실행

```bash
python server.py
```

브라우저에서 `http://localhost:8000` 접속.

## 테스트

```bash
python -m unittest discover -s tests -q
```

## Google Cloud Run 배포

### 1) 빠른 배포 (스크립트)

```bash
PROJECT_ID=<your-gcp-project-id> \
REGION=asia-northeast3 \
SERVICE_NAME=ai-arena-web \
REPOSITORY=ai-arena \
scripts/deploy_cloud_run.sh
```

배포 완료 후 서비스 URL이 출력됩니다.

### 2) Cloud Build 파이프라인 사용

```bash
gcloud builds submit \
  --config cloudbuild.yaml \
  --substitutions _REGION=asia-northeast3,_REPOSITORY=ai-arena,_SERVICE_NAME=ai-arena-web
```

## 환경 변수

- `PORT` (default: `8000`, Cloud Run에서는 `8080` 자동 주입)
- `HOST` (default: `0.0.0.0`)

## 주요 파일

- `server.py`: API + 정적 웹앱 제공 서버
- `app/static/index.html`: 듀얼 모드 데모 UI
- `tests/test_server.py`: API 통합 흐름 테스트
- `Dockerfile`: Cloud Run용 컨테이너 빌드 파일
- `cloudbuild.yaml`: Cloud Build로 이미지 빌드/푸시/배포
- `scripts/deploy_cloud_run.sh`: 원클릭 배포 스크립트

## 문서

- [MVP 화면별 상세 기획서](docs/mvp-screen-spec.md)
- [DB ERD + API 스펙](docs/erd-api-spec.md)
