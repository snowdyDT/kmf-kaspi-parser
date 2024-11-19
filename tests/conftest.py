import pytest
import os

from dotenv import find_dotenv, load_dotenv

env_file = f'{os.path.dirname(__file__)}/../.env.test'
env_file_ = find_dotenv(env_file)
load_dotenv(env_file_)


@pytest.fixture(scope='function')
def file_path():
    yield os.getenv('TEST_FILE_PATH')
