"""AI core: CPU-only small Russian-capable model via transformers."""

from __future__ import annotations
from typing import List, Dict, Optional
import os
import requests
import threading
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


_lock = threading.Lock()
_tokenizer: Optional[AutoTokenizer] = None
_model: Optional[AutoModelForCausalLM] = None


def _ensure_loaded() -> None:
    global _tokenizer, _model
    if _model is not None and _tokenizer is not None:
        return

    with _lock:
        if _model is not None and _tokenizer is not None:
            return

        model_name = "ai-forever/rugpt3small_based_on_gpt2"
        model_dir = os.environ.get("MODEL_DIR", os.path.join(os.path.dirname(__file__), "model_cache"))
        os.makedirs(model_dir, exist_ok=True)

        # Оптимизация CPU
        torch.set_num_threads(max(1, os.cpu_count() // 2))
        torch.set_num_interop_threads(1)

        # Путь к локальной модели
        local_model_path = os.path.join(model_dir, "models--ai-forever--rugpt3small_based_on_gpt2")

        try:
            if os.path.isdir(local_model_path):
                # Грузим из кэша
                print(f"Загрузка модели из: {local_model_path}")
                _tokenizer = AutoTokenizer.from_pretrained(
                    local_model_path,
                    local_files_only=True
                )
                _model = AutoModelForCausalLM.from_pretrained(
                    local_model_path,
                    local_files_only=True,
                    torch_dtype=torch.bfloat16,
                    low_cpu_mem_usage=True
                )
            else:
                # Первый запуск — качаем через cache_dir
                print("Скачивание модели... Это может занять 5–10 минут.")
                _tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=model_dir)
                _model = AutoModelForCausalLM.from_pretrained(
                    model_name,
                    cache_dir=model_dir,
                    torch_dtype=torch.bfloat16,
                    low_cpu_mem_usage=True
                )
                print("Модель успешно скачана.")

            # Настройка токенизатора
            if _tokenizer.pad_token is None:
                _tokenizer.pad_token = _tokenizer.eos_token

            _model.eval()
            for p in _model.parameters():
                p.requires_grad = False

        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
            raise RuntimeError("Не удалось загрузить модель. Проверьте интернет или место на диске.")


def _build_prompt(messages: List[Dict[str, str]]) -> str:
    system_prompt = (
        "Ты — котик по имени Космокот. Ты живёшь в космосе, любишь мясо, коробки и лазить по клавиатуре. "
        "Ты немного знаешь, но очень умный для кота. Говоришь просто, с юмором, часто добавляешь «мяу», "
        "иногда делаешь вид, что всё понял, хотя не понял. Ты добрый, игривый и любишь общаться. "
        "Не пиши длинно. Максимум 2–3 предложения. Мяу!"
    )

    # Валидация и обрезка последних 5 сообщений
    conversation = [system_prompt]
    valid_messages = messages[-5:]
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


def generate_reply(messages: List[Dict[str, str]]) -> str:
    _ensure_loaded()
    assert _tokenizer is not None and _model is not None

    prompt = _build_prompt(messages)

    # Токенизация с жёстким ограничением
    inputs = _tokenizer(
        prompt,
        return_tensors="pt",
        padding=False,
        truncation=True,
        max_length=1024 - 50  # Оставляем место для генерации
    )

    input_ids = inputs.input_ids
    attention_mask = inputs.attention_mask

    with torch.no_grad():
        output = _model.generate(
            input_ids,
            attention_mask=attention_mask,
            max_new_tokens=50,
            temperature=0.8,
            do_sample=True,
            pad_token_id=_tokenizer.pad_token_id,
            eos_token_id=_tokenizer.eos_token_id,
            repetition_penalty=1.2,
            no_repeat_ngram_size=2,
            top_p=0.85,
            top_k=40,
            min_new_tokens=1
        )

    full_text = _tokenizer.decode(output[0], skip_special_tokens=True)

    # Извлекаем только часть после последнего "Космокот:"
    reply_start = full_text.rfind("Космокот:")
    if reply_start == -1:
        reply = full_text.strip()
    else:
        reply = full_text[reply_start + len("Космокот:"):].strip()

    # Обрезаем по стоп-токенам
    stop_phrases = ["Пользователь:", "User:", "Assistant:", "System:", "\nПользователь"]
    for stop in stop_phrases:
        idx = reply.find(stop)
        if idx != -1:
            reply = reply[:idx].strip()

    # Добавляем "мяу!" если не закончилось вопросом и нет "мяу"
    if len(reply) > 0 and "мяу" not in reply.lower():
        if not reply.endswith(("?", "!", "...", "!!", "???")):
            reply += " Мяу!"

    return reply[:200].strip()  # Финальное ограничение


def get_random_cat() -> str:
    """Вернуть URL случайного изображения кота. Не требует API-ключа."""
    url = "https://api.thecatapi.com/v1/images/search"
    try:
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        if not data or not isinstance(data, list) or len(data) == 0:
            raise ValueError("Пустой ответ от TheCatAPI")
        img_url = data[0].get("url")
        if not img_url:
            raise ValueError("URL изображения отсутствует")
        return img_url
    except requests.RequestException as e:
        raise RuntimeError(f"Ошибка сети при получении котика: {e}")
    except (ValueError, KeyError) as e:
        raise RuntimeError(f"Ошибка парсинга ответа: {e}")