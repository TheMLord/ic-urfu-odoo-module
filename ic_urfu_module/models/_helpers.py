"""Модульные функции, которыми пользуются разные модели."""

from .. import constants


def _expected_zet_from_hours(hours: int, hours_per_zet: int) -> int:
    """Ожидаемое целое ЗЕТ по объёму аудиторных часов и норме «часов на 1 ЗЕТ»."""
    if hours_per_zet <= 0 or hours <= 0:
        return 0
    raw = round(hours / float(hours_per_zet))
    return max(constants.MIN_CREDITS, min(constants.MAX_CREDITS, raw))


def _config_param_truthy(env, key: str, default: bool = True) -> bool:
    raw = env["ir.config_parameter"].sudo().get_param(key)
    if raw is None or raw == "":
        return default
    return str(raw).lower() in ("1", "true", "yes", "on")
