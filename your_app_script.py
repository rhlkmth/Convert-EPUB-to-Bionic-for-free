import streamlit as st
import tempfile
import BeautifulSoup4 from BeautifulSoup
import re
from ebooklib import epub
from tqdm import tqdm
from pathlib import Path

def _convert_file_path(path):
    path_obj = Path(path)
    new_name = "converted-" + path_obj.stem + ".epub"  # Change this line
    new_path = path_obj.with_name(new_name)
    return str(new_path)

def convert_to_bionic_str(soup: BeautifulSoup, s: str):
    new_parent = soup.new_tag("span")
    words = re.split(r'.,;:!?-|\s', s)
    for word in words:
        if len(word) >= 4:  # Increase frequency by bolding words with length >= 4
            mid = (len(word) // 2) + 1
            first_half, second_half = word[:mid], word[mid:]
            b_tag = soup.new_tag("b")
            b_tag.append(soup.new_string(first_half))
            new_parent.append(b_tag)
            new_parent.append(soup.new_string(second_half + " "))
        else:
            new_parent.append(soup.new_string(word + " "))
    return new_parent

def convert_to_bionic(content: str):
    soup = BeautifulSoup(content, 'html.parser')
    for e in soup.descendants:
        if isinstance(e, bs4.element.Tag):
            if e.name == "p":  # Process all paragraphs
                children = list(e.children)
                for child in children:
                    if isinstance(child, bs4.element.NavigableString):
                        if len(child.text.strip()):
                            child.replace_with(convert_to_bionic_str(soup, child.text))
    return str(soup).encode()

def convert_book(book_path):
    source = epub.read_epub(book_path)
    for item in tqdm(source.items):
        if item.media_type == "application/xhtml+xml":
            content = item.content.decode('utf-8')
            item.content = convert_to_bionic(content)
    epub.write_epub(_convert_file_path(book_path), source)

def main():
    st.title("Book Conversion")
    book_path = st.file_uploader("Upload a book file", type=["epub"])

    if book_path is not None:
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(book_path.read())
            tmp_file_path = tmp_file.name

        convert_book(tmp_file_path)
        converted_path = _convert_file_path(tmp_file_path)
        st.success(f"Book converted successfully! Downloaded {converted_path}")

if __name__ == "__main__":
    main()
