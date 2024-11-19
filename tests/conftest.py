import os

import pytest
from dotenv import find_dotenv, load_dotenv

from src.kaspi_parser import util

env_file = f'{os.path.dirname(__file__)}/../.env.test'
env_file_ = find_dotenv(env_file)
load_dotenv(env_file_)


@pytest.fixture
def file_path():
    yield os.getenv('TEST_FILE_PATH')


@pytest.fixture
def sample_pdf_base64(file_path):
    yield util.encode_file(file_path=file_path)
