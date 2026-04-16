#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
云端 LLM API 调用（兼容 OpenAI 格式接口）
"""

import json
import logging
from typing import Optional

import requests

logger = logging.getLogger("ClueScreener")

# ---------- 配置文件读写 ----------
CONFIG_FILE = "./config.json"


def load_config() -> dict:
    import os
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {
        "cloud_api_key": "",
        "cloud_api_url": "https://open.bigmodel.cn/api/paas/v4",
        "cloud_model": "glm-4-flash",
        "theme": "light",
        "whisper_model": "base",
        "duplicate_threshold": 0.6,
    }


def save_config(config: dict):
    try:
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    except Exception as e:
        logger.error(f"保存配置失败: {e}")


# ---------- 云端调用 ----------
def call_cloud_api(prompt: str, api_key: str, api_url: str, model: str,
                   timeout: int = 60) -> Optional[str]:
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
    }
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.3,
        "max_tokens": 500,
    }
    try:
        url = api_url.rstrip("/")
        if not url.endswith("/chat/completions"):
            url += "/chat/completions"
        resp = requests.post(url, headers=headers, json=payload, timeout=timeout)
        if resp.status_code == 200:
            return resp.json()["choices"][0]["message"]["content"].strip()
        else:
            logger.warning(f"API 返回 {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as e:
        logger.error(f"API 调用异常: {e}")
        return None
