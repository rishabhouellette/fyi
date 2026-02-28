"""AI routes: captions, hashtags, XY-AI engine, image/video/voice generation, translate."""
import os
import re
import json
import random
import asyncio
from datetime import datetime
from typing import Any, Optional
from uuid import uuid4

import httpx
from fastapi import APIRouter, HTTPException

from core.config import DATA_DIR, UPLOADS_DIR, _get_byok_key, _add_usage
from core.models import (
    AICaptionRequest, AIHashtagsRequest,
    XYAIPromptRequest, XYAITrendRequest, XYAIChatRequest, XYAIContentPlanRequest,
    AIImageRequest, AIVideoRequest, AIVoiceRequest, TranslateRequest,
)
from core.utils import _split_hashtags, _ollama_models, _ollama_generate

router = APIRouter()


# ═══════════════════════════════════════════════════════════════════════════════
# AI Caption & Hashtags
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/ai/caption")
async def ai_generate_caption(request: AICaptionRequest):
    topic = (request.topic or "").strip()
    if not topic:
        raise HTTPException(status_code=400, detail="topic is required")

    platform = (request.platform or "instagram").strip().lower()
    tone = (request.tone or "casual").strip().lower()
    max_length = max(40, min(int(request.max_length or 220), 1000))
    hashtags_count = max(0, min(int(request.hashtags_count or 0), 30))
    keywords = [k.strip() for k in (request.keywords or []) if isinstance(k, str) and k.strip()]

    model = (os.getenv("FYI_OLLAMA_MODEL") or "").strip()
    models = await _ollama_models()
    if not model and models:
        model = models[0]

    if model:
        try:
            system = "You write concise, high-performing social media captions. Return only the caption text."
            kw = f"\nKeywords: {', '.join(keywords)}" if keywords else ""
            prompt = (
                f"Platform: {platform}\n"
                f"Tone: {tone}\n"
                f"Topic: {topic}{kw}\n"
                f"Constraints: max {max_length} characters."
            )
            caption = await _ollama_generate(prompt=prompt, model=model, system=system, timeout_s=25.0)
            caption = caption.strip().strip('"').strip("'")
            if len(caption) > max_length:
                caption = caption[: max_length - 1].rstrip() + "…"

            hashtags: list[str] = []
            if request.include_hashtags and hashtags_count > 0:
                system2 = "Return only hashtags separated by spaces. No explanations."
                prompt2 = (
                    f"Generate {hashtags_count} relevant hashtags for platform={platform}.\n"
                    f"Topic: {topic}{kw}"
                )
                ht = await _ollama_generate(prompt=prompt2, model=model, system=system2, timeout_s=25.0)
                hashtags = _split_hashtags(ht)[:hashtags_count]

            return {
                "success": True, "mode": "ollama", "model": model,
                "caption": caption, "hashtags": hashtags,
            }
        except Exception:
            pass

    # Deterministic fallback
    templates = {
        "casual": ["{topic} — thoughts?", "Quick update: {topic}", "If you're into {topic}, this one's for you."],
        "professional": ["{topic}. Key takeaways in the comments.", "{topic} — a practical breakdown."],
        "funny": ["Me, pretending I didn't just spend hours on {topic}.", "POV: {topic} was 'quick'…"],
        "inspirational": ["{topic}. Keep going.", "{topic} — progress over perfection."],
    }
    pool = templates.get(tone, templates["casual"])
    base = pool[hash((topic, tone, platform)) % len(pool)].format(topic=topic)
    extras = []
    if keywords:
        extras.append(" • ".join(keywords[:3]))
    caption = (base + ("\n" + extras[0] if extras else "")).strip()
    if len(caption) > max_length:
        caption = caption[: max_length - 1].rstrip() + "…"

    hashtags: list[str] = []
    if request.include_hashtags and hashtags_count > 0:
        seed_words = []
        seed_words.extend(re.findall(r"[A-Za-z0-9_]{4,}", topic))
        seed_words.extend([re.sub(r"[^A-Za-z0-9_]", "", k) for k in keywords])
        seed_words = [w for w in seed_words if w]
        base_tags = [f"#{w[:20]}" for w in seed_words[: max(1, hashtags_count)]]
        trending = ["#trending", "#viral", "#explore"] if platform in ("instagram", "tiktok") else []
        hashtags = list(dict.fromkeys(base_tags + trending))[:hashtags_count]

    return {"success": True, "mode": "fallback", "model": None, "caption": caption, "hashtags": hashtags}


@router.post("/api/ai/hashtags")
async def ai_generate_hashtags(request: AIHashtagsRequest):
    topic = (request.topic or "").strip()
    if not topic:
        raise HTTPException(status_code=400, detail="topic is required")

    platform = (request.platform or "instagram").strip().lower()
    count = max(1, min(int(request.count or 12), 30))

    model = (os.getenv("FYI_OLLAMA_MODEL") or "").strip()
    models = await _ollama_models()
    if not model and models:
        model = models[0]
    if model:
        try:
            system = "Return only hashtags separated by spaces. No explanations."
            prompt = f"Generate {count} relevant hashtags for platform={platform}. Topic: {topic}"
            out = await _ollama_generate(prompt=prompt, model=model, system=system, timeout_s=25.0)
            tags = _split_hashtags(out)
            if request.include_trending and platform in ("instagram", "tiktok"):
                tags = list(dict.fromkeys(tags + ["#trending", "#viral", "#explore"]))
            return {"success": True, "mode": "ollama", "model": model, "hashtags": tags[:count]}
        except Exception:
            pass

    words = re.findall(r"[A-Za-z0-9_]{4,}", topic)
    tags = [f"#{w[:20]}" for w in words[:count]]
    if request.include_trending and platform in ("instagram", "tiktok"):
        tags = list(dict.fromkeys(tags + ["#trending", "#viral", "#explore"]))
    tags = tags[:count]
    if not tags:
        tags = ["#content", "#creator"][:count]
    return {"success": True, "mode": "fallback", "model": None, "hashtags": tags}


# ═══════════════════════════════════════════════════════════════════════════════
# XY-AI Engine — built-in trend knowledge base
# ═══════════════════════════════════════════════════════════════════════════════

_TREND_DB: dict[str, dict] = {
    "fitness": {
        "hashtags": ["#FitTok", "#GymMotivation", "#WorkoutRoutine", "#HealthyLifestyle", "#FitnessJourney", "#GymLife", "#TransformationTuesday", "#Gains", "#FitCheck", "#ActiveLifestyle"],
        "topics": ["75 Hard challenge updates", "Morning routine that changed my body", "What I eat in a day (high protein)", "Gym fails compilation", "3 exercises you're doing wrong", "Progressive overload explained simply"],
        "formats": ["Before/After transformation", "Day-in-the-life vlog", "Quick tips carousel", "Workout follow-along Reel", "Myth-busting thread"],
        "hooks": ["Stop doing this exercise NOW", "I gained 10lbs of muscle in 90 days — here's how", "The workout nobody talks about", "Your trainer won't tell you this"],
    },
    "tech": {
        "hashtags": ["#TechTok", "#AI", "#Coding", "#StartupLife", "#TechNews", "#Innovation", "#MachineLearning", "#WebDev", "#AppDev", "#FutureTech"],
        "topics": ["AI tools that save 10 hours/week", "Best VS Code extensions 2026", "Why I quit my FAANG job", "Build this in 10 minutes with AI", "Tech I regret buying", "Hidden iPhone/Android features"],
        "formats": ["Screen recording tutorial", "Hot take thread", "Tool comparison carousel", "Code-along Reel", "React to tech news"],
        "hooks": ["This AI tool replaced my entire team", "Stop using ChatGPT like this", "The app that made me $10K", "Every developer needs this"],
    },
    "food": {
        "hashtags": ["#FoodTok", "#RecipeOfTheDay", "#Foodie", "#HomeCooking", "#EasyRecipes", "#MealPrep", "#HealthyEating", "#Yummy", "#CookingHacks", "#FoodPorn"],
        "topics": ["5-minute meals that actually taste good", "Meal prep Sunday ideas", "I tried the viral TikTok recipe", "Restaurant quality at home", "Budget grocery haul", "Protein-packed snacks"],
        "formats": ["Overhead cooking video", "Taste test reaction", "Recipe carousel with steps", "Grocery haul vlog", "Before/after plating"],
        "hooks": ["You've been cooking pasta WRONG", "This 3-ingredient dessert broke the internet", "The meal that costs $2 and feeds 4", "Chefs hate this hack"],
    },
    "business": {
        "hashtags": ["#Entrepreneur", "#StartupLife", "#SmallBusiness", "#SideHustle", "#BusinessTips", "#Marketing", "#PersonalBrand", "#Hustle", "#MoneyMindset", "#GrowthHacking"],
        "topics": ["How I got my first 1000 customers", "Marketing mistakes costing you money", "The $0 marketing strategy that works", "Day in my life as a founder", "Tools I use to run my business", "How to price your services"],
        "formats": ["Story-time with lessons", "Step-by-step guide carousel", "Hot take tweet thread", "Revenue screenshot breakdown", "Behind-the-scenes day vlog"],
        "hooks": ["I made $50K from a single post — here's how", "Stop wasting money on ads", "The business model nobody talks about", "Why 90% of startups fail (and how to be the 10%)"],
    },
    "beauty": {
        "hashtags": ["#BeautyTok", "#MakeupTutorial", "#Skincare", "#GRWM", "#GlowUp", "#BeautyHacks", "#SkincareRoutine", "#MakeupLook", "#CleanBeauty", "#BeautyReview"],
        "topics": ["My holy grail skincare routine", "Drugstore vs high-end dupes", "GRWM for date night", "Skincare mistakes ruining your skin", "Clean beauty products that work", "Glass skin routine"],
        "formats": ["Get Ready With Me", "Product review haul", "Split-screen dupes comparison", "Satisfying skincare Reel", "Tutorial carousel"],
        "hooks": ["Dermatologists are BEGGING you to stop this", "The $8 product that replaced my $60 serum", "I tried the viral skincare hack for 30 days", "You're applying sunscreen wrong"],
    },
    "travel": {
        "hashtags": ["#TravelTok", "#Wanderlust", "#TravelGuide", "#HiddenGems", "#BudgetTravel", "#TravelHacks", "#Explore", "#Adventure", "#Backpacking", "#TravelVlog"],
        "topics": ["Hidden gems in [City]", "How I travel for cheap", "Things I wish I knew before visiting", "Best cafes to work from remotely", "Travel packing hacks", "Solo travel tips"],
        "formats": ["Cinematic travel montage", "Top 5 places carousel", "Day vlog in a new city", "Packing Reel", "Drone footage compilation"],
        "hooks": ["Don't visit [Place] without knowing THIS", "I found the cheapest flight hack", "The most underrated country in Europe", "How I travel full-time for $1500/month"],
    },
    "general": {
        "hashtags": ["#Viral", "#Trending", "#ForYouPage", "#FYP", "#Explore", "#ContentCreator", "#DigitalCreator", "#GrowOnSocial", "#SocialMedia", "#CreatorEconomy"],
        "topics": ["How to grow from 0 to 10K followers", "Content batching tips", "The algorithm explained simply", "Engagement hacks that actually work", "How I went viral", "Repurposing content across platforms"],
        "formats": ["Talking head with captions", "Carousel with value bombs", "Duet/stitch reaction", "Story poll series", "Behind-the-scenes Reel"],
        "hooks": ["The algorithm just changed — do THIS now", "I gained 10K followers in 30 days", "Stop posting at the wrong time", "This hack doubled my engagement overnight"],
    },
}


def _match_niche(niche: str | None) -> str:
    """Fuzzy-match user niche to our trend DB keys."""
    if not niche:
        return "general"
    n = niche.strip().lower()
    for key in _TREND_DB:
        if key in n or n in key:
            return key
    mapping = {
        "gym": "fitness", "workout": "fitness", "health": "fitness", "yoga": "fitness", "sport": "fitness",
        "coding": "tech", "programming": "tech", "software": "tech", "app": "tech", "ai": "tech", "developer": "tech",
        "cooking": "food", "recipe": "food", "restaurant": "food", "chef": "food", "meal": "food", "baking": "food",
        "startup": "business", "marketing": "business", "entrepreneur": "business", "brand": "business", "ecommerce": "business", "money": "business",
        "makeup": "beauty", "skincare": "beauty", "cosmetic": "beauty", "hair": "beauty", "fashion": "beauty",
        "travel": "travel", "vacation": "travel", "tourism": "travel", "adventure": "travel", "explore": "travel",
    }
    for kw, cat in mapping.items():
        if kw in n:
            return cat
    return "general"


@router.post("/api/xy-ai/prompts")
async def xy_ai_generate_prompts(request: XYAIPromptRequest):
    """XY-AI: Generate smart content prompts/ideas."""
    goal = (request.goal or "").strip()
    if not goal:
        raise HTTPException(status_code=400, detail="goal is required")

    platform = (request.platform or "instagram").strip().lower()
    content_type = (request.content_type or "post").strip().lower()
    tone = (request.tone or "engaging").strip().lower()
    audience = (request.audience or "").strip()
    niche = (request.niche or "").strip()
    count = max(1, min(request.count, 10))

    model = (os.getenv("FYI_OLLAMA_MODEL") or "").strip()
    models = await _ollama_models()
    if not model and models:
        model = models[0]

    openai_key = _get_byok_key("openai")
    gemini_key = _get_byok_key("gemini")

    prompts_result: list[dict] = []

    # --- Path 1: Ollama ---
    if model:
        try:
            system = (
                "You are XY-AI, FYIXT's creative content strategist. "
                "Generate unique, platform-optimized content prompts. "
                "Return a JSON array of objects with keys: title, caption, hashtags (array), hook, content_type. "
                "Return ONLY valid JSON, no markdown fences."
            )
            aud_part = f"\nTarget audience: {audience}" if audience else ""
            niche_part = f"\nNiche: {niche}" if niche else ""
            prompt = (
                f"Generate {count} viral content ideas.\n"
                f"Goal: {goal}\nPlatform: {platform}\n"
                f"Content type: {content_type}\nTone: {tone}{aud_part}{niche_part}\n"
                f"Make each idea unique with a scroll-stopping hook."
            )
            raw = await _ollama_generate(prompt=prompt, model=model, system=system, timeout_s=30.0)
            raw = raw.strip()
            if raw.startswith("```"):
                raw = re.sub(r"^```\w*\n?", "", raw)
                raw = re.sub(r"\n?```$", "", raw)
            parsed = json.loads(raw)
            if isinstance(parsed, list):
                prompts_result = parsed[:count]
            return {"success": True, "mode": "xy-ai-ollama", "model": model, "prompts": prompts_result, "niche_detected": _match_niche(niche or goal)}
        except Exception:
            pass

    # --- Path 2: OpenAI ---
    if openai_key:
        try:
            aud_part = f"\nTarget audience: {audience}" if audience else ""
            niche_part = f"\nNiche: {niche}" if niche else ""
            messages = [
                {"role": "system", "content": (
                    "You are XY-AI, FYIXT's creative content strategist. "
                    "Generate unique, platform-optimized content prompts. "
                    "Return a JSON array of objects with keys: title, caption, hashtags (array), hook, content_type. "
                    "Return ONLY valid JSON, no markdown."
                )},
                {"role": "user", "content": (
                    f"Generate {count} viral content ideas.\n"
                    f"Goal: {goal}\nPlatform: {platform}\n"
                    f"Content type: {content_type}\nTone: {tone}{aud_part}{niche_part}"
                )},
            ]
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                    json={"model": "gpt-4o-mini", "messages": messages, "temperature": 0.9},
                )
                resp.raise_for_status()
                data = resp.json()
                text = data["choices"][0]["message"]["content"].strip()
                if text.startswith("```"):
                    text = re.sub(r"^```\w*\n?", "", text)
                    text = re.sub(r"\n?```$", "", text)
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    prompts_result = parsed[:count]
                return {"success": True, "mode": "xy-ai-openai", "model": "gpt-4o-mini", "prompts": prompts_result, "niche_detected": _match_niche(niche or goal)}
        except Exception:
            pass

    # --- Path 3: Gemini ---
    if gemini_key:
        try:
            aud_part = f"\nTarget audience: {audience}" if audience else ""
            niche_part = f"\nNiche: {niche}" if niche else ""
            prompt_text = (
                "You are XY-AI, FYIXT's creative content strategist. "
                f"Generate {count} viral content ideas as a JSON array. "
                f"Goal: {goal}. Platform: {platform}. "
                f"Content type: {content_type}. Tone: {tone}.{aud_part}{niche_part}\n"
                "Each object: title, caption, hashtags (array), hook, content_type. "
                "Return ONLY valid JSON."
            )
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}",
                    json={"contents": [{"parts": [{"text": prompt_text}]}]},
                )
                resp.raise_for_status()
                data = resp.json()
                text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                if text.startswith("```"):
                    text = re.sub(r"^```\w*\n?", "", text)
                    text = re.sub(r"\n?```$", "", text)
                parsed = json.loads(text)
                if isinstance(parsed, list):
                    prompts_result = parsed[:count]
                return {"success": True, "mode": "xy-ai-gemini", "model": "gemini-2.5-flash", "prompts": prompts_result, "niche_detected": _match_niche(niche or goal)}
        except Exception:
            pass

    # --- Path 4: Smart deterministic fallback ---
    matched = _match_niche(niche or goal)
    trend_data = _TREND_DB.get(matched, _TREND_DB["general"])
    hooks = trend_data.get("hooks", [])
    topics = trend_data.get("topics", [])
    formats = trend_data.get("formats", [])
    hashtags_pool = trend_data.get("hashtags", [])

    for i in range(count):
        idx = (hash((goal, i, platform)) % max(1, len(topics)))
        hook = hooks[i % len(hooks)] if hooks else f"Here's what you need to know about {goal}"
        topic = topics[idx % len(topics)] if topics else goal
        fmt = formats[i % len(formats)] if formats else "Standard post"
        tags = random.sample(hashtags_pool, min(5, len(hashtags_pool)))

        personalized_hook = hook
        for placeholder in ["[City]", "[Place]"]:
            personalized_hook = personalized_hook.replace(placeholder, goal.split()[0].title() if goal else "this")

        prompts_result.append({
            "title": topic,
            "caption": f"{personalized_hook}\n\n{topic}",
            "hashtags": tags,
            "hook": personalized_hook,
            "content_type": content_type,
            "format_suggestion": fmt,
        })

    return {"success": True, "mode": "xy-ai-smart-fallback", "model": None, "prompts": prompts_result, "niche_detected": matched}


@router.post("/api/xy-ai/trends")
async def xy_ai_get_trends(request: XYAITrendRequest):
    """XY-AI: Discover trending topics, hashtags and content formats for any niche."""
    niche = (request.niche or "").strip()
    platform = (request.platform or "instagram").strip().lower()
    matched = _match_niche(niche)
    trend_data = _TREND_DB.get(matched, _TREND_DB["general"])

    model = (os.getenv("FYI_OLLAMA_MODEL") or "").strip()
    models = await _ollama_models()
    if not model and models:
        model = models[0]

    ai_insights = None
    if model:
        try:
            system = "You are a social media trend analyst. Return a brief JSON with keys: emerging_trends (array of strings), predicted_viral (string), best_posting_times (array), engagement_tip (string). ONLY valid JSON."
            prompt = f"Analyze current {platform} trends for niche: {niche or 'general content creation'}. Country: {request.country}."
            raw = await _ollama_generate(prompt=prompt, model=model, system=system, timeout_s=20.0)
            raw = raw.strip()
            if raw.startswith("```"):
                raw = re.sub(r"^```\w*\n?", "", raw)
                raw = re.sub(r"\n?```$", "", raw)
            ai_insights = json.loads(raw)
        except Exception:
            pass

    if not ai_insights:
        openai_key = _get_byok_key("openai")
        gemini_key = _get_byok_key("gemini")
        if openai_key:
            try:
                messages = [
                    {"role": "system", "content": "You are a social media trend analyst. Return a JSON with keys: emerging_trends (array of 5 strings), predicted_viral (string), best_posting_times (array of 3 strings), engagement_tip (string). ONLY valid JSON."},
                    {"role": "user", "content": f"Analyze current {platform} trends for niche: {niche or 'general'}. Country: {request.country}."},
                ]
                async with httpx.AsyncClient(timeout=25.0) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                        json={"model": "gpt-4o-mini", "messages": messages, "temperature": 0.7},
                    )
                    resp.raise_for_status()
                    text = resp.json()["choices"][0]["message"]["content"].strip()
                    if text.startswith("```"):
                        text = re.sub(r"^```\w*\n?", "", text)
                        text = re.sub(r"\n?```$", "", text)
                    ai_insights = json.loads(text)
            except Exception:
                pass
        elif gemini_key:
            try:
                prompt_text = (
                    "You are a social media trend analyst. "
                    f"Analyze current {platform} trends for niche: {niche or 'general'}. Country: {request.country}. "
                    "Return a JSON with keys: emerging_trends (array of 5 strings), predicted_viral (string), best_posting_times (array of 3 strings), engagement_tip (string). ONLY valid JSON."
                )
                async with httpx.AsyncClient(timeout=30.0) as client:
                    resp = await client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}",
                        json={"contents": [{"parts": [{"text": prompt_text}]}], "tools": [{"google_search": {}}]},
                    )
                    resp.raise_for_status()
                    text = resp.json()["candidates"][0]["content"]["parts"][0]["text"].strip()
                    if text.startswith("```"):
                        text = re.sub(r"^```\w*\n?", "", text)
                        text = re.sub(r"\n?```$", "", text)
                    ai_insights = json.loads(text)
            except Exception:
                pass

    posting_times = {
        "instagram": ["9:00 AM", "12:00 PM", "5:00 PM", "7:00 PM"],
        "youtube": ["2:00 PM", "5:00 PM", "9:00 PM"],
        "tiktok": ["7:00 AM", "10:00 AM", "7:00 PM", "11:00 PM"],
        "facebook": ["9:00 AM", "1:00 PM", "4:00 PM"],
        "twitter": ["8:00 AM", "12:00 PM", "5:00 PM"],
        "linkedin": ["7:30 AM", "12:00 PM", "5:30 PM"],
    }

    return {
        "success": True, "niche": matched, "platform": platform,
        "trending_hashtags": trend_data.get("hashtags", []),
        "trending_topics": trend_data.get("topics", []),
        "content_formats": trend_data.get("formats", []),
        "viral_hooks": trend_data.get("hooks", []),
        "best_posting_times": posting_times.get(platform, ["12:00 PM", "6:00 PM"]),
        "ai_insights": ai_insights,
    }


@router.post("/api/xy-ai/content-plan")
async def xy_ai_content_plan(request: XYAIContentPlanRequest):
    """XY-AI: Generate a multi-day content calendar plan for a niche."""
    niche = (request.niche or "").strip()
    if not niche:
        raise HTTPException(status_code=400, detail="niche is required")

    platform = (request.platform or "instagram").strip().lower()
    days = max(1, min(request.days, 30))
    ppd = max(1, min(request.posts_per_day, 5))
    tone = (request.tone or "engaging").strip().lower()
    matched = _match_niche(niche)
    trend_data = _TREND_DB.get(matched, _TREND_DB["general"])

    model = (os.getenv("FYI_OLLAMA_MODEL") or "").strip()
    models = await _ollama_models()
    if not model and models:
        model = models[0]

    openai_key = _get_byok_key("openai")
    gemini_key = _get_byok_key("gemini")

    if model or openai_key or gemini_key:
        try:
            system = (
                "You are XY-AI, a content planning expert. "
                f"Create a {days}-day content plan ({ppd} post(s)/day) for {platform}. "
                "Return a JSON array where each item has: day (int), posts (array of {{title, caption, hashtags (array), content_type, best_time}}). "
                "Return ONLY valid JSON."
            )
            user_prompt = f"Niche: {niche}. Tone: {tone}. Platform: {platform}."

            raw = None
            used_mode = None
            if model:
                raw = await _ollama_generate(prompt=user_prompt, model=model, system=system, timeout_s=40.0)
                used_mode = "ollama"
            elif openai_key:
                async with httpx.AsyncClient(timeout=40.0) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/chat/completions",
                        headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                        json={"model": "gpt-4o-mini", "messages": [{"role": "system", "content": system}, {"role": "user", "content": user_prompt}], "temperature": 0.8},
                    )
                    resp.raise_for_status()
                    raw = resp.json()["choices"][0]["message"]["content"]
                    used_mode = "openai"
            elif gemini_key:
                async with httpx.AsyncClient(timeout=40.0) as client:
                    resp = await client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}",
                        json={"contents": [{"parts": [{"text": f"{system}\n\n{user_prompt}"}]}]},
                    )
                    resp.raise_for_status()
                    raw = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
                    used_mode = "gemini"

            if raw:
                raw = raw.strip()
                if raw.startswith("```"):
                    raw = re.sub(r"^```\w*\n?", "", raw)
                    raw = re.sub(r"\n?```$", "", raw)
                plan = json.loads(raw)
                return {"success": True, "mode": f"xy-ai-{used_mode}", "plan": plan, "niche": matched}
        except Exception:
            pass

    # Deterministic fallback
    topics = trend_data.get("topics", [f"{niche} content idea"])
    formats = trend_data.get("formats", ["Standard post"])
    hooks = trend_data.get("hooks", [f"Check this out: {niche}"])
    tags = trend_data.get("hashtags", [f"#{niche.replace(' ', '')}"])

    posting_times = {
        "instagram": ["9:00 AM", "12:00 PM", "5:00 PM"],
        "youtube": ["2:00 PM", "5:00 PM"],
        "tiktok": ["7:00 AM", "7:00 PM", "10:00 PM"],
    }
    times = posting_times.get(platform, ["12:00 PM"])

    plan = []
    for d in range(1, days + 1):
        day_posts = []
        for p in range(ppd):
            idx = (d * ppd + p) % len(topics)
            day_posts.append({
                "title": topics[idx],
                "caption": f"{hooks[idx % len(hooks)]}\n\n{topics[idx]}",
                "hashtags": random.sample(tags, min(5, len(tags))),
                "content_type": formats[idx % len(formats)],
                "best_time": times[p % len(times)],
            })
        plan.append({"day": d, "posts": day_posts})

    return {"success": True, "mode": "xy-ai-smart-fallback", "plan": plan, "niche": matched}


@router.get("/api/xy-ai/chat/models")
async def xy_ai_chat_models():
    """Return the list of available chat models based on configured API keys."""
    available_models = [{"id": "auto", "name": "Auto (Best Available)", "provider": "auto"}]

    ollama_model = (os.getenv("FYI_OLLAMA_MODEL") or "").strip()
    ollama_list = await _ollama_models()
    if ollama_model or ollama_list:
        for m in (ollama_list or [ollama_model]):
            if m:
                available_models.append({"id": m, "name": m, "provider": "ollama"})

    if _get_byok_key("openai"):
        available_models.extend([
            {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "provider": "openai"},
            {"id": "gpt-4o", "name": "GPT-4o", "provider": "openai"},
            {"id": "gpt-4.1-mini", "name": "GPT-4.1 Mini", "provider": "openai"},
            {"id": "gpt-4.1", "name": "GPT-4.1", "provider": "openai"},
            {"id": "o4-mini", "name": "o4-mini (Reasoning)", "provider": "openai"},
        ])

    if _get_byok_key("gemini"):
        available_models.extend([
            {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "provider": "gemini"},
            {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "provider": "gemini"},
            {"id": "gemini-2.0-flash", "name": "Gemini 2.0 Flash", "provider": "gemini"},
        ])

    if _get_byok_key("anthropic"):
        available_models.extend([
            {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4", "provider": "anthropic"},
            {"id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku", "provider": "anthropic"},
        ])

    if _get_byok_key("xai"):
        available_models.extend([
            {"id": "grok-3", "name": "Grok 3", "provider": "xai"},
            {"id": "grok-3-mini", "name": "Grok 3 Mini", "provider": "xai"},
        ])

    return {"success": True, "models": available_models}


@router.post("/api/xy-ai/chat")
async def xy_ai_chat(request: XYAIChatRequest):
    """XY-AI: Chat with FYIXT's AI assistant."""
    message = (request.message or "").strip()
    if not message:
        raise HTTPException(status_code=400, detail="message is required")

    context_hint = (request.context or "").strip()
    history = request.history or []
    preferred = (request.preferred_model or "auto").strip().lower()

    system_prompt = (
        "You are XY-AI, FYIXT's intelligent assistant specializing in social media, "
        "content creation, digital marketing, branding, and growth strategy. "
        "You have real-time internet access via Google Search grounding — use it to provide "
        "current news, live trends, recent viral content, and up-to-date information. "
        "You are friendly, concise, and actionable. Use emojis sparingly. "
        "When asked about trends, give specific platform-tailored advice with real data. "
        "If the user asks something unrelated, answer helpfully but steer back to content/marketing."
    )
    if context_hint:
        system_prompt += f"\nAdditional context: {context_hint}"

    conv_history = ""
    for msg in history[-20:]:
        role = msg.get("role", "user")
        content = msg.get("content", "")
        conv_history += f"\n{'User' if role == 'user' else 'XY-AI'}: {content}"
    conv_history += f"\nUser: {message}\nXY-AI:"

    ollama_model = (os.getenv("FYI_OLLAMA_MODEL") or "").strip()
    ollama_models_list = await _ollama_models()
    if not ollama_model and ollama_models_list:
        ollama_model = ollama_models_list[0]

    openai_key = _get_byok_key("openai")
    gemini_key = _get_byok_key("gemini")
    anthropic_key = _get_byok_key("anthropic")
    xai_key = _get_byok_key("xai")

    async def _chat_openai(oai_model: str = "gpt-4o-mini"):
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-20:]:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": message})
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={"Authorization": f"Bearer {openai_key}", "Content-Type": "application/json"},
                json={"model": oai_model, "messages": messages, "temperature": 0.8},
            )
            resp.raise_for_status()
            data = resp.json()
            reply = data["choices"][0]["message"]["content"].strip()
            return {"success": True, "mode": "xy-ai-openai", "model": oai_model, "reply": reply}

    async def _chat_gemini(gm: str = "gemini-2.5-flash"):
        contents = []
        for msg in history[-20:]:
            role = "user" if msg.get("role") == "user" else "model"
            contents.append({"role": role, "parts": [{"text": msg.get("content", "")}]})
        contents.append({"role": "user", "parts": [{"text": message}]})
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{gm}:generateContent?key={gemini_key}",
                json={
                    "systemInstruction": {"parts": [{"text": system_prompt}]},
                    "contents": contents,
                    "tools": [{"google_search": {}}],
                },
            )
            if resp.status_code == 429:
                raise Exception(f"Rate limited on {gm}")
            resp.raise_for_status()
            data = resp.json()
            parts = data["candidates"][0]["content"]["parts"]
            reply_parts = [p["text"] for p in parts if "text" in p]
            reply = "\n".join(reply_parts).strip()
            return {"success": True, "mode": "xy-ai-gemini", "model": gm, "reply": reply}

    async def _chat_anthropic(claude_model: str = "claude-sonnet-4-20250514"):
        messages = []
        for msg in history[-20:]:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": message})
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": anthropic_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"},
                json={"model": claude_model, "max_tokens": 1024, "system": system_prompt, "messages": messages},
            )
            resp.raise_for_status()
            data = resp.json()
            reply = data["content"][0]["text"].strip()
            return {"success": True, "mode": "xy-ai-anthropic", "model": claude_model, "reply": reply}

    async def _chat_xai(grok_model: str = "grok-3-mini"):
        messages = [{"role": "system", "content": system_prompt}]
        for msg in history[-20:]:
            messages.append({"role": msg.get("role", "user"), "content": msg.get("content", "")})
        messages.append({"role": "user", "content": message})
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                "https://api.x.ai/v1/chat/completions",
                headers={"Authorization": f"Bearer {xai_key}", "Content-Type": "application/json"},
                json={"model": grok_model, "messages": messages, "temperature": 0.8},
            )
            resp.raise_for_status()
            data = resp.json()
            reply = data["choices"][0]["message"]["content"].strip()
            return {"success": True, "mode": "xy-ai-xai", "model": grok_model, "reply": reply}

    failed_provider = None
    fallback_reason = ""
    if preferred and preferred != "auto":
        try:
            if preferred.startswith("gpt-") or preferred.startswith("o"):
                failed_provider = "openai"
                if openai_key:
                    return await _chat_openai(preferred)
                raise Exception("No OpenAI API key configured")
            elif preferred.startswith("gemini-"):
                failed_provider = "gemini"
                if gemini_key:
                    return await _chat_gemini(preferred)
                raise Exception("No Gemini API key configured")
            elif preferred.startswith("claude-"):
                failed_provider = "anthropic"
                if anthropic_key:
                    return await _chat_anthropic(preferred)
                raise Exception("No Anthropic API key configured")
            elif preferred.startswith("grok-"):
                failed_provider = "xai"
                if xai_key:
                    return await _chat_xai(preferred)
                raise Exception("No xAI API key configured")
            elif ollama_model or preferred in (ollama_models_list or []):
                failed_provider = "ollama"
                target = preferred if preferred in (ollama_models_list or []) else ollama_model
                raw = await _ollama_generate(prompt=conv_history, model=target, system=system_prompt, timeout_s=45.0)
                return {"success": True, "mode": "xy-ai-ollama", "model": target, "reply": raw.strip()}
        except Exception as e:
            fallback_reason = str(e)
            print(f"[XY-AI chat] Preferred model '{preferred}' failed: {e}, falling back to auto...")

    def _with_fallback(result: dict) -> dict:
        if failed_provider and preferred != "auto":
            result["fallback"] = True
            result["requested_model"] = preferred
            result["fallback_reason"] = fallback_reason or "Unknown error"
        return result

    # Auto cascade
    if ollama_model and failed_provider != "ollama":
        try:
            raw = await _ollama_generate(prompt=conv_history, model=ollama_model, system=system_prompt, timeout_s=45.0)
            return _with_fallback({"success": True, "mode": "xy-ai-ollama", "model": ollama_model, "reply": raw.strip()})
        except Exception as e:
            print(f"[XY-AI chat] Ollama failed: {e}")

    if openai_key and failed_provider != "openai":
        try:
            return _with_fallback(await _chat_openai("gpt-4o-mini"))
        except Exception as e:
            print(f"[XY-AI chat] OpenAI failed: {e}")

    if gemini_key:
        gemini_models_list = ["gemini-2.5-flash", "gemini-2.0-flash", "gemini-2.0-flash-lite"]
        for gm in gemini_models_list:
            try:
                result = await _chat_gemini(gm)
                return _with_fallback(result)
            except Exception as e:
                print(f"[XY-AI chat] Gemini {gm} failed: {e}")
                await asyncio.sleep(1)
                continue

    if anthropic_key and failed_provider != "anthropic":
        try:
            return _with_fallback(await _chat_anthropic())
        except Exception as e:
            print(f"[XY-AI chat] Anthropic failed: {e}")

    if xai_key and failed_provider != "xai":
        try:
            return _with_fallback(await _chat_xai("grok-3-mini"))
        except Exception as e:
            print(f"[XY-AI chat] xAI Grok failed: {e}")

    # Smart offline fallback
    lower = message.lower()
    if any(w in lower for w in ["hashtag", "tag", "#"]):
        matched = _match_niche(message)
        tags = _TREND_DB.get(matched, _TREND_DB["general"])["hashtags"][:8]
        reply = f"Here are some trending hashtags for {matched}: {', '.join(tags)}\n\nTip: Mix 3-5 popular tags with 2-3 niche-specific ones for best reach!"
    elif any(w in lower for w in ["trend", "trending", "viral", "popular"]):
        matched = _match_niche(message)
        info = _TREND_DB.get(matched, _TREND_DB["general"])
        topics = info["topics"][:4]
        reply = f"Trending in {matched}:\n" + "\n".join(f"  • {t}" for t in topics) + "\n\nWant me to create content prompts for any of these?"
    elif any(w in lower for w in ["best time", "when to post", "schedule", "posting time"]):
        reply = "Best posting times vary by platform:\n  • Instagram: 11am-1pm & 7pm-9pm\n  • TikTok: 7am-9am & 7pm-11pm\n  • YouTube: 2pm-4pm (Thu-Sat)\n  • Twitter/X: 8am-10am & 6pm-9pm\n  • LinkedIn: 7am-8am & 5pm-6pm (Tue-Thu)\n\nAlways check your own analytics for your specific audience!"
    elif any(w in lower for w in ["caption", "write", "copy", "text"]):
        reply = "Here's a caption formula that works:\n\n🎯 Hook (stop the scroll)\n📖 Story or value (why should they care?)\n💡 CTA (tell them what to do)\n#️⃣ Hashtags (5-10 relevant ones)\n\nWant me to generate specific captions? Head to the Prompt Generator tab!"
    elif any(w in lower for w in ["grow", "growth", "followers", "engagement"]):
        reply = "Top growth strategies for 2026:\n  1. Post consistently (4-7x/week)\n  2. Use trending audio & formats\n  3. Engage in the first 30 min after posting\n  4. Collaborate with creators in your niche\n  5. Repurpose content across platforms\n  6. Optimize your bio & profile\n\nWhich platform are you focusing on?"
    elif any(w in lower for w in ["hello", "hi", "hey", "sup", "yo"]):
        reply = "Hey! 👋 I'm XY-AI, your content & marketing assistant. I can help with:\n  • Content ideas & captions\n  • Trending hashtags & topics\n  • Posting strategies\n  • Platform-specific tips\n  • Growth advice\n\nWhat would you like help with?"
    else:
        reply = f"Great question! While I work best with an AI provider connected (check Settings → AI Services), here's what I can help with offline:\n  • Trending hashtags & topics (try asking about trends)\n  • Best posting times\n  • Caption formulas\n  • Growth tips\n\nConnect an AI key like Gemini or OpenAI for full conversational answers!"

    return _with_fallback({"success": True, "mode": "xy-ai-smart-fallback", "model": None, "reply": reply})


@router.get("/api/xy-ai/niches")
async def xy_ai_list_niches():
    """XY-AI: List available trend niches."""
    return {
        "success": True,
        "niches": list(_TREND_DB.keys()),
        "description": "Pass any of these to the niche parameter, or describe your own — XY-AI will fuzzy-match it.",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# AI Image Generation
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/ai/image")
async def ai_generate_image(request: AIImageRequest):
    """Generate images using BYOK providers."""
    prompt = (request.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    provider = (request.provider or "openai").strip().lower()
    api_key = _get_byok_key(provider)
    if not api_key:
        raise HTTPException(status_code=400, detail=f"No API key configured for {provider}. Add it via /api/byok/keys")

    size = request.size or "1024x1024"
    n = max(1, min(int(request.n or 1), 4))

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            if provider == "openai":
                resp = await client.post(
                    "https://api.openai.com/v1/images/generations",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"model": "dall-e-3", "prompt": prompt, "size": size, "n": n, "quality": "standard"},
                )
                if resp.status_code >= 400:
                    raise HTTPException(status_code=resp.status_code, detail=resp.text)
                data = resp.json()
                images = [{"url": img.get("url"), "revised_prompt": img.get("revised_prompt")} for img in data.get("data", [])]
                _add_usage("image_generation", n * 10, {"provider": provider, "prompt": prompt[:100]})
                return {"success": True, "provider": provider, "images": images}

            elif provider == "stability":
                resp = await client.post(
                    "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"text_prompts": [{"text": prompt, "weight": 1}], "cfg_scale": 7, "height": 1024, "width": 1024, "samples": n, "steps": 30},
                )
                if resp.status_code >= 400:
                    raise HTTPException(status_code=resp.status_code, detail=resp.text)
                data = resp.json()
                images = [{"base64": art.get("base64"), "seed": art.get("seed")} for art in data.get("artifacts", [])]
                _add_usage("image_generation", n * 8, {"provider": provider, "prompt": prompt[:100]})
                return {"success": True, "provider": provider, "images": images}

            elif provider == "replicate":
                resp = await client.post(
                    "https://api.replicate.com/v1/predictions",
                    headers={"Authorization": f"Token {api_key}"},
                    json={"version": "black-forest-labs/flux-schnell", "input": {"prompt": prompt, "num_outputs": n}},
                )
                if resp.status_code >= 400:
                    raise HTTPException(status_code=resp.status_code, detail=resp.text)
                prediction = resp.json()
                pred_id = prediction.get("id")
                for _ in range(60):
                    status_resp = await client.get(
                        f"https://api.replicate.com/v1/predictions/{pred_id}",
                        headers={"Authorization": f"Token {api_key}"},
                    )
                    status_data = status_resp.json()
                    if status_data.get("status") == "succeeded":
                        images = [{"url": u} for u in (status_data.get("output") or [])]
                        _add_usage("image_generation", n * 5, {"provider": provider, "prompt": prompt[:100]})
                        return {"success": True, "provider": provider, "images": images}
                    if status_data.get("status") == "failed":
                        raise HTTPException(status_code=500, detail=status_data.get("error", "Generation failed"))
                    await asyncio.sleep(2)
                raise HTTPException(status_code=504, detail="Image generation timed out")

            else:
                raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ═══════════════════════════════════════════════════════════════════════════════
# AI Video Generation
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/ai/video")
async def ai_generate_video(request: AIVideoRequest):
    """Generate videos using BYOK providers (async - returns job_id to poll)."""
    prompt = (request.prompt or "").strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="prompt is required")

    provider = (request.provider or "runway").strip().lower()
    if provider == "veo":
        api_key = _get_byok_key("gemini")
    elif provider == "grok_imagine":
        api_key = _get_byok_key("xai")
    else:
        api_key = _get_byok_key(provider)
    if not api_key:
        key_name = "gemini" if provider == "veo" else ("xai" if provider == "grok_imagine" else provider)
        raise HTTPException(status_code=400, detail=f"No API key configured for {key_name}. Add it in Settings > AI Services.")

    job_id = f"aivideo_{uuid4().hex[:12]}"
    job_file = DATA_DIR / "ai_jobs" / f"{job_id}.json"
    job_file.parent.mkdir(parents=True, exist_ok=True)

    job_data = {
        "id": job_id, "provider": provider, "prompt": prompt,
        "status": "pending", "created_at": datetime.now().isoformat(),
        "result": None, "error": None,
    }
    job_file.write_text(json.dumps(job_data, indent=2), encoding="utf-8")

    asyncio.create_task(_run_video_generation(job_id, provider, api_key, prompt, request.image_url, request.duration, request.aspect_ratio))

    _add_usage("video_generation", 50, {"provider": provider, "prompt": prompt[:100]})
    return {"success": True, "job_id": job_id, "status": "pending", "poll_url": f"/api/ai/video/status/{job_id}"}


async def _run_video_generation(job_id: str, provider: str, api_key: str, prompt: str, image_url: str | None, duration: int, aspect_ratio: str = "16:9"):
    """Background task for video generation."""
    job_file = DATA_DIR / "ai_jobs" / f"{job_id}.json"

    def _update_job(status: str, result: Any = None, error: str = None):
        data = json.loads(job_file.read_text())
        data["status"] = status
        data["result"] = result
        data["error"] = error
        data["updated_at"] = datetime.now().isoformat()
        job_file.write_text(json.dumps(data, indent=2))

    try:
        async with httpx.AsyncClient(timeout=300) as client:
            if provider == "runway":
                resp = await client.post(
                    "https://api.runwayml.com/v1/generations",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={"prompt": prompt, "seconds": duration, "seed": random.randint(1, 999999)},
                )
                if resp.status_code >= 400:
                    _update_job("failed", error=resp.text)
                    return
                gen_data = resp.json()
                gen_id = gen_data.get("id")
                for _ in range(120):
                    status_resp = await client.get(f"https://api.runwayml.com/v1/generations/{gen_id}", headers={"Authorization": f"Bearer {api_key}"})
                    status_data = status_resp.json()
                    if status_data.get("status") == "succeeded":
                        _update_job("completed", result={"url": status_data.get("output", [{}])[0].get("url")})
                        return
                    if status_data.get("status") == "failed":
                        _update_job("failed", error=status_data.get("error", "Generation failed"))
                        return
                    await asyncio.sleep(5)
                _update_job("failed", error="Generation timed out")

            elif provider == "replicate":
                resp = await client.post(
                    "https://api.replicate.com/v1/predictions",
                    headers={"Authorization": f"Token {api_key}"},
                    json={"version": "kuaishou/kling-v1", "input": {"prompt": prompt, "duration": duration}},
                )
                if resp.status_code >= 400:
                    _update_job("failed", error=resp.text)
                    return
                pred = resp.json()
                pred_id = pred.get("id")
                for _ in range(120):
                    status_resp = await client.get(f"https://api.replicate.com/v1/predictions/{pred_id}", headers={"Authorization": f"Token {api_key}"})
                    status_data = status_resp.json()
                    if status_data.get("status") == "succeeded":
                        output = status_data.get("output")
                        url = output[0] if isinstance(output, list) else output
                        _update_job("completed", result={"url": url})
                        return
                    if status_data.get("status") == "failed":
                        _update_job("failed", error=status_data.get("error", "Generation failed"))
                        return
                    await asyncio.sleep(5)
                _update_job("failed", error="Generation timed out")

            elif provider == "veo":
                veo_duration = max(5, min(8, duration))
                ar_map = {"16:9": "16:9", "9:16": "9:16", "1:1": "1:1"}
                veo_ar = ar_map.get(aspect_ratio, "16:9")
                generate_payload = {"instances": [{"prompt": prompt}], "parameters": {"aspectRatio": veo_ar, "durationSeconds": veo_duration, "sampleCount": 1}}
                if image_url:
                    generate_payload["instances"][0]["image"] = {"bytesBase64Encoded": image_url} if not image_url.startswith("http") else {"gcsUri": image_url}

                _update_job("processing")

                resp = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/veo-2.0-generate-001:predictLongRunning?key={api_key}",
                    json=generate_payload, headers={"Content-Type": "application/json"},
                )
                if resp.status_code >= 400:
                    _update_job("failed", error=f"Veo API error ({resp.status_code}): {resp.text[:500]}")
                    return

                op_data = resp.json()
                op_name = op_data.get("name")
                if not op_name:
                    _update_job("failed", error=f"Veo returned no operation name: {json.dumps(op_data)[:500]}")
                    return

                for attempt in range(120):
                    await asyncio.sleep(5)
                    poll_resp = await client.post(
                        f"https://generativelanguage.googleapis.com/v1beta/{op_name}:fetchPredictOperation?key={api_key}",
                        headers={"Content-Type": "application/json"},
                    )
                    if poll_resp.status_code >= 400:
                        continue
                    poll_data = poll_resp.json()
                    done = poll_data.get("done", False)
                    if done:
                        if "error" in poll_data:
                            _update_job("failed", error=poll_data["error"].get("message", "Unknown Veo error"))
                            return
                        response_data = poll_data.get("response", {})
                        videos = response_data.get("generateVideoResponse", {}).get("generatedSamples", [])
                        if not videos:
                            videos = response_data.get("predictions", [])
                        if videos:
                            video_info = videos[0]
                            if "video" in video_info and "uri" in video_info["video"]:
                                _update_job("completed", result={"url": video_info["video"]["uri"], "provider": "veo"})
                            elif "video" in video_info and "bytesBase64Encoded" in video_info["video"]:
                                import base64
                                video_bytes = base64.b64decode(video_info["video"]["bytesBase64Encoded"])
                                video_path = DATA_DIR / "ai_videos" / f"{job_id}.mp4"
                                video_path.parent.mkdir(parents=True, exist_ok=True)
                                video_path.write_bytes(video_bytes)
                                _update_job("completed", result={"url": f"/api/ai/video/file/{job_id}.mp4", "provider": "veo", "local": True})
                            else:
                                _update_job("completed", result={"raw": str(video_info)[:1000], "provider": "veo"})
                        else:
                            _update_job("failed", error="Veo completed but no video found in response")
                        return
                    metadata = poll_data.get("metadata", {})
                    progress = metadata.get("percentComplete", 0)
                    _update_job("processing", result={"progress": progress})

                _update_job("failed", error="Veo generation timed out after 10 minutes")

            elif provider == "grok_imagine":
                _update_job("processing")
                gen_payload = {"prompt": prompt, "model": "grok-imagine-video", "duration": max(5, min(10, duration))}
                if image_url:
                    gen_payload["image"] = {"url": image_url}

                resp = await client.post(
                    "https://api.x.ai/v1/videos/generations",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json=gen_payload,
                )
                if resp.status_code >= 400:
                    _update_job("failed", error=f"Grok Imagine API error ({resp.status_code}): {resp.text[:500]}")
                    return

                req_data = resp.json()
                request_id = req_data.get("request_id")
                if not request_id:
                    _update_job("failed", error=f"Grok Imagine returned no request_id: {json.dumps(req_data)[:500]}")
                    return

                for attempt in range(120):
                    await asyncio.sleep(5)
                    poll_resp = await client.get(f"https://api.x.ai/v1/videos/{request_id}", headers={"Authorization": f"Bearer {api_key}"})
                    if poll_resp.status_code == 202:
                        _update_job("processing", result={"progress": min(95, attempt * 2)})
                        continue
                    if poll_resp.status_code >= 400:
                        continue
                    poll_data = poll_resp.json()
                    video_info = poll_data.get("video", {})
                    video_url = video_info.get("url")
                    if video_url:
                        _update_job("completed", result={"url": video_url, "provider": "grok_imagine"})
                        return
                    else:
                        _update_job("failed", error=f"Grok Imagine completed but no video URL: {json.dumps(poll_data)[:500]}")
                        return
                _update_job("failed", error="Grok Imagine generation timed out after 10 minutes")

            else:
                _update_job("failed", error=f"Unsupported provider: {provider}")

    except Exception as e:
        _update_job("failed", error=str(e))


@router.get("/api/ai/video/file/{filename}")
async def serve_ai_video_file(filename: str):
    """Serve locally saved AI-generated video files."""
    from fastapi.responses import FileResponse
    # Sanitize filename to prevent path traversal
    filename = filename.replace("..", "").replace("/", "").replace("\\", "")
    if not filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    video_path = (DATA_DIR / "ai_videos" / filename).resolve()
    videos_dir = (DATA_DIR / "ai_videos").resolve()
    if not video_path.is_relative_to(videos_dir) or not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    return FileResponse(str(video_path), media_type="video/mp4")


@router.get("/api/ai/video/status/{job_id}")
async def get_video_generation_status(job_id: str):
    """Check status of video generation job."""
    # Sanitize job_id to prevent path traversal
    job_id = job_id.replace("..", "").replace("/", "").replace("\\", "")
    if not job_id:
        raise HTTPException(status_code=400, detail="Invalid job_id")
    job_file = (DATA_DIR / "ai_jobs" / f"{job_id}.json").resolve()
    jobs_dir = (DATA_DIR / "ai_jobs").resolve()
    if not job_file.is_relative_to(jobs_dir) or not job_file.exists():
        raise HTTPException(status_code=404, detail="Job not found")
    data = json.loads(job_file.read_text())
    return {"success": True, **data}


# ═══════════════════════════════════════════════════════════════════════════════
# AI Voice / TTS
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/api/ai/voice")
async def ai_generate_voice(request: AIVoiceRequest):
    """Generate voiceover audio using TTS providers."""
    text = (request.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    if len(text) > 5000:
        raise HTTPException(status_code=400, detail="text exceeds 5000 character limit")

    provider = (request.provider or "elevenlabs").strip().lower()
    api_key = _get_byok_key(provider)
    if not api_key:
        raise HTTPException(status_code=400, detail=f"No API key configured for {provider}. Add it via /api/byok/keys")

    voice_id = request.voice_id or ("Rachel" if provider == "elevenlabs" else "alloy")
    out_id = f"voice_{uuid4().hex[:12]}"
    out_path = UPLOADS_DIR / f"{out_id}.mp3"

    try:
        async with httpx.AsyncClient(timeout=120) as client:
            if provider == "elevenlabs":
                el_voice_id = voice_id if len(voice_id) > 10 else "21m00Tcm4TlvDq8ikWAM"
                resp = await client.post(
                    f"https://api.elevenlabs.io/v1/text-to-speech/{el_voice_id}",
                    headers={"xi-api-key": api_key, "Content-Type": "application/json"},
                    json={"text": text, "model_id": "eleven_multilingual_v2", "voice_settings": {"stability": 0.5, "similarity_boost": 0.75}},
                )
                if resp.status_code >= 400:
                    raise HTTPException(status_code=resp.status_code, detail=resp.text)
                out_path.write_bytes(resp.content)

            elif provider == "openai":
                resp = await client.post(
                    "https://api.openai.com/v1/audio/speech",
                    headers={"Authorization": f"Bearer {api_key}"},
                    json={"model": "tts-1", "input": text, "voice": voice_id if voice_id in ["alloy", "echo", "fable", "onyx", "nova", "shimmer"] else "alloy"},
                )
                if resp.status_code >= 400:
                    raise HTTPException(status_code=resp.status_code, detail=resp.text)
                out_path.write_bytes(resp.content)

            else:
                raise HTTPException(status_code=400, detail=f"Unsupported provider: {provider}")

        chars = len(text)
        credits = max(1, chars // 100)
        _add_usage("voice_generation", credits, {"provider": provider, "chars": chars})

        return {
            "success": True, "provider": provider,
            "file_id": f"{out_id}.mp3",
            "url": f"/uploads/{out_id}.mp3",
            "duration_estimate": len(text) / 15,
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/ai/voices")
async def list_available_voices():
    """List available voices for TTS providers."""
    voices = {
        "elevenlabs": [
            {"id": "21m00Tcm4TlvDq8ikWAM", "name": "Rachel", "gender": "female"},
            {"id": "AZnzlk1XvdvUeBnXmlld", "name": "Domi", "gender": "female"},
            {"id": "EXAVITQu4vr4xnSDxMaL", "name": "Bella", "gender": "female"},
            {"id": "ErXwobaYiN019PkySvjV", "name": "Antoni", "gender": "male"},
            {"id": "VR6AewLTigWG4xSOukaG", "name": "Arnold", "gender": "male"},
            {"id": "pNInz6obpgDQGcFmaJgB", "name": "Adam", "gender": "male"},
            {"id": "yoZ06aMxZJJ28mfd3POQ", "name": "Sam", "gender": "male"},
        ],
        "openai": [
            {"id": "alloy", "name": "Alloy", "gender": "neutral"},
            {"id": "echo", "name": "Echo", "gender": "male"},
            {"id": "fable", "name": "Fable", "gender": "female"},
            {"id": "onyx", "name": "Onyx", "gender": "male"},
            {"id": "nova", "name": "Nova", "gender": "female"},
            {"id": "shimmer", "name": "Shimmer", "gender": "female"},
        ],
    }
    return {"success": True, "voices": voices}


# ═══════════════════════════════════════════════════════════════════════════════
# AI Translation
# ═══════════════════════════════════════════════════════════════════════════════

SUPPORTED_LANGUAGES = {
    "en": "English", "es": "Spanish", "fr": "French", "de": "German", "it": "Italian",
    "pt": "Portuguese", "nl": "Dutch", "pl": "Polish", "ru": "Russian", "ja": "Japanese",
    "ko": "Korean", "zh": "Chinese", "ar": "Arabic", "hi": "Hindi", "tr": "Turkish",
    "vi": "Vietnamese", "th": "Thai", "id": "Indonesian", "ms": "Malay", "fil": "Filipino",
    "sv": "Swedish", "da": "Danish", "no": "Norwegian", "fi": "Finnish", "cs": "Czech",
    "el": "Greek", "he": "Hebrew", "hu": "Hungarian", "ro": "Romanian", "uk": "Ukrainian",
    "bg": "Bulgarian", "hr": "Croatian", "sk": "Slovak", "sl": "Slovenian", "et": "Estonian",
    "lv": "Latvian", "lt": "Lithuanian", "sr": "Serbian", "mk": "Macedonian", "sq": "Albanian",
    "bn": "Bengali", "ta": "Tamil", "te": "Telugu", "mr": "Marathi", "gu": "Gujarati",
    "kn": "Kannada", "ml": "Malayalam", "pa": "Punjabi", "ur": "Urdu", "fa": "Persian",
    "sw": "Swahili", "af": "Afrikaans", "zu": "Zulu", "xh": "Xhosa", "am": "Amharic",
    "ne": "Nepali", "si": "Sinhala", "my": "Myanmar", "km": "Khmer", "lo": "Lao",
}


@router.get("/api/languages")
async def list_supported_languages():
    """List all supported languages (58+)."""
    return {"success": True, "languages": SUPPORTED_LANGUAGES, "count": len(SUPPORTED_LANGUAGES)}


@router.post("/api/ai/translate")
async def ai_translate(request: TranslateRequest):
    """Translate text to target language."""
    text = (request.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    target = request.target_language or "en"
    if target not in SUPPORTED_LANGUAGES:
        raise HTTPException(status_code=400, detail=f"Unsupported language: {target}")

    target_name = SUPPORTED_LANGUAGES[target]

    model = (os.getenv("FYI_OLLAMA_MODEL") or "").strip()
    models = await _ollama_models()
    if not model and models:
        model = models[0]

    prompt = f"Translate the following text to {target_name}. Output only the translation, nothing else.\n\nText:\n{text}"
    system = "You are a professional translator. Output only the translated text."

    try:
        if model:
            result = await _ollama_generate(prompt=prompt, model=model, system=system, timeout_s=30.0)
            return {"success": True, "translated": result.strip(), "target_language": target, "mode": "ollama"}

        openai_key = _get_byok_key("openai")
        if openai_key:
            async with httpx.AsyncClient(timeout=60) as client:
                resp = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={"Authorization": f"Bearer {openai_key}"},
                    json={
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": system},
                            {"role": "user", "content": prompt},
                        ],
                        "max_tokens": 2000,
                    },
                )
                if resp.status_code == 200:
                    data = resp.json()
                    result = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                    _add_usage("translation", 1, {"target": target, "chars": len(text)})
                    return {"success": True, "translated": result.strip(), "target_language": target, "mode": "openai"}

        gemini_key = _get_byok_key("gemini")
        if gemini_key:
            async with httpx.AsyncClient(timeout=60) as client:
                prompt_text = f"{system}\n\n{prompt}"
                resp = await client.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={gemini_key}",
                    json={"contents": [{"parts": [{"text": prompt_text}]}]},
                )
                if resp.status_code == 200:
                    data = resp.json()
                    result = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    _add_usage("translation", 1, {"target": target, "chars": len(text)})
                    return {"success": True, "translated": result, "target_language": target, "mode": "gemini"}

        raise HTTPException(status_code=501, detail="No AI provider available. Configure Ollama, OpenAI, or Gemini.")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
