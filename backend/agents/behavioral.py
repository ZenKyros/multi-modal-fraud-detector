# agents/behavioral.py
from typing import List, Dict, Any
import numpy as np

class BehavioralAgent:
    """
    Analyzes speaker behavior patterns from transcribed segments.
    Requires segments with optional speaker labels.
    """

    def analyze(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        segments: list of dicts with keys: speaker, text, start, end (optional)
        Returns: speaker dominance, interruptions, turn-taking stats.
        """
        if not segments:
            return self._empty_result()

        speakers = {}
        total_words = 0
        total_duration = 0
        interruptions = 0

        for i, seg in enumerate(segments):
            spk = seg.get("speaker", "UNKNOWN")
            words = len(seg.get("text", "").split())
            dur = seg.get("end", 0) - seg.get("start", 0)
            if spk not in speakers:
                speakers[spk] = {"word_count": 0, "duration": 0, "turns": 0}
            speakers[spk]["word_count"] += words
            speakers[spk]["duration"] += max(0, dur)
            speakers[spk]["turns"] += 1
            total_words += words
            total_duration += max(0, dur)

        # Count interruptions: if a speaker starts before previous ends (gap < 0.2s)
        for i in range(1, len(segments)):
            prev_end = segments[i-1].get("end", 0)
            curr_start = segments[i].get("start", 0)
            if curr_start - prev_end < 0.2 and segments[i].get("speaker") != segments[i-1].get("speaker"):
                interruptions += 1

        # Dominance ratio: words spoken by most talkative speaker / total
        if speakers:
            max_words = max(s["word_count"] for s in speakers.values())
            dominance = max_words / total_words if total_words > 0 else 0
            # Average turn length
            avg_turn_words = np.mean([s["word_count"]/s["turns"] for s in speakers.values() if s["turns"]>0]) if speakers else 0
        else:
            dominance = 0
            avg_turn_words = 0

        return {
            "speaker_count": len(speakers),
            "speakers": {spk: {"word_pct": round(d["word_count"]/total_words,2) if total_words else 0,
                               "duration_pct": round(d["duration"]/total_duration,2) if total_duration else 0,
                               "turns": d["turns"]}
                         for spk, d in speakers.items()},
            "dominance_ratio": round(dominance, 2),   # high => monologue (scammer)
            "interruption_count": interruptions,
            "avg_turn_words": round(avg_turn_words, 1),
            # Behavioral risk score: high dominance + many interruptions
            "behavior_score": round(min(1.0, dominance*0.6 + (interruptions/5)*0.4), 3)
        }

    def _empty_result(self):
        return {
            "speaker_count": 0,
            "speakers": {},
            "dominance_ratio": 0,
            "interruption_count": 0,
            "avg_turn_words": 0,
            "behavior_score": 0.0
        }