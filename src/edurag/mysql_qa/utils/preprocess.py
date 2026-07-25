import jieba
import re

STOP_WORDS = {
    "的",
    "了",
    "在",
    "是",
    "我",
    "有",
    "和",
    "就",
    "不",
    "人",
    "都",
    "一",
    "一个",
    "上",
    "也",
    "很",
    "到",
    "说",
    "要",
    "去",
    "你",
    "会",
    "着",
    "没有",
    "看",
    "好",
    "自己",
    "这",
}


def tokenize(text: str):
    text = text.translate(
        str.maketrans(
            {
                "，": ",",
                "。": ".",
                "？": "?",
                "！": "!",
                "；": ";",
                "：": ":",
                "（": "(",
                "）": ")",
                "【": "[",
                "】": "]",
                "「": '"',
                "」": '"',
                "『": "'",
                "』": "'",
            }
        )
    ).lower()

    words = jieba.lcut(text, cut_all=False)

    return [w for w in words if w.strip() and w not in STOP_WORDS]
