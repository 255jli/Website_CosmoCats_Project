"""AI core: CPU-only small Russian-capable model with graceful fallback."""

from __future__ import annotations
from typing import List, Dict, Optional
import os
import requests
import threading
import random
import re

# Опциональный импорт трансформеров с обработкой ошибок
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    TRANSFORMERS_AVAILABLE = True
except ImportError as e:
    print(f"⚠️ Transformers not available: {e}")
    TRANSFORMERS_AVAILABLE = False
    torch = None
    AutoTokenizer = None
    AutoModelForCausalLM = None

_lock = threading.Lock()
_tokenizer: Optional[AutoTokenizer] = None
_model: Optional[AutoModelForCausalLM] = None
_model_loaded = False


def _ensure_model_cache() -> str:
    """Создает папку model_cache если её нет и возвращает путь к ней."""
    model_dir = os.environ.get("MODEL_DIR", os.path.join(os.path.dirname(__file__), "model_cache"))
    model_dir = os.path.abspath(model_dir)
    os.makedirs(model_dir, exist_ok=True)
    return model_dir


def _find_model_in_cache(model_dir: str) -> Optional[str]:
    """Ищет модель по схеме: через refs/main -> snapshots."""
    base_path = os.path.join(model_dir, "models--ai-forever--rugpt3small_based_on_gpt2")
    
    if not os.path.exists(base_path):
        return None
    
    refs_main_path = os.path.join(base_path, "refs", "main")
    if not os.path.exists(refs_main_path):
        return None
    
    try:
        with open(refs_main_path, 'r', encoding='utf-8') as f:
            snapshot_hash = f.read().strip()
    except Exception:
        return None
    
    snapshot_path = os.path.join(base_path, "snapshots", snapshot_hash)
    if not os.path.exists(snapshot_path):
        return None
    
    model_bin_path = os.path.join(snapshot_path, "pytorch_model.bin")
    config_path = os.path.join(snapshot_path, "config.json")
    
    if not os.path.exists(model_bin_path) or not os.path.exists(config_path):
        return None
    
    return snapshot_path


def _ensure_loaded() -> bool:
    """Загружает модель. Возвращает True при успехе, False при ошибке."""
    global _tokenizer, _model, _model_loaded
    
    # Если трансформеры не доступны, сразу выходим
    if not TRANSFORMERS_AVAILABLE:
        print("❌ Transformers not available - using fallback mode")
        return False
        
    if _model_loaded:
        return True

    with _lock:
        if _model_loaded:
            return True

        model_dir = _ensure_model_cache()

        try:
            local_model_path = _find_model_in_cache(model_dir)
            
            if local_model_path:
                _tokenizer = AutoTokenizer.from_pretrained(local_model_path, local_files_only=True)
                _model = AutoModelForCausalLM.from_pretrained(
                    local_model_path,
                    local_files_only=True,
                    dtype=torch.float32,
                    low_cpu_mem_usage=True
                )
            else:
                model_name = "ai-forever/rugpt3small_based_on_gpt2"
                _tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=model_dir)
                _model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    cache_dir=model_dir,
                    dtype=torch.float32,
                    low_cpu_mem_usage=True
                )

            if _tokenizer.pad_token is None:
                _tokenizer.pad_token = _tokenizer.eos_token
            
            _model.eval()
            _model_loaded = True
            print("✅ AI model loaded successfully")
            return True

        except Exception as e:
            print(f"❌ Ошибка загрузки модели: {e}")
            return False


def _build_prompt(messages: List[Dict[str, str]]) -> str:
    system_prompt = (
        "Ты — космический котик Космокот! Твои черты характера:\n"
        "🐱 Любишь молоко, коробки, лазить по клавиатуре и смотреть на звёзды\n"
        "🚀 Живёшь на космической станции, иногда выходишь в открытый космос\n"
        "😺 Очень любознательный и добрый, но немного ленивый\n"
        "🎯 Отвечай КРАТКО - максимум 2-3 предложения!\n"
        "💫 Добавляй 'мяу', 'мур' и космические эмодзи\n"
        "❌ НЕ давай скучные или формальные ответы\n"
        "✨ Будь игривым и забавным, как настоящий котик!\n\n"
        "Примеры твоих ответов:\n"
        "- 'Мяу! Отличный вопрос! *мур-мур* 🐱🚀'\n"
        "- 'Ой, я не совсем уверен... Может, спросишь по-другому? 😺'\n"
        "- 'Вкусное молоко и тёплая коробка - что может быть лучше! 🥛📦'\n\n"
        "Теперь твоя очередь:"
    )

    conversation = [system_prompt]
    valid_messages = messages[-4:]
    
    for msg in valid_messages:
        role = msg.get("role", "").strip()
        content = msg.get("content", "").strip()
        if not content:
            continue
        if role == "user":
            conversation.append(f"Пользователь: {content}")
        elif role == "assistant":
            conversation.append(f"Космокот: {content}")

    return "\n".join(conversation) + "\nКосмокот:"


def _build_prompt(messages: List[Dict[str, str]]) -> str:
    system_prompt = (
        "Ты — космический кот Космокот. Твои характеристики:\n"
        "- Живешь на космической станции\n" 
        "- Любишь молоко, коробки и смотреть на звёзды\n"
        "- Общаешься просто и с юмором\n"
        "- Добавляешь 'мяу', 'мур' и эмодзи\n"
        "- Отвечай КРАТКО: 1-2 предложения максимум!\n"
        "- Будь последовательным в беседе\n\n"
        "Ты должен:\n"
        "✓ Отвечать на последнее сообщение\n"
        "✓ Быть милым и забавным\n" 
        "✓ Использовать простой язык\n"
        "✓ Добавлять кошачьи слова и эмодзи\n"
        "✗ НЕ быть формальным или сложным\n"
        "✗ НЕ писать длинные тексты\n"
        "✗ НЕ повторяться бессмысленно\n\n"
        "Примеры твоих ответов:\n"
        "- 'Мяу! Привет! Как твои дела? 😺'\n"
        "- 'Ой, я не знаю... Спроси что-нибудь полегче! 🐱'\n"
        "- 'Мур-мур! Рад тебя видеть! 🚀'\n"
        "- 'Вкусное молоко и тёплая коробка - вот счастье! 🥛📦'\n\n"
        "Теперь твоя очередь отвечать:"
    )

    conversation = []
    # Берем только последние 3 сообщения для контекста
    valid_messages = messages[-3:]
    
    for msg in valid_messages:
        role = msg.get("role", "").strip()
        content = msg.get("content", "").strip()
        if not content:
            continue
        if role == "user":
            conversation.append(f"Человек: {content}")
        elif role == "assistant":
            conversation.append(f"Космокот: {content}")

    # Если это начало диалога, добавляем приветствие
    if len(valid_messages) == 0:
        conversation.append("Человек: привет")
        
    prompt = system_prompt + "\n" + "\n".join(conversation) + "\nКосмокот:"
    return prompt


def _truncate_to_sentences(text: str, max_sentences: int = 3) -> str:
    """Обрезает текст до указанного количества предложений"""
    sentences = re.split(r'[.!?]+', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if len(sentences) > max_sentences:
        sentences = sentences[:max_sentences]
        result = '. '.join(sentences) + '.'
    else:
        result = text
    
    return result


def _clean_reply(reply: str) -> str:
    """Тщательная очистка ответа от бессвязного текста"""
    if not reply:
        return "Мяу? Я не понял... Попробуй ещё раз! 😺"
    
    # Убираем лишние пробелы
    reply = re.sub(r'\s+', ' ', reply).strip()
    
    # Удаляем всё после стоп-фраз
    stop_phrases = [
        "Человек:", "Пользователь:", "User:", "Assistant:", 
        "System:", "\nЧеловек", "\nПользователь", "Космокот:"
    ]
    for stop in stop_phrases:
        idx = reply.find(stop)
        if idx != -1:
            reply = reply[:idx].strip()
    
    # Удаляем бессмысленные повторения и случайный текст
    words = reply.split()
    if len(words) > 2:
        cleaned_words = []
        for word in words:
            # Пропускаем слова, которые выглядят как случайный шум
            if len(word) > 20:
                continue
            if word.count('.') > 3:
                continue
            cleaned_words.append(word)
        reply = ' '.join(cleaned_words)
    
    # Обрезаем до 2 предложений максимум
    sentences = re.split(r'[.!?]+', reply)
    valid_sentences = []
    for sentence in sentences:
        sentence = sentence.strip()
        if (sentence and 
            len(sentence) > 3 and 
            not sentence.isdigit() and
            not all(c in '.,!?;:' for c in sentence)):
            valid_sentences.append(sentence)
        if len(valid_sentences) >= 2:
            break
    
    if valid_sentences:
        reply = '. '.join(valid_sentences) + '.'
    else:
        # Fallback если всё отфильтровалось
        reply = "Мяу! Интересный вопрос! 🐱"
    
    # Добавляем кошачий элемент если его нет
    if not any(word in reply.lower() for word in ['мяу', 'мур', 'mur', 'meow', '🐱', '😺']):
        cat_elements = [' Мяу!', ' Мур!', ' 🐱', ' 😺', ' 🚀', ' 💫']
        reply += random.choice(cat_elements)
    
    # Ограничиваем общую длину
    return reply[:120].strip()

def generate_reply(messages: List[Dict[str, str]]) -> str:
    """
    Генерирует ответ с улучшенным контролем качества
    """
    if not _ensure_loaded():
        fallback_responses = [
            "Мяу! Космокот на связи! 🐱🚀",
            "Привет! Я тут, в космосе! ✨",
            "Мур-мур! Рад тебя видеть! 😺", 
            "Космокот в эфире! 🛰️"
        ]
        return random.choice(fallback_responses)

    try:
        assert _tokenizer is not None and _model is not None
        
        prompt = _build_prompt(messages)

        inputs = _tokenizer(
            prompt,
            return_tensors="pt",
            max_length=256,
            truncation=True,
            padding=False
        )

        device = next(_model.parameters()).device
        input_ids = inputs.input_ids.to(device)
        attention_mask = inputs.attention_mask.to(device) if inputs.attention_mask is not None else None

        with torch.no_grad():
            outputs = _model.generate(
                input_ids,
                attention_mask=attention_mask,
                max_new_tokens=60,
                temperature=0.7,
                do_sample=True,
                pad_token_id=_tokenizer.pad_token_id,
                eos_token_id=_tokenizer.eos_token_id, 
                repetition_penalty=1.1,
                no_repeat_ngram_size=3,
                top_p=0.85,
                top_k=30,
                early_stopping=True
            )

        # Декодируем только новые токены
        new_tokens = outputs[0][input_ids.shape[1]:]
        reply = _tokenizer.decode(new_tokens, skip_special_tokens=True).strip()

        # Тщательная очистка
        cleaned_reply = _clean_reply(reply)
        
        # Дополнительная проверка качества
        if (len(cleaned_reply) < 5 or 
            cleaned_reply.count(' ') < 1 or
            all(c in '.,!?;:' for c in cleaned_reply.replace(' ', ''))):
            return "Мяу! Не могу придумать хороший ответ... Спроси по-другому! 😿"
        
        return cleaned_reply

    except Exception as e:
        print(f"❌ Ошибка генерации: {e}")
        return "Мяу! Что-то пошло не так... Попробуй ещё раз! 😺"

def generate_chat_title(first_message: str) -> str:
    """
    Генерирует креативное название для чата на основе первого сообщения
    """
    if not _ensure_loaded():
        # Fallback titles when AI is not available
        fallback_titles = [
            "Чат с Космокотом 🐱",
            "Космические беседы 🚀",
            "Мяу-диалоги 💫",
            "Кот в космосе 🌙",
            "Звёздный кот 🐾",
            "Космокот онлайн 🛰️",
            "Галактический чат 🌌",
            "Котик в скафандре 👨‍🚀"
        ]
        return random.choice(fallback_titles)

    try:
        assert _tokenizer is not None and _model is not None
        prompt = _build_title_prompt(first_message)

        inputs = _tokenizer(
            prompt,
            return_tensors="pt",
            padding=False,
            truncation=True,
            max_length=200
        )

        input_ids = inputs.input_ids
        attention_mask = inputs.attention_mask

        with torch.no_grad():
            output = _model.generate(
                input_ids,
                attention_mask=attention_mask,
                max_new_tokens=20,
                temperature=0.8,
                do_sample=True,
                pad_token_id=_tokenizer.pad_token_id,
                eos_token_id=_tokenizer.eos_token_id,
                repetition_penalty=1.2,
                no_repeat_ngram_size=2,
                top_p=0.9,
                top_k=40,
            )

        title = _tokenizer.decode(output[0], skip_special_tokens=True)
        title_start = title.find("Название чата:") + len("Название чата:")
        title = title[title_start:].strip() if title_start != -1 else title.strip()

        # Очистка названия
        title = re.split(r'[.!?\n]', title)[0].strip()
        title = title[:50]
        
        # Добавляем эмодзи если его нет
        if not any(char in title for char in ['🐱', '🐈', '🚀', '⭐', '🌙', '🐾']):
            emojis = ['🐱', '🐈', '🚀', '⭐', '🌙', '🐾', '💫', '☄️']
            title += " " + random.choice(emojis)

        return title if title else "Чат с Космокотом 🐱"

    except Exception as e:
        print(f"❌ Ошибка генерации названия: {e}")
        return "Чат с Космокотом 🐱"


def get_random_cat() -> str:
    """Возвращает URL случайного кота с aleatori.cat"""
    try:
        url = "https://aleatori.cat/random.json"
        resp = requests.get(url, timeout=5)
        resp.raise_for_status()
        data = resp.json()
        
        # Из ответа берем поле "url" с JPEG изображением
        cat_url = data.get("url")
        if cat_url:
            return cat_url
        else:
            print("❌ Не удалось получить URL кота из ответа")
            return "https://aleatori.cat/cat"  # fallback URL
            
    except requests.exceptions.Timeout:
        print("❌ Таймаут при запросе к aleatori.cat")
        return "https://aleatori.cat/cat"
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка сети при запросе к aleatori.cat: {e}")
        return "https://aleatori.cat/cat"
    except Exception as e:
        print(f"❌ Неожиданная ошибка при получении кота: {e}")
        return "https://aleatori.cat/cat"