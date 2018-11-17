import typing as t
import requests
import re
from bs4 import BeautifulSoup

YEAR_REGEX = re.compile(r'\d\d\d\d')

SOURCE_LINK = 'http://wwwold.pzh.gov.pl/oldpage/epimeld/index_p.html'
BASE_LINK = SOURCE_LINK.split('epimeld')[0] + 'epimeld/'


def link_directories() -> t.Generator[BeautifulSoup, None, None]:
    r = requests.get(SOURCE_LINK)
    soup = BeautifulSoup(r.content, 'html.parser')
    for td in soup.find_all('td', class_='gora'):
        for link in td.parent.find_all('a'):
            yield link


def pdf_links(link: str) -> t.Generator[BeautifulSoup, None, None]:
    r = requests.get(link)
    soup = BeautifulSoup(r.content, 'html.parser')
    for pdf_link in soup.find_all('a'):
        try:
            if pdf_link['href'].endswith('.pdf'):
                yield pdf_link
        except KeyError:
            pass


def all_pdfs() -> t.Generator[t.Tuple[str, str], None, None]:
    """
    :return: Generator[Tuple[
       daterange<str>: string with date of that pdf,
       link<str>: http link to that pdf
    ]]
    """
    for subdir_link in link_directories():
        year = YEAR_REGEX.search(subdir_link.text).group(0)
        base_link = BASE_LINK + subdir_link['href']
        for link in pdf_links(base_link):
            start, end = link.text.replace(' ', '').split('-')
            date = f'{start}.{year}-{end}.{year}'
            yield date, base_link.rsplit('/', maxsplit=1)[0] + '/' + link['href']


if __name__ == '__main__':
    for pdf in all_pdfs():
        print(pdf)
