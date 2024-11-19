import os

from dotenv import find_dotenv, load_dotenv

env_file = os.getenv('ENV_FILE', '.env.development')
env_file_ = find_dotenv(env_file)
load_dotenv(env_file_)
