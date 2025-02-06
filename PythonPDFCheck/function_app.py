import azure.functions as func
import logging
from PyPDF2 import PdfReader
from io import BytesIO
import base64
import os
import uuid

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

@app.route(route="checkpdf")
def checkpdf(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        # Extract base64 encoded string from the request body
        base64_string = req.get_body().decode('utf-8')

        if not base64_string:
            return HttpResponse(
                "Please pass a base64 encoded PDF string in the request body",
                status_code=400
            )

        # Decode the base64 string
        pdf_bytes = base64.b64decode(base64_string)

    # Create a BytesIO object from the PDF bytes
        pdf_stream = BytesIO(pdf_bytes)

        # Try to read the PDF to check if it's valid
        try:
            # Check PDF header
            header = pdf_stream.read(5)
            if header != b'%PDF-':
                return func.HttpResponse("An error occurred while processing the request.",status_code=500)
            pdf_stream.seek(0)  # Reset stream position

            pdf = PdfReader(pdf_stream)
            
            # Check if PDF is encrypted/password protected
            if pdf.is_encrypted:
                return func.HttpResponse("PDF is password protected", status_code=400)

            # Check for pages
            if len(pdf.pages) == 0:
                return func.HttpResponse("No pages", status_code=400)

            # Basic metadata check
            try:
                pdf.metadata
            except:
                logging.warning("PDF metadata is corrupt or missing")
                return func.HttpResponse("PDF metadata is corrupt or missing", status_code=400)

            pdf.pages[0].extract_text()

        except Exception as e:
            return func.HttpResponse(f"Invalid or corrupt PDF file: {str(e)}", status_code=400)
        # Define the file path to save the PDF
        # generate a unique file name
        file_name = f"pdf_{uuid.uuid4()}.pdf"
        file_path = os.path.join(".", file_name)
    

        # Save the PDF file
        with open(file_path, "wb") as pdf_file:
            pdf_file.write(pdf_bytes)

        return func.HttpResponse(f"PDF file saved to {file_path}", status_code=200)

    except Exception as e:
        logging.error(f"Error processing request: {e}")
        return func.HttpResponse(
            "An error occurred while processing the request.",
            status_code=500
        )





@app.blob_trigger(arg_name="myblob", path="tenderdocs",
                               connection="Tender_STORAGE") 
def CheckPDFBlobTrigger(myblob: func.InputStream):
    logging.info(f"Python blob trigger function processed blob"
                f"Name: {myblob.name}"
                f"Blob Size: {myblob.length} bytes")

    # Read the PDF file from the blob
    pdf_bytes = myblob.read()
    # Save the pdf file
    # generate a unique file name
    # call is_pdf_valid function to check if the pdf is valid 
    # if the pdf is valid, save the pdf file
    # if the pdf is not valid, log an error message
    # and return from the function
    if not is_pdf_valid(pdf_bytes):
        logging.error(f"Invalid PDF file: {myblob.name}")
        return
    file_name = f"pdf_{uuid.uuid4()}.pdf"
    with open(file_name, "wb") as pdf_file:
        pdf_file.write(pdf_bytes)

def is_pdf_valid(pdf_bytes: bytes) -> bool:
    try:
        # Create in-memory stream
        pdf_stream = BytesIO(pdf_bytes)
        
        # Check PDF header
        header = pdf_bytes[:1024].decode('utf-8', errors='ignore')
        if not header.startswith('%PDF-'):
            logging.error("Invalid PDF header")
            return False
            
        # Attempt to read PDF structure
        reader = PdfReader(pdf_stream)
        
        # Check for encryption
        if reader.is_encrypted:
            logging.error("PDF is password protected")
            return False
            
        # Validate page structure
        try:
            page_count = len(reader.pages)
            if page_count < 1:
                logging.error("PDF has no pages")
                return False
                
            # Test access to each page
            for i in range(page_count):
                _ = reader.pages[i]
                
            # Check document metadata
            _ = reader.metadata
            
            return True
            
        except Exception as e:
            logging.error(f"PDF structure validation failed: {str(e)}")
            return False
            
    except Exception as e:
        logging.error(f"PDF validation failed: {str(e)}")
        return False