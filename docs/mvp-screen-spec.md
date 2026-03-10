# AI Arena MVP 화면별 상세 기획서

## 1) 제품 목표

- 사용자가 실제 AI 모델과 1:1로 대결한다.
- 한 세션을 3~10분 내 종료해 반복 플레이를 유도한다.
- 경기 종료 즉시 결과 분석 + 공유를 제공한다.

---

## 2) 핵심 사용자 흐름

1. 홈 진입
2. AI 상대 선택
3. 모드/난이도 선택
4. 경기 진행 (라운드)
5. 결과 리포트 확인
6. 공유 또는 재도전

---

## 3) 화면 정의

## A. 홈 (Home)

### 목적

- 즉시 플레이 진입
- 오늘의 챌린지 노출
- 개인 전적/랭킹 진입점 제공

### 주요 UI

- Hero: `"지금 AI와 대결해보세요"`
- CTA: `"빠른 대결 시작"`
- 카드: 추천 AI 상대 (GPT, Claude, Gemini)
- 섹션: 최근 결과, 내 배지, 주간 랭킹 미리보기

### 핵심 이벤트

- `home_start_click`
- `home_ai_card_click`
- `home_challenge_click`

---

## B. 상대 선택 (Choose Opponent)

### 목적

- 대전 상대 AI 선택
- AI 성향을 명확히 인지시키기

### 주요 UI

- AI 카드
  - 모델명
  - 플레이 스타일
  - 난이도 티어 (Rookie / Casual / Pro)
  - 평균 승률(전 사용자 기준)
- 선택 후 `도전하기` 버튼 활성화

### 상태

- 기본 선택 없음
- 선택 시 카드 하이라이트

### 핵심 이벤트

- `opponent_select`
- `opponent_confirm`

---

## C. 모드 선택 (Mode Select)

### MVP 모드

- Duel Mode (기본)

### Duel 옵션

- 라운드 수: 3 / 5
- 난이도: Easy / Normal / Hard
- 게임 세트:
  - Quick Mix 5 (기본)
  - Logic Focus
  - Creativity Focus

### 핵심 이벤트

- `mode_select`
- `round_count_select`
- `difficulty_select`
- `set_select`
- `match_create_click`

---

## D. 경기 화면 (Match Play)

### 공통 레이아웃

- 상단: 라운드 진행 상태 (`Round 2/5`), 타이머
- 좌측: Human 패널 (내 점수, 최근 정답률)
- 우측: AI 패널 (AI 점수, 모델명)
- 중앙: 문제/미션 영역
- 하단: 입력창 + 제출 버튼

### 라운드 처리

1. 문제 표시
2. 사용자 입력
3. 시간 종료/제출
4. AI 결과 수신
5. 라운드 판정
6. 다음 라운드

### 오류/예외

- AI 응답 타임아웃 시 재시도 1회
- 재시도 실패 시 fallback 모델 또는 사전 캐시 답 사용

### 핵심 이벤트

- `round_started`
- `answer_submitted`
- `ai_answer_received`
- `round_scored`
- `match_finished`

---

## E. 결과 화면 (Result Report)

### 목적

- 승패 및 이유를 즉시 이해
- 재도전/공유 유도

### 필수 구성요소

1. 최종 승패 배너 (`You Win`, `You Lose`, `Draw`)
2. 최종 점수 (`Human 420 : AI 380`)
3. 카테고리별 비교
   - Logic / Intuition / Creativity / Strategy / Speed
4. 강점/약점 카드
5. 바이럴 문구
   - 예: `"당신은 GPT보다 창의력이 높습니다."`
6. CTA
   - 재도전
   - 다른 AI와 대결
   - 공유 이미지 생성

### 핵심 이벤트

- `result_viewed`
- `result_share_click`
- `result_rematch_click`

---

## F. 랭킹/프로필 (간소 MVP)

### 목적

- 리텐션 확보
- 장기 목표 제시

### 구성

- 최근 10경기 전적
- 총 승률
- 현재 등급 (AI Challenger 등)
- 상위 퍼센타일

---

## 4) MVP 게임 세트 (6종)

1. 숫자 패턴 추론 (Logic)
2. 논리 퍼즐 (Logic)
3. 사회적 상황 판단 (Intuition)
4. 광고 카피 생성 (Creativity)
5. 투자 선택 시뮬레이션 (Strategy)
6. 반응속도 클릭 (Speed/Action)

---

## 5) UX 원칙

- 첫 경기 시작까지 2클릭 이내
- 한 라운드 설명은 1문장 원칙
- 결과는 3초 내 핵심 정보 노출
- AI 이름/스타일을 캐릭터처럼 표현

---

## 6) MVP 성공 지표

- 첫 경기 완료율
- 1일 재방문율
- 공유 클릭률
- 경기당 평균 플레이 시간
- AI별 선택 분포
