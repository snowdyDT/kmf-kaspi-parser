import base64


def encode_file(file_path: str) -> str:
    """
    Encodes a file to a Base64 string.

    Args:
        file_path (str): The path to the file to be encoded.

    Returns:
        str: The Base64 encoded string representation of the file content.
    """
    with open(file_path, "rb") as file:
        return base64.b64encode(file.read()).decode("utf-8")
