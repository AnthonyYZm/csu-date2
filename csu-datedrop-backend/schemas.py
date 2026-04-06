from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class QuizSubmit(BaseModel):
    """问卷提交体：硬性字段可顶层传入；若前端整包发送 quiz 对象，会在校验前拆出 raw_quiz_data。"""

    model_config = ConfigDict(extra="forbid")

    gender: Optional[str] = None
    campus: Optional[str] = None
    crossCampus: Optional[str] = None
    sexuality: Optional[str] = None
    raw_quiz_data: Dict[str, Any] = Field(default_factory=dict)

    @model_validator(mode="before")
    @classmethod
    def split_hard_filters(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data
        if data.get("raw_quiz_data") is not None:
            return data
        hard_keys = {"gender", "campus", "crossCampus", "sexuality"}
        out = {k: data[k] for k in hard_keys if k in data}
        out["raw_quiz_data"] = {k: v for k, v in data.items() if k not in hard_keys}
        return out


# --- Auth ---


class RegisterRequest(BaseModel):
    email: str = Field(..., description="完整邮箱或学号（将自动补全 @csu.edu.cn）")
    password: str = Field(..., min_length=6)
    code: str = Field(..., min_length=6, max_length=6, description="邮箱验证码")
    name: str
    campus: str
    grade: str
    major: str
    no_edu: bool = False


class LoginRequest(BaseModel):
    email: str
    password: str
    no_edu: bool = False


# --- User ---


class ProfileUpdateRequest(BaseModel):
    name: Optional[str] = None
    bio: Optional[str] = None
    campus: Optional[str] = None
    grade: Optional[str] = None
    major: Optional[str] = None


class WechatUpdateRequest(BaseModel):
    wechat: str = ""


class ShootRequest(BaseModel):
    target_email: str
    message: str = ""


class PausedRequest(BaseModel):
    paused: bool


class GreetRequest(BaseModel):
    message: str


class SendCodeRequest(BaseModel):
    email: str = Field(..., description="完整邮箱或学号")
    no_edu: bool = False


class VerifyCodeRequest(BaseModel):
    email: str
    code: str = Field(..., min_length=6, max_length=6)


class EduEmailSendCodeRequest(BaseModel):
    edu_email: str = Field(..., description="教育邮箱地址（@csu.edu.cn）")


class EduEmailVerifyRequest(BaseModel):
    edu_email: str = Field(..., description="教育邮箱地址")
    code: str = Field(..., min_length=6, max_length=6, description="验证码")


class ResetPasswordRequest(BaseModel):
    email: str = Field(..., description="注册邮箱")
    code: str = Field(..., min_length=6, max_length=6, description="验证码")
    new_password: str = Field(..., min_length=6, description="新密码")
    no_edu: bool = False


class RunMatchBody(BaseModel):
    week_id: Optional[int] = None
