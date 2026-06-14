import streamlit as st
import fitz  # PyMuPDF
from ebooklib import epub
import tempfile
import os
import pytesseract # The new AI engine!
from PIL import Image
import io
import sys  # <--- Make sure sys is imported!

# --- SMART ENVIRONMENT DETECTION ---
# This MUST be placed right here, BEFORE any other code runs!
if sys.platform.startswith('win'):
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'


st.set_page_config(page_title="Library EPUB Converter", page_icon="📚")
st.title("Library Archive Converter 📚")
st.write("Upload a scanned PDF. We will create an original image EPUB with a hidden searchable text layer!")

book_title = st.text_input("What is the Title of the Book?", "My Archive Book")
uploaded_pdf = st.file_uploader("Drag and drop your PDF here", type="pdf")

if uploaded_pdf is not None:
    if st.button("Convert to Searchable EPUB"):
        with st.spinner("Scanning and reading text... This will take longer than usual."):
            
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                temp_pdf.write(uploaded_pdf.read())
                pdf_path = temp_pdf.name
                
            epub_path = pdf_path.replace(".pdf", ".epub")

            doc = fitz.open(pdf_path)
            book = epub.EpubBook()
            book.set_title(book_title)
            book.set_language('en')
            spine = ['nav']

            progress_bar = st.progress(0)
            total_pages = len(doc)

            for page_number in range(total_pages):
                page = doc.load_page(page_number)
                
                # 1. Take the photo for the reader to see
                pixmap = page.get_pixmap(dpi=150) 
                image_bytes = pixmap.tobytes("jpeg")
                image_filename = f"images/page_{page_number}.jpg"
                
                img_item = epub.EpubItem(uid=f"img_{page_number}", file_name=image_filename, media_type="image/jpeg", content=image_bytes)
                book.add_item(img_item)
                
                if page_number == 0:
                    book.set_cover("cover.jpg", image_bytes)
                
                # 2. Convert the photo into a format Tesseract can read
                img_for_ai = Image.open(io.BytesIO(image_bytes))
                
                # 3. AI MAGIC: Read the words from the image!
                extracted_text = pytesseract.image_to_string(img_for_ai)
                
                # Clean up the text so HTML doesn't break
                safe_text = extracted_text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

                # 4. Create the HTML page
                # Notice the hidden text div at the bottom! It is transparent and tiny.
                chapter = epub.EpubHtml(title=f'Page {page_number + 1}', file_name=f'page_{page_number}.xhtml', lang='en')
                chapter.content = f'''
                    <html xmlns="http://www.w3.org/1999/xhtml">
                        <head><title>Page {page_number + 1}</title></head>
                        <body style="margin: 0; padding: 0; text-align: center;">
                            
                            <img src="{image_filename}" style="max-width: 100%; height: auto;" alt="Page {page_number + 1}"/>
                            
                            <div style="color: transparent; font-size: 1px; line-height: 1px; user-select: text;">
                                {safe_text}
                            </div>
                            
                        </body>
                    </html>
                '''
                book.add_item(chapter)
                spine.append(chapter)
                
                progress_bar.progress((page_number + 1) / total_pages)

            # ... (this is your existing code that loops through pages)
            book.spine = spine
            epub.write_epub(epub_path, book)
            
            # --- ADD THIS LINE HERE ---
            # This releases the Windows lock on the PDF file!
            doc.close() 
            
            # --- Prepare the Download ---
            with open(epub_path, "rb") as f:
                epub_data = f.read()
            
            st.success("Conversion Complete!")
            
            st.download_button(
                label="📥 Download Searchable EPUB",
                data=epub_data,
                file_name=f"{book_title.replace(' ', '_')}.epub",
                mime="application/epub+zip"
            )

            # Now Windows will allow you to delete these safely!
            os.remove(pdf_path)
            os.remove(epub_path)