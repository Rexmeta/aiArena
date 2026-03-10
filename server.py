from __future__ import annotations

import json
import os
import random
import uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

ROOT = Path(__file__).parent
INDEX_FILE = ROOT / "app" / "static" / "index.html"

USERS: dict[str, dict] = {}
MATCHES: dict[str, dict] = {}

AI_MODELS = [
    {"id": "ai_1", "code": "gpt-4o", "display_name": "GPT", "provider": "openai", "difficulty_tier": "pro", "is_active": True},
    {"id": "ai_2", "code": "claude-3-5", "display_name": "Claude", "provider": "anthropic", "difficulty_tier": "casual", "is_active": True},
    {"id": "ai_3", "code": "gemini-1.5", "display_name": "Gemini", "provider": "google", "difficulty_tier": "casual", "is_active": True},
]

GAME_TYPES = [
    {"id": "gt_1", "code": "number_pattern", "category": "logic", "is_action": False, "is_active": True},
    {"id": "gt_2", "code": "logic_puzzle", "category": "logic", "is_action": False, "is_active": True},
    {"id": "gt_3", "code": "social_judgment", "category": "intuition", "is_action": False, "is_active": True},
    {"id": "gt_4", "code": "ad_copy", "category": "creativity", "is_action": False, "is_active": True},
    {"id": "gt_5", "code": "investment_pick", "category": "strategy", "is_action": False, "is_active": True},
    {"id": "gt_6", "code": "reaction_tap", "category": "speed", "is_action": True, "is_active": True},
]

QUESTION_BANK = {
    "number_pattern": [("숫자 패턴: 2, 6, 7, 21, 22, ?", "66")],
    "logic_puzzle": [("A는 B를 보고, B는 C를 보고, C는 아무도 못 본다. 누가 정보가 가장 적은가?", "C")],
    "social_judgment": [("1~10 중 사람들이 가장 많이 고를 숫자를 고르세요.", "7")],
    "ad_copy": [("연필 기반 제품을 위한 10자 이내 광고 카피를 작성하세요.", "smart")],
    "investment_pick": [("수익률/리스크 균형이 가장 좋은 선택지는? (A/B/C)", "B")],
    "reaction_tap": [("빠르게 'tap' 을 입력하세요.", "tap")],
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def json_response(handler: BaseHTTPRequestHandler, status: int, payload: dict | list):
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def html_response(handler: BaseHTTPRequestHandler, status: int, payload: bytes):
    handler.send_response(status)
    handler.send_header("Content-Type", "text/html; charset=utf-8")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Content-Length", str(len(payload)))
    handler.end_headers()
    handler.wfile.write(payload)


def parse_json(handler: BaseHTTPRequestHandler) -> dict:
    length = int(handler.headers.get("Content-Length", "0"))
    if length <= 0:
        return {}
    raw = handler.rfile.read(length)
    if not raw:
        return {}
    try:
        return json.loads(raw.decode("utf-8"))
    except json.JSONDecodeError:
        return {}


def choose_game_types(set_code: str, round_count: int) -> list[str]:
    if set_code == "logic_focus":
        pool = ["number_pattern", "logic_puzzle", "social_judgment", "investment_pick"]
    elif set_code == "creativity_focus":
        pool = ["ad_copy", "social_judgment", "investment_pick", "reaction_tap"]
    else:
        pool = [x["code"] for x in GAME_TYPES]
    return [pool[i % len(pool)] for i in range(round_count)]


def generate_rounds(set_code: str, round_count: int) -> list[dict]:
    rounds = []
    for idx, game_code in enumerate(choose_game_types(set_code, round_count), start=1):
        prompt, expected = random.choice(QUESTION_BANK[game_code])
        rounds.append(
            {
                "round_no": idx,
                "game_type_code": game_code,
                "prompt": prompt,
                "expected_answer": expected,
                "human_answer": None,
                "ai_answer": None,
                "human_score": 0,
                "ai_score": 0,
                "winner": None,
            }
        )
    return rounds


def score_answer(game_type_code: str, expected: str, answer: str, latency_ms: int) -> int:
    if game_type_code == "ad_copy":
        base = min(100, max(20, len(answer) * 5))
    else:
        base = 80 if answer.strip().lower() == expected.strip().lower() else 30
    speed_bonus = max(0, 20 - latency_ms // 500)
    return min(100, base + speed_bonus)


def ai_answer_and_score(round_data: dict, difficulty: str) -> tuple[str, int]:
    mistake_rate = {"easy": 0.35, "normal": 0.2, "hard": 0.1}[difficulty]
    ai_answer = "wrong" if random.random() < mistake_rate else round_data["expected_answer"]
    ai_latency = {"easy": 1800, "normal": 1200, "hard": 800}[difficulty]
    ai_score = score_answer(round_data["game_type_code"], round_data["expected_answer"], ai_answer, ai_latency)
    return ai_answer, ai_score


class Handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        path = urlparse(self.path).path

        if path == "/":
            return html_response(self, 200, INDEX_FILE.read_bytes())
        if path == "/healthz":
            return json_response(self, 200, {"status": "ok", "service": "ai-arena"})

        if path == "/api/v1/ai-models":
            return json_response(self, 200, AI_MODELS)
        if path == "/api/v1/game-types":
            return json_response(self, 200, GAME_TYPES)

        if path.startswith("/api/v1/matches/") and "/rounds/" in path:
            parts = path.strip("/").split("/")
            if len(parts) < 6:
                return json_response(self, 404, {"detail": "Not found"})
            match_id, round_no = parts[3], int(parts[5])
            match = MATCHES.get(match_id)
            if not match:
                return json_response(self, 404, {"detail": "Match not found"})
            if round_no < 1 or round_no > len(match["rounds"]):
                return json_response(self, 404, {"detail": "Round not found"})
            r = match["rounds"][round_no - 1]
            return json_response(self, 200, {"round_no": r["round_no"], "game_type_code": r["game_type_code"], "prompt": r["prompt"]})

        if path.startswith("/api/v1/matches/") and path.endswith("/report"):
            match_id = path.strip("/").split("/")[3]
            match = MATCHES.get(match_id)
            if not match:
                return json_response(self, 404, {"detail": "Match not found"})
            if match["status"] != "finished":
                return json_response(self, 400, {"detail": "Match not finished"})

            categories = {}
            type_to_category = {g["code"]: g["category"] for g in GAME_TYPES}
            for r in match["rounds"]:
                cat = type_to_category[r["game_type_code"]]
                categories.setdefault(cat, {"human": 0, "ai": 0})
                categories[cat]["human"] += r["human_score"]
                categories[cat]["ai"] += r["ai_score"]
            viral = "당신은 AI를 이겼습니다!" if match["winner"] == "human" else "재도전해보세요!"
            return json_response(
                self,
                200,
                {
                    "winner": match["winner"],
                    "total": {"human": match["human_total_score"], "ai": match["ai_total_score"]},
                    "category_breakdown": categories,
                    "viral_title": viral,
                },
            )

        if path.startswith("/api/v1/matches/"):
            match_id = path.strip("/").split("/")[3]
            match = MATCHES.get(match_id)
            if not match:
                return json_response(self, 404, {"detail": "Match not found"})
            return json_response(self, 200, match)

        if path == "/api/v1/leaderboard":
            query = parse_qs(urlparse(self.path).query)
            period = query.get("period", ["weekly"])[0]
            mode = query.get("mode", ["duel"])[0]
            finished = [m for m in MATCHES.values() if m["status"] == "finished"]
            ranking = sorted(finished, key=lambda m: m["human_total_score"] - m["ai_total_score"], reverse=True)
            rows = []
            for i, m in enumerate(ranking[:20], start=1):
                rows.append(
                    {
                        "rank": i,
                        "user_id": m["user_id"],
                        "rating": 1000 + m["human_total_score"] - m["ai_total_score"],
                        "wins": 1 if m["winner"] == "human" else 0,
                        "losses": 1 if m["winner"] == "ai" else 0,
                    }
                )
            return json_response(self, 200, {"period": period, "mode": mode, "rows": rows})

        return json_response(self, 404, {"detail": "Not found"})

    def do_POST(self):
        path = urlparse(self.path).path

        if path == "/api/v1/auth/guest":
            user_id = f"u_{uuid.uuid4().hex[:8]}"
            USERS[user_id] = {"user_id": user_id, "nickname": f"guest-{user_id[-4:]}", "created_at": now_iso()}
            return json_response(self, 200, {"user_id": user_id, "token": f"token-{user_id}"})

        if path == "/api/v1/matches":
            payload = parse_json(self)
            user_id = payload.get("user_id")
            ai_model_code = payload.get("ai_model_code")
            round_count = max(3, min(5, int(payload.get("round_count", 5))))
            difficulty = payload.get("difficulty", "normal")
            set_code = payload.get("set_code", "quick_mix_5")

            if user_id not in USERS:
                return json_response(self, 404, {"detail": "User not found"})
            if ai_model_code not in [m["code"] for m in AI_MODELS]:
                return json_response(self, 404, {"detail": "AI model not found"})
            if difficulty not in {"easy", "normal", "hard"}:
                return json_response(self, 400, {"detail": "Invalid difficulty"})

            match_id = f"m_{uuid.uuid4().hex[:8]}"
            MATCHES[match_id] = {
                "match_id": match_id,
                "user_id": user_id,
                "ai_model_code": ai_model_code,
                "mode": "duel",
                "status": "created",
                "difficulty": difficulty,
                "round_count": round_count,
                "rounds": generate_rounds(set_code, round_count),
                "human_total_score": 0,
                "ai_total_score": 0,
                "winner": None,
                "started_at": None,
                "ended_at": None,
            }
            return json_response(self, 200, {"match_id": match_id, "status": "created"})

        if path.startswith("/api/v1/matches/") and path.endswith("/start"):
            match_id = path.strip("/").split("/")[3]
            match = MATCHES.get(match_id)
            if not match:
                return json_response(self, 404, {"detail": "Match not found"})
            match["status"] = "in_progress"
            match["started_at"] = now_iso()
            return json_response(self, 200, {"match_id": match_id, "status": "in_progress"})

        if path.startswith("/api/v1/matches/") and "/rounds/" in path and path.endswith("/submit"):
            parts = path.strip("/").split("/")
            if len(parts) < 7:
                return json_response(self, 404, {"detail": "Not found"})
            match_id, round_no = parts[3], int(parts[5])
            payload = parse_json(self)
            match = MATCHES.get(match_id)
            if not match:
                return json_response(self, 404, {"detail": "Match not found"})
            if match["status"] != "in_progress":
                return json_response(self, 400, {"detail": "Match is not in progress"})
            if round_no < 1 or round_no > len(match["rounds"]):
                return json_response(self, 404, {"detail": "Round not found"})

            r = match["rounds"][round_no - 1]
            if r["winner"] is not None:
                return json_response(self, 400, {"detail": "Round already submitted"})

            answer = payload.get("answer", {}).get("final_answer", "")
            latency = int(payload.get("latency_ms", 1000))
            human_score = score_answer(r["game_type_code"], r["expected_answer"], answer, latency)
            ai_answer, ai_score = ai_answer_and_score(r, match["difficulty"])

            winner = "draw"
            if human_score > ai_score:
                winner = "human"
            elif human_score < ai_score:
                winner = "ai"

            r["human_answer"] = answer
            r["ai_answer"] = ai_answer
            r["human_score"] = human_score
            r["ai_score"] = ai_score
            r["winner"] = winner
            match["human_total_score"] += human_score
            match["ai_total_score"] += ai_score

            return json_response(self, 200, {"round_result": {"human_score": human_score, "ai_score": ai_score, "winner": winner}})

        if path.startswith("/api/v1/matches/") and path.endswith("/finish"):
            match_id = path.strip("/").split("/")[3]
            match = MATCHES.get(match_id)
            if not match:
                return json_response(self, 404, {"detail": "Match not found"})

            if match["human_total_score"] > match["ai_total_score"]:
                match["winner"] = "human"
            elif match["human_total_score"] < match["ai_total_score"]:
                match["winner"] = "ai"
            else:
                match["winner"] = "draw"
            match["status"] = "finished"
            match["ended_at"] = now_iso()
            return json_response(
                self,
                200,
                {
                    "match_id": match_id,
                    "winner": match["winner"],
                    "human_total_score": match["human_total_score"],
                    "ai_total_score": match["ai_total_score"],
                },
            )

        if path.startswith("/api/v1/matches/") and path.endswith("/share-image"):
            match_id = path.strip("/").split("/")[3]
            if match_id not in MATCHES:
                return json_response(self, 404, {"detail": "Match not found"})
            return json_response(self, 200, {"share_image_url": f"https://example.com/share/{match_id}.png"})

        return json_response(self, 404, {"detail": "Not found"})


def run() -> None:
    port = int(os.environ.get("PORT", "8000"))
    host = os.environ.get("HOST", "0.0.0.0")
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"AI Arena server running: http://{host}:{port}")
    server.serve_forever()


if __name__ == "__main__":
    run()
