# models/__init__.py

from sqlalchemy.orm import declarative_base

# 定义共享的 Base
Base = declarative_base()

# 导入所有模型，确保它们被注册到 Base.metadata
from .user import *
from .question import *