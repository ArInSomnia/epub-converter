import streamlit as st
import fitz  # PyMuPDF
from ebooklib import epub
import tempfile
import os

# 1. Set up the Website Design
st.set_page_config(page_title="Library EPUB Converter", page_icon="📚")
st.title("Library Archive Converter 📚")
st.write("Upload a scanned PDF to instantly create an image-based EPUB for e-readers.")

# 2. Create the User Inputs (Text Box and File Uploader)
book_title = st.text_input("What is the Title of the Book?", "My Archive Book")
uploaded_pdf = st.file_uploader("Drag and drop your PDF here", type="pdf")

# 3. What happens when a file is uploaded
if uploaded_pdf is not None:
    
    # Create a button to start the process
    if st.button("Convert to EPUB"):
        
        # Show a loading spinner on the website
        with st.spinner("Converting... This might take a minute depending on the book size."):
            
            # --- Save the uploaded file temporarily ---
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_pdf:
                temp_pdf.write(uploaded_pdf.read())
                pdf_path = temp_pdf.name
                
            epub_path = pdf_path.replace(".pdf", ".epub")

            # --- Core Conversion Logic ---
            doc = fitz.open(pdf_path)
            book = epub.EpubBook()
            book.set_title(book_title)
            book.set_language('en')
            spine = ['nav']

            # Create a progress bar on the website
            progress_bar = st.progress(0)
            total_pages = len(doc)

            for page_number in range(total_pages):
                page = doc.load_page(page_number)
                pixmap = page.get_pixmap(dpi=150) 
                image_bytes = pixmap.tobytes("jpeg")
                image_filename = f"images/page_{page_number}.jpg"
                
                img_item = epub.EpubItem(uid=f"img_{page_number}", file_name=image_filename, media_type="image/jpeg", content=image_bytes)
                book.add_item(img_item)
                
                if page_number == 0:
                    book.set_cover("cover.jpg", image_bytes)
                
                chapter = epub.EpubHtml(title=f'Page {page_number + 1}', file_name=f'page_{page_number}.xhtml', lang='en')
                chapter.content = f'<html><body style="margin: 0; padding: 0; text-align: center;"><img src="{image_filename}" style="max-width: 100%; height: auto;" alt="Page {page_number + 1}"/></body></html>'
                book.add_item(chapter)
                spine.append(chapter)
                
                # Update the website's progress bar
                progress_bar.progress((page_number + 1) / total_pages)

            book.spine = spine
            epub.write_epub(epub_path, book)
            
            # --- Prepare the Download ---
            with open(epub_path, "rb") as f:
                epub_data = f.read()
            
            st.success("Conversion Complete!")
            
            # Create the auto-download button
            st.download_button(
                label="📥 Download Your EPUB",
                data=epub_data,
                file_name=f"{book_title.replace(' ', '_')}.epub",
                mime="application/epub+zip"
            )

# ---> THE FIX IS HERE <---
            doc.close()  # Tell PyMuPDF to close the file so Windows unlocks it

            # Clean up the temporary files from the server
            os.remove(pdf_path)
            os.remove(epub_path)