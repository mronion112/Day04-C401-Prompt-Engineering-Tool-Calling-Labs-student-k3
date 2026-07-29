import requests 
from pprint import pprint


BOOK_API_KEY = "a32714a53b674ebc941254195eddc897"
url = "https://api.bigbookapi.com/search-books?query="


def search_book(nameBook: str):
    nameBook = nameBook.replace(" ", "+")
    response = requests.get(url+nameBook+ "&api-key="+BOOK_API_KEY)

    

    if response.status_code == 200:
        data = response.json()
        pprint(data)
        return data

    else:
        print("Lỗi:", response.status_code)


