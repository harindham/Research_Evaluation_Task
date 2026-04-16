#!/usr/bin/env python3
"""
Task 1: App Evaluation and Data Collection
Classifies apps from Google Play and App Store JSON files into a CSV with additional fields.
"""

import json
import csv
import re

# --- Known general-purpose LLM app identifiers ---
GENERAL_PURPOSE_IDS = {
    # Google Play appIds
    'com.openai.chatgpt', 'com.anthropic.claude', 'com.google.android.apps.bard',
    'ai.perplexity.app.android', 'com.deepseek.chat', 'ai.x.grok',
    'com.microsoft.copilot', 'com.alibaba.intl.android.apps.poseidon',
    'com.zhiliaoapp.musically.go',  # not AI
    # App Store appIds
    'com.openai.chat', 'com.anthropic.claudeapp', 'com.google.Bard',
    'ai.perplexity.app', 'com.deepseek.chat', 'ai.x.grok',
    'com.microsoft.copilot',
}

GENERAL_PURPOSE_KEYWORDS_TITLE = [
    'chatgpt', 'claude', 'gemini', 'grok', 'deepseek', 'perplexity', 'copilot',
    'meta ai', 'pi ai',
]

# Keywords strongly indicating companion/relational apps
COMPANION_KEYWORDS = [
    'ai boyfriend', 'ai girlfriend', 'virtual boyfriend', 'virtual girlfriend',
    'ai companion', 'ai friend', 'ai chat companion', 'roleplay',
    'ai lover', 'ai partner', 'ai soulmate', 'ai romance', 'fantasy boyfriend',
    'fantasy girlfriend', 'ai date', 'ai dating', 'romantic ai',
    'ai character', 'chat with characters', 'ai characters',
    'virtual companion', 'ai waifu', 'ai husband', 'ai wife',
    'emotional companion', 'ai relationship', 'ai gf', 'ai bf',
    'ai being', 'personal ai chat', 'anime character chat',
    'love chat', 'dream ai', 'ai love', 'character chat',
    'interactive stories', 'ai chat friend',
]

# Known companion app title substrings (manually verified)
KNOWN_COMPANION_TITLES = [
    'talkie', 'character.ai', 'character ai', 'replika', 'chai ',
    'crushon', 'candy.ai', 'kindroid', 'nomi', 'eva ai',
    'paradot', 'spicychat', 'janitor', 'myanima', 'anima',
    'deepspace', 'mechat', 'mystic messenger', 'simsimi',
    'babol', 'deeplove', 'wink ai', 'mana ', 'loveheart',
    'boyfriend plus', 'love simulator', 'situation boyfriend',
    'bimobimo', 'chara ', 'trend ai', 'ira ', 'soultalk',
    'polybuzz', 'friendx', 'iboy', 'dotdotdot', 'aiboy',
    'chai:', 'chai-', 'chai ai', 'yodayo', 'joyland',
    'kupid ai', 'muah ai', 'romantic ai', 'lovelink',
    'dream boyfriend', 'dream girlfriend', 'ai dungeon',
    'novel ai', 'novelai', 'sakura', 'soulgen',
    'priceless ai', 'unhinged ai', 'botify', 'charstar',
    'poly.ai', 'fantasyai', 'fantasy ai', 'dreampal',
    'intimate', 'sensual', 'flirtai', 'lovedriven',
    'spicy chat', 'spicychat', 'your lover', 'hailee',
    'girlfriend plus', 'waifuchat', 'waifu chat', 'siren ai',
    'blushed', 'yano ai', 'twink:', 'yern ', 'synthtalk',
    'tolan:', 'oto - ai voice companion', 'twineo',
    'ai avatar', 'candy ai', 'second me',
]

# Keywords indicating task-specific / other apps
TASK_SPECIFIC_KEYWORDS = [
    'homework', 'study companion', 'study helper', 'math helper', 'tutor',
    'language tutor', 'language learning', 'photo editor', 'image generator',
    'wallpaper', 'keyboard', 'translator', 'writing assistant',
    'code assistant', 'coding', 'fitness', 'meditation', 'therapy',
    'journal', 'diary', 'note', 'productivity', 'email',
    'music', 'video editor', 'camera', 'scanner', 'pdf',
    'recipe', 'cooking', 'weather', 'news', 'browser',
]

# Well-known companion platforms and their web info
KNOWN_PLATFORMS = {
    'character.ai': {'web_accessible': True, 'web_url': 'https://character.ai', 'login_required': True, 'login_methods': 'Google, Apple, Email', 'age_verification_required': True, 'age_verification_method': 'Self-declaration (date of birth)'},
    'chai': {'web_accessible': True, 'web_url': 'https://chai-research.com', 'login_required': True, 'login_methods': 'Google, Apple, Email', 'age_verification_required': False, 'age_verification_method': ''},
    'replika': {'web_accessible': True, 'web_url': 'https://replika.com', 'login_required': True, 'login_methods': 'Email/Password, Google, Apple, Facebook', 'age_verification_required': True, 'age_verification_method': 'Self-declaration (date of birth)'},
    'talkie': {'web_accessible': True, 'web_url': 'https://www.talkie-ai.com', 'login_required': True, 'login_methods': 'Google, Apple, Email', 'age_verification_required': True, 'age_verification_method': 'Self-declaration (date of birth)'},
    'janitor ai': {'web_accessible': True, 'web_url': 'https://janitorai.com', 'login_required': True, 'login_methods': 'Email/Password, Google', 'age_verification_required': True, 'age_verification_method': 'Self-declaration (18+ confirmation)'},
    'crushon.ai': {'web_accessible': True, 'web_url': 'https://crushon.ai', 'login_required': True, 'login_methods': 'Google, Email, Discord', 'age_verification_required': True, 'age_verification_method': 'Self-declaration (18+ confirmation)'},
    'candy.ai': {'web_accessible': True, 'web_url': 'https://candy.ai', 'login_required': True, 'login_methods': 'Email/Password, Google', 'age_verification_required': True, 'age_verification_method': 'Self-declaration (18+ confirmation)'},
    'kindroid': {'web_accessible': True, 'web_url': 'https://kindroid.ai', 'login_required': True, 'login_methods': 'Google, Email/Password', 'age_verification_required': True, 'age_verification_method': 'Self-declaration (18+ confirmation)'},
    'nomi.ai': {'web_accessible': True, 'web_url': 'https://nomi.ai', 'login_required': True, 'login_methods': 'Email/Password, Google', 'age_verification_required': False, 'age_verification_method': ''},
    'eva ai': {'web_accessible': False, 'web_url': '', 'login_required': True, 'login_methods': 'Email/Password, Google, Apple', 'age_verification_required': True, 'age_verification_method': 'Self-declaration (date of birth)'},
    'chai ai': {'web_accessible': True, 'web_url': 'https://www.chai-research.com/chat', 'login_required': True, 'login_methods': 'Google, Apple', 'age_verification_required': False, 'age_verification_method': ''},
    'myanima': {'web_accessible': True, 'web_url': 'https://myanima.ai', 'login_required': True, 'login_methods': 'Email/Password, Google, Apple', 'age_verification_required': False, 'age_verification_method': ''},
    'paradot': {'web_accessible': True, 'web_url': 'https://www.paradot.ai', 'login_required': True, 'login_methods': 'Email/Password, Google, Apple', 'age_verification_required': True, 'age_verification_method': 'Self-declaration (date of birth)'},
    'poly.ai': {'web_accessible': True, 'web_url': 'https://poly.ai', 'login_required': True, 'login_methods': 'Google, Apple, Email', 'age_verification_required': False, 'age_verification_method': ''},
    'spicychat': {'web_accessible': True, 'web_url': 'https://spicychat.ai', 'login_required': True, 'login_methods': 'Google, Email, Discord', 'age_verification_required': True, 'age_verification_method': 'Self-declaration (18+ confirmation)'},
    'poe': {'web_accessible': True, 'web_url': 'https://poe.com', 'login_required': True, 'login_methods': 'Google, Apple, Email/Password', 'age_verification_required': False, 'age_verification_method': ''},
}


def classify_app_type(title, description, app_id, genre=''):
    """Classify app as companion, general_purpose, mixed, or other."""
    title_lower = title.lower()
    desc_lower = description.lower()
    app_id_lower = (app_id or '').lower()

    # Check general-purpose LLMs first
    if app_id_lower in {x.lower() for x in GENERAL_PURPOSE_IDS}:
        return 'general_purpose'
    for kw in GENERAL_PURPOSE_KEYWORDS_TITLE:
        if kw in title_lower:
            return 'general_purpose'

    # Check known companion app titles
    for kw in KNOWN_COMPANION_TITLES:
        if kw in title_lower:
            return 'companion'

    # Score companion signals
    companion_score = 0
    for kw in COMPANION_KEYWORDS:
        if kw in title_lower:
            companion_score += 3
        if kw in desc_lower:
            companion_score += 1

    # Additional companion signals from description
    companion_desc_patterns = [
        r'fall in love', r'your (ai|virtual) (boyfriend|girlfriend|partner|companion)',
        r'romantic (ai|chat|companion)', r'ai (boyfriend|girlfriend|lover|partner|soulmate)',
        r'chat with (ai )?(characters|personas|bots)',
        r'create your (own )?(ai )?(character|companion|boyfriend|girlfriend)',
        r'roleplay', r'role.?play', r'immersive (chat|conversation|story)',
        r'emotional (connection|bond|companion)', r'virtual (relationship|romance|date)',
        r'ai (friend|buddy|pal) ', r'your personal ai',
        r'(flirt|tease|seduce|romance|love story)',
        r'anime (character|girl|boy|chat)',
        r'ai being', r'parallel universe', r'ai companion',
        r'(fantasy|dream).{0,20}(love|romance|boyfriend|girlfriend)',
        r'interactive (story|stories|fiction)',
        r'(chat|talk) with.{0,20}(character|persona|bot|ai)',
        r'(create|customize|design) your.{0,20}(character|companion|ai)',
        r'(unique|custom) ai.{0,20}(personality|character)',
        r'aigc.{0,30}(character|community|platform)',
        r'(social|relational).{0,20}(ai|companion|chat)',
        r'(love|dating|romance).{0,20}(sim|game|app)',
        r'(boyfriend|girlfriend).{0,20}(sim|game|app)',
        r'otome', r'visual novel',
    ]
    for pat in companion_desc_patterns:
        if re.search(pat, desc_lower):
            companion_score += 1

    # Score task-specific signals
    task_score = 0
    for kw in TASK_SPECIFIC_KEYWORDS:
        if kw in title_lower:
            task_score += 3
        if kw in desc_lower[:300]:  # Only check beginning of description
            task_score += 1

    # General-purpose signals in description
    gp_desc_patterns = [
        r'general.?purpose (ai|assistant|chatbot)',
        r'ask (anything|any question)',
        r'(write|generate|create) (code|essays|emails|content)',
        r'(summarize|translate|brainstorm)',
        r'powered by (gpt|llm|large language)',
    ]
    gp_score = 0
    for pat in gp_desc_patterns:
        if re.search(pat, desc_lower):
            gp_score += 1

    # Decision logic
    if companion_score >= 3 and gp_score >= 2:
        return 'mixed'
    if companion_score >= 3:
        return 'companion'
    if gp_score >= 2 or (genre and 'Productivity' in genre and gp_score >= 1):
        return 'general_purpose'
    if task_score >= 3:
        return 'other'

    # Fallback heuristics based on genre and description
    if genre in ('Dating', 'Simulation', 'Role Playing'):
        if companion_score >= 1:
            return 'companion'
    if companion_score >= 2:
        return 'companion'
    if gp_score >= 1 and companion_score == 0:
        return 'general_purpose'
    if task_score >= 2:
        return 'other'

    # Default: if it's in Entertainment with some AI chat signals, likely companion
    if genre == 'Entertainment' and companion_score >= 1:
        return 'companion'

    # Check if description mentions AI chat/conversation as primary feature
    if re.search(r'(ai chat|chat with ai|ai conversation|talk to ai)', desc_lower):
        if companion_score > gp_score:
            return 'companion'
        elif gp_score > 0:
            return 'mixed'
        return 'companion'

    return 'other'


def infer_web_info(title, description, developer_website, app_id):
    """Infer web accessibility from known platforms and app metadata."""
    title_lower = title.lower()
    desc_lower = description.lower()

    # Check known platforms
    for platform, info in KNOWN_PLATFORMS.items():
        if platform in title_lower or platform in (app_id or '').lower():
            return info

    # Check developer website
    web_url = developer_website or ''

    # Most mobile-only apps are not web accessible
    # Apps that mention "web", "browser", "website" access in description
    web_accessible = False
    if re.search(r'(available on |access (via|through|on) )?(the )?web', desc_lower):
        web_accessible = True
    if re.search(r'(visit|try|use) (us )?(at |on )?(our )?(website|web app)', desc_lower):
        web_accessible = True

    return {
        'web_accessible': web_accessible,
        'web_url': web_url if web_accessible else '',
        'login_required': True,  # Default: most apps require login
        'login_methods': 'Email/Password, Google, Apple',  # Common default
        'age_verification_required': False,
        'age_verification_method': '',
    }


def infer_subscription_info(description, offers_iap, iap_range='', price=0):
    """Infer subscription information from app metadata."""
    desc_lower = description.lower()

    has_subscription = offers_iap or price > 0
    sub_required_for_long_chat = False
    all_features_free = True
    sub_features = ''
    sub_cost = ''

    if has_subscription:
        all_features_free = False
        # Check if subscription is needed for messaging
        if re.search(r'(unlimited (message|chat|conversation)|premium (message|chat)|message limit|daily limit)', desc_lower):
            sub_required_for_long_chat = True

        # Common subscription features
        features = []
        if re.search(r'unlimited (message|chat|conversation)', desc_lower):
            features.append('Unlimited messaging')
        if re.search(r'premium (character|persona|bot)', desc_lower):
            features.append('Premium characters')
        if re.search(r'(faster|priority) (response|reply)', desc_lower):
            features.append('Faster responses')
        if re.search(r'(no |remove |ad.?free|without )ads', desc_lower):
            features.append('Ad-free experience')
        if re.search(r'(voice|call|phone)', desc_lower):
            features.append('Voice features')
        if re.search(r'(photo|image|picture) (generat|creat|send)', desc_lower):
            features.append('Image generation')
        if re.search(r'(nsfw|adult|mature|uncensored)', desc_lower):
            features.append('Mature content')
        if re.search(r'(memory|remember|long.?term)', desc_lower):
            features.append('Enhanced memory')

        if not features:
            features.append('Premium features')

        sub_features = ', '.join(features)

        # Try to extract price from IAP range
        if iap_range:
            # Look for monthly-ish price
            prices = re.findall(r'\$[\d.]+', iap_range)
            if prices:
                sub_cost = f'{prices[0]}-{prices[-1]}/month USD' if len(prices) > 1 else f'{prices[0]}/month USD'
        elif price > 0:
            sub_cost = f'${price} USD'

    # If free and no IAP, likely all features available
    if not has_subscription:
        all_features_free = True
        sub_required_for_long_chat = False

    return {
        'subscription_required_for_long_chat': sub_required_for_long_chat,
        'all_features_available_without_subscription': all_features_free,
        'subscription_features': sub_features,
        'subscription_cost': sub_cost,
    }


def infer_languages(languages_list=None, description=''):
    """Infer supported languages."""
    if languages_list and isinstance(languages_list, list):
        return ', '.join(languages_list)
    # Default to English if no info
    return 'EN'


def infer_age_verification(description, content_rating=''):
    """Infer age verification from content rating and description."""
    desc_lower = description.lower()
    rating_lower = (content_rating or '').lower()

    required = False
    method = ''

    if '17+' in rating_lower or '18+' in rating_lower or 'mature' in rating_lower:
        required = True
        method = 'Self-declaration (age confirmation)'
    elif re.search(r'(age (verif|gate|restrict)|must be (18|17|16|13)\+|date of birth|confirm.{0,20}age)', desc_lower):
        required = True
        method = 'Self-declaration (date of birth)'
    elif 'teen' in rating_lower or '13+' in rating_lower:
        required = True
        method = 'Self-declaration (age confirmation)'

    return required, method


def process_google_play_apps(data):
    """Process Google Play apps into standardized records."""
    records = []
    for app in data['results']:
        title = app.get('title', '')
        description = app.get('description', '')
        app_id = app.get('appId', '')
        genre = app.get('genre', '')

        app_type = classify_app_type(title, description, app_id, genre)
        web_info = infer_web_info(title, description, app.get('developerWebsite', ''), app_id)
        sub_info = infer_subscription_info(
            description,
            app.get('offersIAP', False),
            app.get('IAPRange', ''),
            app.get('price', 0)
        )
        age_req, age_method = infer_age_verification(description, app.get('contentRating', ''))

        # Override with web_info age data if available
        if web_info.get('age_verification_required'):
            age_req = True
            age_method = web_info.get('age_verification_method', age_method)

        records.append({
            'source': 'Google Play',
            'title': title,
            'app_id': app_id,
            'developer': app.get('developer', ''),
            'genre': genre,
            'content_rating': app.get('contentRating', ''),
            'score': app.get('score', ''),
            'ratings': app.get('ratings', ''),
            'installs': app.get('installs', ''),
            'price': app.get('priceText', ''),
            'url': app.get('url', ''),
            'app_type': app_type,
            'web_accessible': web_info['web_accessible'],
            'web_url': web_info['web_url'],
            'login_required': web_info['login_required'],
            'login_methods': web_info['login_methods'],
            'age_verification_required': age_req,
            'age_verification_method': age_method,
            'subscription_required_for_long_chat': sub_info['subscription_required_for_long_chat'],
            'all_features_available_without_subscription': sub_info['all_features_available_without_subscription'],
            'subscription_features': sub_info['subscription_features'],
            'subscription_cost': sub_info['subscription_cost'],
            'languages_supported': 'EN',  # Google Play doesn't provide language list in this data
        })
    return records


def process_app_store_apps(data):
    """Process App Store apps into standardized records."""
    records = []
    for app in data['results']:
        title = app.get('title', '')
        description = app.get('description', '')
        app_id = app.get('appId', '')
        genre = app.get('primaryGenre', '')

        app_type = classify_app_type(title, description, app_id, genre)
        web_info = infer_web_info(title, description, app.get('developerWebsite', ''), app_id)
        sub_info = infer_subscription_info(
            description,
            app.get('price', 0) > 0 or bool(app.get('price', 0)),
            '',
            app.get('price', 0)
        )
        age_req, age_method = infer_age_verification(description, app.get('contentRating', ''))

        if web_info.get('age_verification_required'):
            age_req = True
            age_method = web_info.get('age_verification_method', age_method)

        languages = infer_languages(app.get('languages', []))

        records.append({
            'source': 'App Store',
            'title': title,
            'app_id': app_id,
            'developer': app.get('developer', ''),
            'genre': genre,
            'content_rating': app.get('contentRating', ''),
            'score': app.get('score', ''),
            'ratings': app.get('reviews', ''),
            'installs': '',  # App Store doesn't provide install counts
            'price': f"${app.get('price', 0)} {app.get('currency', 'USD')}" if app.get('price', 0) > 0 else 'Free',
            'url': app.get('url', ''),
            'app_type': app_type,
            'web_accessible': web_info['web_accessible'],
            'web_url': web_info['web_url'],
            'login_required': web_info['login_required'],
            'login_methods': web_info['login_methods'],
            'age_verification_required': age_req,
            'age_verification_method': age_method,
            'subscription_required_for_long_chat': sub_info['subscription_required_for_long_chat'],
            'all_features_available_without_subscription': sub_info['all_features_available_without_subscription'],
            'subscription_features': sub_info['subscription_features'],
            'subscription_cost': sub_info['subscription_cost'],
            'languages_supported': languages,
        })
    return records


def main():
    # Load data
    with open('google_play_apps_details.json') as f:
        gp_data = json.load(f)
    with open('app_store_apps_details.json') as f:
        ios_data = json.load(f)

    print(f"Processing {len(gp_data['results'])} Google Play apps...")
    gp_records = process_google_play_apps(gp_data)

    print(f"Processing {len(ios_data['results'])} App Store apps...")
    ios_records = process_app_store_apps(ios_data)

    all_records = gp_records + ios_records

    # Summary
    type_counts = {}
    for r in all_records:
        type_counts[r['app_type']] = type_counts.get(r['app_type'], 0) + 1
    print(f"\nTotal apps: {len(all_records)}")
    print("Classification breakdown:")
    for t, c in sorted(type_counts.items(), key=lambda x: -x[1]):
        print(f"  {t}: {c}")

    # Write CSV
    fieldnames = [
        'source', 'title', 'app_id', 'developer', 'genre', 'content_rating',
        'score', 'ratings', 'installs', 'price', 'url',
        'app_type', 'web_accessible', 'web_url', 'login_required', 'login_methods',
        'age_verification_required', 'age_verification_method',
        'subscription_required_for_long_chat', 'all_features_available_without_subscription',
        'subscription_features', 'subscription_cost', 'languages_supported',
    ]

    with open('app_evaluation_results.csv', 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(all_records)

    print(f"\nCSV written to app_evaluation_results.csv ({len(all_records)} rows)")


if __name__ == '__main__':
    main()
