# AI Arena MVP: DB ERD + API 스펙

## 1) 데이터 모델 (ERD)

## users

- `id` (PK)
- `nickname`
- `email` (nullable)
- `avatar_url` (nullable)
- `country` (nullable)
- `created_at`

## ai_models

- `id` (PK)
- `code` (unique, 예: `gpt-4o`)
- `display_name`
- `provider` (openai/anthropic/google/local)
- `difficulty_tier` (rookie/casual/pro)
- `is_active`

## game_modes

- `id` (PK)
- `code` (unique, 예: `duel`)
- `name`
- `description`

## game_types

- `id` (PK)
- `code` (unique)
- `category` (logic/intuition/creativity/strategy/speed)
- `scoring_rule` (json)
- `is_action` (bool)
- `is_active` (bool)

## matches

- `id` (PK)
- `user_id` (FK -> users)
- `ai_model_id` (FK -> ai_models)
- `mode_id` (FK -> game_modes)
- `status` (created/in_progress/finished/canceled)
- `started_at` (nullable)
- `ended_at` (nullable)
- `winner` (human/ai/draw, nullable)
- `human_total_score` (default 0)
- `ai_total_score` (default 0)

## rounds

- `id` (PK)
- `match_id` (FK -> matches)
- `round_no`
- `game_type_id` (FK -> game_types)
- `prompt_data` (json)
- `expected_answer` (json, nullable)
- `difficulty`
- `started_at`
- `ended_at` (nullable)

## human_round_results

- `id` (PK)
- `round_id` (FK -> rounds)
- `user_input` (json/text)
- `raw_score`
- `normalized_score`
- `latency_ms`
- `metadata_json` (json)

## ai_round_results

- `id` (PK)
- `round_id` (FK -> rounds)
- `ai_model_id` (FK -> ai_models)
- `ai_output` (json/text)
- `raw_score`
- `normalized_score`
- `latency_ms`
- `token_usage` (json)
- `metadata_json` (json)

## match_reports

- `id` (PK)
- `match_id` (FK -> matches, unique)
- `summary_text`
- `viral_title`
- `radar_json`
- `strengths_json`
- `weaknesses_json`
- `share_image_url` (nullable)

---

## 2) 관계 요약

- `users 1:N matches`
- `ai_models 1:N matches`
- `matches 1:N rounds`
- `rounds 1:1 human_round_results`
- `rounds 1:1 ai_round_results`
- `matches 1:1 match_reports`

---

## 3) API 스펙 (MVP)

Base URL: `/api/v1`

## Auth

### `POST /auth/guest`

게스트 유저 생성

응답 예시

```json
{
  "user_id": "u_123",
  "token": "jwt..."
}
```

---

## AI/메타 조회

### `GET /ai-models`

활성 AI 목록 조회

### `GET /game-types`

활성 게임 유형 조회

---

## Match

### `POST /matches`

대전 생성

요청 예시

```json
{
  "ai_model_code": "gpt-4o",
  "mode": "duel",
  "round_count": 5,
  "difficulty": "normal",
  "set_code": "quick_mix_5"
}
```

응답 예시

```json
{
  "match_id": "m_1001",
  "status": "created"
}
```

### `POST /matches/{match_id}/start`

대전 시작

### `GET /matches/{match_id}`

매치 상세/스코어/상태 조회

### `GET /matches/{match_id}/rounds/{round_no}`

현재 라운드 문제 조회

### `POST /matches/{match_id}/rounds/{round_no}/submit`

사용자 답 제출 + 라운드 판정 트리거

요청 예시

```json
{
  "answer": {
    "final_answer": "B"
  },
  "latency_ms": 8210
}
```

응답 예시

```json
{
  "round_result": {
    "human_score": 80,
    "ai_score": 70,
    "winner": "human"
  }
}
```

### `POST /matches/{match_id}/finish`

매치 강제 종료/최종 집계

---

## Result / Report

### `GET /matches/{match_id}/report`

최종 분석 리포트 조회

응답 예시

```json
{
  "winner": "human",
  "total": {
    "human": 420,
    "ai": 380
  },
  "category_breakdown": {
    "logic": {"human": 82, "ai": 85},
    "creativity": {"human": 91, "ai": 73}
  },
  "viral_title": "당신은 GPT보다 창의력이 높습니다."
}
```

### `POST /matches/{match_id}/share-image`

결과 공유 이미지 생성

---

## Leaderboard

### `GET /leaderboard?period=weekly&mode=duel`

주간/시즌 랭킹 조회

---

## 4) AI 응답 표준 포맷

AI 어댑터의 출력은 아래 JSON으로 통일:

```json
{
  "final_answer": "B",
  "confidence": 0.82,
  "reasoning_brief": "pattern alternates",
  "action": null
}
```

액션 계열 게임은 `action` 객체를 사용:

```json
{
  "final_answer": null,
  "confidence": 0.77,
  "reasoning_brief": "",
  "action": {
    "move": "left",
    "target_id": "t3",
    "timestamp": 1710000000
  }
}
```

---

## 5) 운영 원칙

- 사용자와 AI는 동일한 문제/제한시간 적용
- 심사형 게임은 다중 평가(룰 기반 + LLM Judge + 투표) 권장
- 응답/점수 로그는 리플레이 가능하도록 저장
- 비용 절감을 위해 문제+모델 단위 AI 결과 캐시 적용
