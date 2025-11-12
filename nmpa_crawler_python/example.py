from pprint import pprint

from client import NMPAClient


def main() -> None:
    client = NMPAClient()
    client.warmup()

    params = {
        "itemId": "ff80808183cad75001840881f848179f",
        "searchValue": "阿司匹林",
        "pageNum": 1,
        "pageSize": 10,
        "isSenior": "N",
    }
    response = client.get("/data/nmpadata/search", params=params)
    data = response.json()
    pprint(data)


if __name__ == "__main__":
    main()
