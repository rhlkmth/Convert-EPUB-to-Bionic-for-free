import streamlit as st
import tempfile
import re
from tqdm import tqdm
from pathlib import Path
import subprocess

# Install beautifulsoup4 and ebooklib packages
subprocess.run(["pip", "install", "beautifulsoup4", "ebooklib"])

from bs4 import BeautifulSoup
import bs4
from ebooklib import epub

def _convert_file_path(path, original_name):
    path_obj = Path(path)
    new_name = f"Bionic_{original_name}"
    new_path = path_obj.with_name(new_name)
    return str(new_path)

def convert_to_bionic_str(soup: BeautifulSoup, s: str):
    new_parent = soup.new_tag("span")
    words = re.split(r'.,;:!?-|\s', s)
    for word in words:
        if len(word) >= 2:
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
            if e.name == "p":
                children = list(e.children)
                for child in children:
                    if isinstance(child, bs4.element.NavigableString):
                        if len(child.text.strip()):
                            child.replace_with(convert_to_bionic_str(soup, child.text))
    return str(soup).encode()

def convert_book(book_path, original_name):
    source = epub.read_epub(book_path)
    total_items = len(list(source.items))
    progress_bar = st.progress(0)
    
    for i, item in enumerate(source.items):
        if item.media_type == "application/xhtml+xml":
            content = item.content.decode('utf-8')
            item.content = convert_to_bionic(content)
        progress_bar.progress((i + 1) / total_items)
    
    converted_path = _convert_file_path(book_path, original_name)
    epub.write_epub(converted_path, source)
    
    with open(converted_path, "rb") as f:
        converted_data = f.read()
    
    return converted_data, Path(converted_path).name

def main():
    st.title("Convert your EPUB to Bionic")
    book_path = st.file_uploader("Upload a book file", type=["epub"])

    if book_path is not None:
        original_name = book_path.name
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(book_path.read())
            tmp_file_path = tmp_file.name

        if 'converted_data' not in st.session_state:
            with st.spinner("Processing the file..."):
                st.session_state.converted_data, st.session_state.converted_name = convert_book(tmp_file_path, original_name)
            st.success("Conversion completed!")
        
        converted_data = st.session_state.converted_data
        converted_name = st.session_state.converted_name
        st.download_button(
            label="Download Converted Book",
            data=converted_data,
            file_name=converted_name,
            mime="application/epub+zip"
        )

if __name__ == "__main__":
    main()
