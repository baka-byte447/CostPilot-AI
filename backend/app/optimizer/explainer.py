import os
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = "llama3-8b-8192"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _build_prompt(decision: dict) -> str:
    action = decision.get("action")
    cpu = decision.get("cpu")
    memory = decision.get("memory")
    req = decision.get("request_load")
    replicas = decision.get("replicas")
    reward = decision.get("reward")
    violations = decision.get("safety", {}).get("violations", [])
    proposed = decision.get("proposed_action")
    q_values = decision.get("q_values", {})

    parts = [
        f"Action taken: {action}",
        f"CPU: {cpu}%, Memory: {memory}%, Requests: {req}/s",
        f"Replicas after action: {replicas}",
        f"Reward: {reward}",
        f"Q-values: scale_up={q_values.get('scale_up')}, maintain={q_values.get('maintain')}, scale_down={q_values.get('scale_down')}",
    ]

    if violations:
        parts.append(f"Safety override: proposed {proposed} but blocked because {violations[0]}")

    parts.append("Explain this decision in 2-3 plain English sentences for a technical audience.")

    return "\n".join(parts)


def _groq_explain(decision: dict) -> str:
    import requests as req_lib
    prompt = _build_prompt(decision)
    try:
        resp = req_lib.post(
            GROQ_URL,
            headers={
                "Authorization": f"Bearer {GROQ_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "llama3-8b-8192",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a cloud infrastructure assistant. Explain scaling decisions concisely in 2-3 sentences."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 150,
                "temperature": 0.4
            },
            timeout=8
        )
        if resp.status_code != 200:
            logger.warning(f"Groq returned {resp.status_code}: {resp.text[:200]}")
            return None
        text = resp.json()["choices"][0]["message"]["content"].strip()
        logger.info(f"Groq explanation generated ({len(text)} chars)")
        return text
    except Exception as e:
        logger.warning(f"Groq API failed ({type(e).__name__}): {e} — falling back to rule-based")
        return None


def _rule_based_explain(decision: dict) -> str:
    action = decision.get("action")
    cpu = decision.get("cpu")
    memory = decision.get("memory")
    req = decision.get("request_load")
    replicas = decision.get("replicas")
    reward = decision.get("reward")
    safety = decision.get("safety", {})
    violations = safety.get("violations", [])
    proposed = decision.get("proposed_action")

    hourly_cost = round(replicas * 0.0416, 4)

    if violations:
        override_reason = violations[0]
        base = (
            f"The RL agent proposed to {proposed}, but the Safety Engine blocked this action "
            f"because: {override_reason}. "
            f"Action was overridden to '{action}' to maintain service reliability. "
            f"Current metrics — CPU: {cpu}%, Memory: {memory}%, Requests: {req}/s. "
            f"Running at {replicas} replica(s) at ${hourly_cost}/hour."
        )
        return base

    if action == "scale_up":
        reasons = []
        if cpu > 70:
            reasons.append(f"CPU is elevated at {cpu}%")
        if memory > 70:
            reasons.append(f"memory pressure at {memory}%")
        if req > 0.4:
            reasons.append(f"request load is high at {req}/s")
        reason_text = " and ".join(reasons) if reasons else f"workload conditions at CPU={cpu}%, Memory={memory}%"
        return (
            f"Scaled up to {replicas} replica(s) because {reason_text}. "
            f"The agent chose scale_up with a reward of {reward} to prevent under-provisioning. "
            f"Estimated cost: ${hourly_cost}/hour."
        )

    if action == "scale_down":
        return (
            f"Scaled down to {replicas} replica(s) because CPU is at {cpu}%, "
            f"memory at {memory}%, and request load at {req}/s — all within safe thresholds. "
            f"This saves cost by removing unused capacity. "
            f"Estimated cost after reduction: ${hourly_cost}/hour."
        )

    if action == "maintain":
        if cpu > 40 and cpu <= 70:
            reason = f"CPU at {cpu}% is in the moderate range"
        elif cpu <= 40:
            reason = f"load is stable with CPU at {cpu}%"
        else:
            reason = f"metrics are within acceptable bounds"
        return (
            f"Maintained current {replicas} replica(s) because {reason}, "
            f"memory at {memory}%, and requests at {req}/s. "
            f"No scaling action was needed. Current cost: ${hourly_cost}/hour."
        )

    return f"Action '{action}' taken with {replicas} replica(s). CPU={cpu}%, Memory={memory}%, Cost=${hourly_cost}/hour."


def explain_decision(decision: dict) -> dict:
    source = "rule_based"
    explanation = None

    if GROQ_API_KEY:
        explanation = _groq_explain(decision)
        if explanation:
            source = "groq_llama3"

    if not explanation:
        explanation = _rule_based_explain(decision)

    return {
        "explanation": explanation,
        "source": source,
        "timestamp": datetime.utcnow().isoformat(),
        "action": decision.get("action"),
        "cpu": decision.get("cpu"),
        "memory": decision.get("memory"),
        "request_load": decision.get("request_load"),
        "replicas": decision.get("replicas"),
        "safety_overridden": len(decision.get("safety", {}).get("violations", [])) > 0
    }