import base64


def get_b64_file_content(path: str) -> str:
    with open(path, 'rb') as f_opened:
        return base64.b64encode(f_opened.read()).decode()
