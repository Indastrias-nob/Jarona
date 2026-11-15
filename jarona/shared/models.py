"""Pydantic модели для Jarona — валидация данных между сервером и клиентом."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field

from .protocol import CommandStatus, CommandTarget, IntentType


class CommandRequest(BaseModel):
    """Запрос на выполнение команды."""
    text: str = Field(..., description="Текст команды (голосовая или текстовая)")
    target: CommandTarget = Field(CommandTarget.AUTO, description="Где выполнить")
    mode: str = Field("voice", description="voice | text")
    context: Optional[Dict[str, Any]] = Field(None, description="Дополнительный контекст")

    class Config:
        use_enum_values = True


class CommandResponse(BaseModel):
    """Ответ на выполнение команды."""
    status: CommandStatus
    intent: Optional[IntentType] = None
    answer: str = Field("", description="Текстовый ответ пользователю")
    result: Optional[Dict[str, Any]] = Field(None, description="Результат выполнения")
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        use_enum_values = True


class LLMIntent(BaseModel):
    """Намерение, распознанное LLM."""
    intent: IntentType
    args: Dict[str, Any] = Field(default_factory=dict)
    answer: str = Field("", description="Краткий ответ пользователю")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)

    class Config:
        use_enum_values = True


class VoiceCommand(BaseModel):
    """Голосовая команда."""
    audio_data: Optional[bytes] = None
    text: Optional[str] = None
    language: str = "ru-RU"
    sample_rate: int = 16000


class GPIOCommand(BaseModel):
    """Команда управления GPIO."""
    pin: int = Field(..., ge=1, le=40, description="Номер GPIO пина")
    action: str = Field(..., description="set | get | pwm")
    value: Optional[int] = Field(None, description="Значение 0/1 или PWM 0-100")


class WindowsCommand(BaseModel):
    """Команда для Windows ПК."""
    intent: IntentType
    args: Dict[str, Any]
    require_confirmation: bool = False


class SystemStatus(BaseModel):
    """Статус системы."""
    hostname: str
    uptime: float
    cpu_percent: float
    memory_percent: float
    temperature: Optional[float] = None
    gpio_available: bool = False
    connected_clients: int = 0


class ClientInfo(BaseModel):
    """Информация о подключённом клиенте."""
    client_id: str
    hostname: str
    os_type: str
    connected_at: datetime
    last_activity: datetime
