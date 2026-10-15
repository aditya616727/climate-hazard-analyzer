"""AI layer: grounded natural-language insights + Q&A over analysis results.

Design rule (important for the "honest insight" evaluation): the LLM never
invents numbers. We compute every statistic in Python, inject them into the
prompt as verified facts, and ask the model only to *explain* them. If no
API key is configured, we degrade to a deterministic template summary.
"""

from app.config import settings
from app.models import AnalyzeResponse


def verified_facts(a: AnalyzeResponse, region_label: str) -> str:
    t = a.trend
    lines = [
        f"Region: {region_label}",
        f"Heatwave definition: 3+ consecutive days above {a.threshold_c:.1f}°C "
        f"(95th percentile of baseline).",
        f"Total heatwave events: {len(a.events)}",
        f"Trend direction: {t.trend_direction} ({t.slope_per_year:+.3f} events/year)",
        f"First-5yr vs last-5yr change: "
        f"{t.pct_change_vs_baseline if t.pct_change_vs_baseline is not None else 'n/a'}%",
    ]
    if a.events:
        longest = max(a.events, key=lambda e: e.duration_days)
        lines.append(
            f"Longest heatwave: {longest.duration_days} days "
            f"({longest.start_date} to {longest.end_date}), peak {longest.max_temp_c:.1f}°C."
        )
    worst = max(a.yearly, key=lambda y: y.heatwave_days, default=None)
    if worst and worst.heatwave_days:
        lines.append(f"Worst year: {worst.year} ({worst.heatwave_days} heatwave days).")
    return "\n".join(lines)


def template_summary(a: AnalyzeResponse, region_label: str) -> str:
    facts = verified_facts(a, region_label).replace("\n", " ")
    return f"{a.headline} Key facts: {facts}"


async def ai_narrative(a: AnalyzeResponse, region_label: str) -> str:
    """3-4 sentence plain-language briefing. Falls back to template without a key."""
    if not settings.openai_api_key:
        return template_summary(a, region_label)
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    system = (
        "You are a climate-data explainer. You are given VERIFIED statistics computed "
        "from observations. Write a 3-4 sentence briefing for a non-technical reader. "
        "Only use the numbers provided. Never invent numbers, causes, or predictions. "
        "If the trend is flat or uncertain, say so honestly."
    )
    resp = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": f"Explain these findings:\n{verified_facts(a, region_label)}"},
        ],
        temperature=0.3,
        max_tokens=300,
    )
    return resp.choices[0].message.content.strip()


async def ai_answer(a: AnalyzeResponse, region_label: str, question: str) -> str:
    """Grounded Q&A: the model may only answer from the verified facts + headline."""
    if not settings.openai_api_key:
        return (
            "AI Q&A needs an OpenAI-compatible API key (set OPENAI_API_KEY). "
            f"Meanwhile: {a.headline}"
        )
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    system = (
        "Answer the user's question about heatwave trends using ONLY the verified "
        "statistics below. If the question cannot be answered from them, say so "
        "plainly instead of guessing. Be concise (2-3 sentences)."
    )
    resp = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": system},
            {
                "role": "user",
                "content": f"Facts:\n{verified_facts(a, region_label)}\n\n"
                           f"Headline: {a.headline}\n\nQuestion: {question}",
            },
        ],
        temperature=0.2,
        max_tokens=250,
    )
    return resp.choices[0].message.content.strip()
