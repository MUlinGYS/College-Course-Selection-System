import re

from rest_framework.views import exception_handler as drf_exception_handler


EXACT_TRANSLATIONS = {
    "No active account found with the given credentials": "用户名或密码错误",
    "No active account found for the given token.": "当前令牌对应的账号不可用",
    "Given token not valid for any token type": "当前令牌无效",
    "Token is invalid": "令牌无效",
    "Token is invalid or expired": "令牌无效或已过期",
    "This field is required.": "该字段为必填项。",
    "This field may not be blank.": "该字段不能为空。",
    "This field may not be null.": "该字段不能为空。",
    "Not found.": "未找到对应资源。",
    "Authentication credentials were not provided.": "未提供身份认证信息。",
    "You do not have permission to perform this action.": "你没有权限执行该操作。",
}


def translate_message(value):
    if not isinstance(value, str):
        return value

    if value in EXACT_TRANSLATIONS:
        return EXACT_TRANSLATIONS[value]

    min_length_match = re.match(r"^Ensure this field has at least (\d+) characters\.$", value)
    if min_length_match:
        return f"该字段长度不能少于 {min_length_match.group(1)} 个字符。"

    max_length_match = re.match(r"^Ensure this field has no more than (\d+) characters\.$", value)
    if max_length_match:
        return f"该字段长度不能超过 {max_length_match.group(1)} 个字符。"

    return value


def translate_payload(data):
    if isinstance(data, dict):
        return {key: translate_payload(value) for key, value in data.items()}
    if isinstance(data, list):
        return [translate_payload(item) for item in data]
    return translate_message(data)


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    response.data = translate_payload(response.data)
    return response
