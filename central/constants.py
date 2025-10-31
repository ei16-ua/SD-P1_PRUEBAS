"""Shared constants for the CENTRAL module."""

from __future__ import annotations

from enum import Enum


class CPStatus(str, Enum):
    """High level state of a charging point."""

    DISCONNECTED = "DESCONECTADO"
    AVAILABLE = "ACTIVADO"
    PENDING_AUTH = "PENDIENTE_AUTORIZACION"
    SUPPLYING = "SUMINISTRANDO"
    STOPPED = "FUERA_DE_SERVICIO"
    FAULT = "AVERIA"


class HealthStatus(str, Enum):
    """Health reported by the charging point monitor."""

    OK = "OK"
    FAULT = "AVERIA"


class SessionState(str, Enum):
    """State of a supply session."""

    PENDING = "PENDIENTE"
    AUTHORIZED = "AUTORIZADA"
    DENIED = "DENEGADA"
    IN_PROGRESS = "EN_CURSO"
    FINISHED = "FINALIZADA"
    ABORTED = "CANCELADA"
