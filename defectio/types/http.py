from typing import Dict, Optional, List, Union, Any


class QueryNodeFeature:
    registration: bool
    captcha: Dict[str, Any]
    email: bool
    invite_only: str
    autumn: Dict[str, Any]
    january: Dict[str, Any]
    voso: Dict[str, Any]


class QueryNode:
    revolt: str
    features: QueryNodeFeature
    ws: str
    app: str
    vapid: str


class OnboardingStatus:
    onboarding: bool
