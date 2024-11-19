import os

from src.kaspi_parser import util


def test_encode_file(capsys, file_path):
    assert isinstance(file_path, str)
    assert os.path.isfile(file_path)
    encoded_file = util.encode_file(file_path=file_path)
    assert encoded_file and isinstance(encoded_file, str)
