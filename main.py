from fastapi import FastAPI, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
import requests
from bs4 import BeautifulSoup
from transformers import pipeline
from docx import Document
import fitz
import io

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize the summarizer
summarizer = pipeline("summarization")

@app.get("/", response_class=HTMLResponse)
async def get_form():
    with open("templates/index.html") as file:
        return HTMLResponse(content=file.read())

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    if file.content_type == "text/plain":
        text = await file.read()
        text = text.decode("utf-8")
    elif file.content_type == "application/pdf":
        text = await extract_text_from_pdf(file)
    elif file.content_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        text = await extract_text_from_docx(file)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Only TXT, PDF, and DOCX files are supported.")

    if not text.strip():  # Check if text is empty
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")

    # Summarize the text
    summarized_text = generate_summary(text)
    
    # Apply Bionic Reader after summarizing
    bionic_text = process_bionic_reader(summarized_text)

    return {"bionic_text": bionic_text}

@app.post("/url")
async def fetch_url_content(url: str = Form(...)):
    try:
        # Fetch content from the URL
        response = requests.get(url)
        response.raise_for_status()
        
        # Parse and extract main text content from the HTML
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract only the main content (remove scripts, ads, navigation, etc.)
        text = extract_main_content(soup)

        if not text.strip():  # Check if extracted text is empty
            raise HTTPException(status_code=400, detail="No meaningful content found at the provided URL.")
        
        # Summarize the extracted text
        summarized_text = generate_summary(text)
        
        # Apply Bionic Reader after summarizing
        bionic_text = process_bionic_reader(summarized_text)
        
        return {"bionic_text": bionic_text}
    except requests.RequestException as e:
        raise HTTPException(status_code=400, detail="Failed to fetch the URL content.")

@app.post("/summarize")
async def summarize_text(text: str = Form(...)):
    if not text.strip():
        raise HTTPException(status_code=400, detail="Input text is empty.")
    
    # Summarize the provided text
    summarized_text = generate_summary(text)
    
    # Apply Bionic Reader after summarizing
    bionic_text = process_bionic_reader(summarized_text)

    return {"bionic_text": bionic_text}

@app.post("/convert")
async def convert_text(text: str = Form(...)):
    if not text.strip():  # Check if text is empty
        raise HTTPException(status_code=400, detail="Input text is empty.")
    
    # Summarize the text
    summarized_text = generate_summary(text)
    
    # Apply Bionic Reader after summarizing
    bionic_text = process_bionic_reader(summarized_text)

    return {"bionic_text": bionic_text}

# Helper functions

async def extract_text_from_pdf(file: UploadFile):
    try:
        text = ""
        with fitz.open(stream=await file.read(), filetype="pdf") as pdf:
            for page in pdf:
                text += page.get_text()
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error extracting text from PDF.")

async def extract_text_from_docx(file: UploadFile):
    try:
        text = ""
        contents = await file.read()
        document = Document(io.BytesIO(contents))
        for para in document.paragraphs:
            text += para.text + "\n"
        return text
    except Exception as e:
        raise HTTPException(status_code=400, detail="Error extracting text from DOCX.")

def extract_main_content(soup: BeautifulSoup) -> str:
    """
    Extracts meaningful content from the webpage by removing irrelevant parts
    such as scripts, styles, navigation, ads, etc.
    """
    # Remove unwanted tags (e.g., scripts, styles, navigation, etc.)
    for element in soup(['script', 'style', 'header', 'footer', 'nav', 'aside', 'advertisement']):
        element.decompose()

    # Get all the main textual content
    text = soup.get_text(separator=" ", strip=True)

    return text

def generate_summary(text: str) -> str:
    if not text.strip():  # Check if text is empty
        raise HTTPException(status_code=400, detail="Cannot summarize empty text.")
    
    # Ensure the text has a reasonable length for summarization
    num_words = len(text.split())
    if num_words < 30:
        return text  # If the text is too short to summarize, return it as is.

    # Dynamically adjust max_length based on text length
    max_length = 250 if num_words > 100 else 50  # Use smaller max_length for shorter texts

    # Split long text into manageable chunks (500 words per chunk)
    chunk_size = 1000  # Number of words per chunk
    chunks = [text[i:i + chunk_size] for i in range(0, len(text), chunk_size)]

    summaries = []
    for chunk in chunks:
        try:
            # Generate summary for each chunk
            summary = summarizer(chunk, max_length=max_length, min_length=30, do_sample=False)
            summaries.append(summary[0]['summary_text'])
        except Exception as e:
            # Handle any errors gracefully, e.g., skip the chunk if there's an issue
            print(f"Error summarizing chunk: {e}")

    # Combine all summaries
    return " ".join(summaries)

def process_bionic_reader(text):
    if not text.strip():  # Handle empty text gracefully
        return ""
    
    # Apply the Bionic Reader effect (split the word in half and bold the first part)
    return " ".join(f"<b>{word[:len(word) // 2]}</b>{word[len(word) // 2:]}" for word in text.split() if word)
