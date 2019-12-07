from typing import Dict, Any, Iterable

from os import listdir
from requests import post
import grequests
from grequests import post, map
from json import dumps


GOOGLE_URL = 'https://vision.googleapis.com/v1/files:annotate'


def exception_handler(request, exception):
    print("Request failed")


def get_token() -> str:
    with open('./token.txt') as f:
        return f.read().strip()


def auth_headers(token: str) -> Dict[str, str]:
    return {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json; charset=utf-8'
    }


def storage_file_path(filename: str) -> str:
    return f'gs://sanepid-data-infestation/as-of-06-12-2019/{filename}'


def annotate_file_request(filename: str) -> Dict[str, Any]:
    return {
        "requests": [
            {
                "inputConfig": {
                    "gcsSource": {
                        "uri": storage_file_path(filename)
                    },
                    "mimeType": "application/pdf"
                },
                "features": [
                    {
                        "type": "DOCUMENT_TEXT_DETECTION"
                    }
                ],
                # "pages": [
                #     1, 2, 3, 4, 5
                # ]
            }
        ]
    }


def extract_file_text(filename: str) -> Dict:
    response = post(
        GOOGLE_URL,
        data=dumps(annotate_file_request(filename)),
        headers=auth_headers(get_token()),
    )

    return response.json()


def main():
    files: Iterable[str] = listdir('./downloads')

    print(auth_headers(get_token()))

    # with open(f'./result/{files[0]}', 'w') as f:
    #     f.write(dumps(data))

    for file in files:
        basename, extension = file.rsplit('.', 1)
        outpath = f'./result/{basename}.json'

        data = extract_file_text(file)

        with open(outpath, 'w') as f:
            f.write(dumps(data, indent=2))

        print(f'{file} -> {outpath} [OK]')


if __name__ == '__main__':
    main()
