import os

from dotenv import find_dotenv, load_dotenv

env_file = os.getenv("ENV", f"{os.path.dirname(__file__)}/../../.env.development")
env_file_ = find_dotenv(env_file)
load_dotenv(env_file_)

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./test.db")
