import logging
import random
from collections import Counter
from typing import List, Dict, Tuple

logger = logging.getLogger(__name__)

class WinGoPredictor:
    def __init__(self):
        # Default fallback weights
        self.streak_threshold = 3
        self.pattern_window = 20

    def analyze(self, history: List[Dict]) -> Dict:
        """
        Analyzes historical data and returns:
        - predicted_choice: 'BIG' or 'SMALL'
        - lucky_numbers: list of 2 or 3 recommended numbers
        - confidence: int (e.g. 85)
        - pattern_name: str (e.g. 'Dragon Trend Follower')
        """
        if not history or len(history) < 5:
            choice = random.choice(["BIG", "SMALL"])
            numbers = [5, 7] if choice == "BIG" else [1, 3]
            return {
                "choice": choice,
                "numbers": numbers,
                "confidence": 70,
                "pattern_name": "Initial Baseline Analysis"
            }

        outcomes = [item["big_small"] for item in history[:self.pattern_window]]
        numbers_history = [item["number"] for item in history[:self.pattern_window]]

        # 1. Streak / Dragon Detection
        streak_choice, streak_conf, streak_type = self._detect_streak(outcomes)

        # 2. Alternating (1-1 ZigZag) Pattern Detection
        zigzag_choice, zigzag_conf = self._detect_zigzag(outcomes)

        # 3. Markov Transition Probability
        markov_choice, markov_conf = self._markov_prediction(outcomes)

        # 4. Balance / Deviation Analysis
        balance_choice, balance_conf = self._balance_analysis(outcomes)

        # Vote Aggregation (Ensemble)
        votes = {"BIG": 0.0, "SMALL": 0.0}
        pattern_reasons = []

        if streak_choice and streak_conf > 0:
            votes[streak_choice] += streak_conf * 1.5
            pattern_reasons.append(streak_type)

        if zigzag_choice and zigzag_conf > 0:
            votes[zigzag_choice] += zigzag_conf * 1.3
            pattern_reasons.append("⚡ 1-1 Zig-Zag Cycle")

        if markov_choice:
            votes[markov_choice] += markov_conf * 1.2
            pattern_reasons.append("📊 Markov Transition")

        if balance_choice:
            votes[balance_choice] += balance_conf * 1.0

        # Determine winner
        if votes["BIG"] >= votes["SMALL"]:
            final_choice = "BIG"
            win_score = votes["BIG"]
            total_score = votes["BIG"] + votes["SMALL"] if (votes["BIG"] + votes["SMALL"]) > 0 else 1
        else:
            final_choice = "SMALL"
            win_score = votes["SMALL"]
            total_score = votes["BIG"] + votes["SMALL"] if (votes["BIG"] + votes["SMALL"]) > 0 else 1

        raw_conf = (win_score / total_score) * 100 if total_score > 0 else 75
        confidence = int(max(75, min(95, raw_conf)))

        pattern_name = pattern_reasons[0] if pattern_reasons else "📈 Trend Momentum"

        # 5. Pick Lucky Numbers (No Colors, only numbers matching the choice)
        lucky_numbers = self._predict_lucky_numbers(final_choice, numbers_history)

        return {
            "choice": final_choice,
            "numbers": lucky_numbers,
            "confidence": confidence,
            "pattern_name": pattern_name
        }

    def _detect_streak(self, outcomes: List[str]) -> Tuple[str, float, str]:
        """Detects if we are currently in a streak (Dragon)"""
        current_type = outcomes[0]
        streak_len = 1
        for i in range(1, len(outcomes)):
            if outcomes[i] == current_type:
                streak_len += 1
            else:
                break

        if streak_len >= 5:
            # Very long dragon streak -> high probability trend continuation
            return current_type, 85.0, f"🐉 Super Dragon ({streak_len}x {current_type})"
        elif streak_len >= 3:
            return current_type, 75.0, f"🔥 Dragon Trend ({streak_len}x {current_type})"
        return None, 0.0, ""

    def _detect_zigzag(self, outcomes: List[str]) -> Tuple[str, float]:
        """Detects 1-1 alternating sequence: B-S-B-S or S-B-S-B"""
        if len(outcomes) < 4:
            return None, 0.0

        is_alternating = True
        for i in range(len(outcomes[:4]) - 1):
            if outcomes[i] == outcomes[i + 1]:
                is_alternating = False
                break

        if is_alternating:
            # If alternating, next is opposite of the most recent
            next_predicted = "BIG" if outcomes[0] == "SMALL" else "SMALL"
            return next_predicted, 80.0
        return None, 0.0

    def _markov_prediction(self, outcomes: List[str]) -> Tuple[str, float]:
        """Calculates 1st order Markov transition matrix"""
        transitions = {"BIG": {"BIG": 0, "SMALL": 0}, "SMALL": {"BIG": 0, "SMALL": 0}}
        for i in range(len(outcomes) - 1):
            prev = outcomes[i + 1]
            curr = outcomes[i]
            transitions[prev][curr] += 1

        last = outcomes[0]
        big_trans = transitions[last]["BIG"]
        small_trans = transitions[last]["SMALL"]
        total = big_trans + small_trans

        if total == 0:
            return random.choice(["BIG", "SMALL"]), 60.0

        if big_trans > small_trans:
            return "BIG", (big_trans / total) * 100
        else:
            return "SMALL", (small_trans / total) * 100

    def _balance_analysis(self, outcomes: List[str]) -> Tuple[str, float]:
        """Detects extreme frequency skew in last 15 rounds"""
        recent = outcomes[:15]
        big_count = recent.count("BIG")
        small_count = recent.count("SMALL")

        if big_count >= 11:
            # Heavily skewed towards BIG -> mean reversion favors SMALL
            return "SMALL", 70.0
        elif small_count >= 11:
            return "BIG", 70.0
        return None, 0.0

    def _predict_lucky_numbers(self, choice: str, numbers_history: List[int]) -> List[int]:
        """
        Calculates 2 or 3 high-probability numbers strictly within the chosen pool:
        - If BIG -> choose from [5, 6, 7, 8, 9]
        - If SMALL -> choose from [0, 1, 2, 3, 4]
        """
        pool = [5, 6, 7, 8, 9] if choice == "BIG" else [0, 1, 2, 3, 4]
        pool_counts = Counter([n for n in numbers_history if n in pool])

        # Score numbers based on frequency and gap
        scored = []
        for num in pool:
            # Frequency score
            freq = pool_counts.get(num, 0)

            # Gap score (how many rounds since this number appeared)
            gap = 20
            for idx, past_num in enumerate(numbers_history):
                if past_num == num:
                    gap = idx
                    break

            # Weighted combination of hot number + due number
            score = (freq * 1.5) + (gap * 0.8) + random.uniform(0.1, 0.5)
            scored.append((num, score))

        # Sort by score descending and take top 2 numbers
        scored.sort(key=lambda x: x[1], reverse=True)
        top_numbers = [item[0] for item in scored[:2]]
        top_numbers.sort()
        return top_numbers

predictor = WinGoPredictor()
