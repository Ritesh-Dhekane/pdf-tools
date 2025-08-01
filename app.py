from flask import Flask, request, send_file, jsonify
import os
import tempfile
from werkzeug.utils import secure_filename
from pypdf import PdfMerger, PdfReader, PdfWriter
import pikepdf
import fitz  # PyMuPDF

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200 MB upload limit
app.secret_key = 'your-secret-key'  # Change this for production


# --- PDF Operations ---

def merge_pdfs(files):
    merger = PdfMerger()
    for f in files:
        merger.append(f)
    temp_out = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    merger.write(temp_out.name)
    merger.close()
    temp_out.close()
    return temp_out.name

def split_pdf(file_path):
    reader = PdfReader(file_path)
    tempdir = tempfile.mkdtemp()
    output_files = []
    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        output_path = os.path.join(tempdir, f"page_{i+1}.pdf")
        with open(output_path, "wb") as f_out:
            writer.write(f_out)
        output_files.append(output_path)
    return output_files, tempdir

def compress_pdf(input_path):
    output_temp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf = pikepdf.open(input_path)
    pdf.save(output_temp.name, compression=pikepdf.Compression.jbig2, optimize_streams=True)
    pdf.close()
    output_temp.close()
    return output_temp.name

def pdf_to_images(input_path):
    tempdir = tempfile.mkdtemp()
    doc = fitz.open(input_path)
    output_files = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap()
        img_path = os.path.join(tempdir, f"page_{page_num+1}.png")
        pix.save(img_path)
        output_files.append(img_path)
    return output_files, tempdir


# --- Flask Routes ---

@app.route('/')
def index():
    return app.send_static_file('index.html')

@app.route('/api/merge', methods=['POST'])
def api_merge():
    uploaded_files = request.files.getlist("files")
    if len(uploaded_files) < 2:
        return jsonify({"error": "Upload at least two PDF files to merge."}), 400
    filepaths = []
    try:
        for f in uploaded_files:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            f.save(temp_file.name)
            filepaths.append(temp_file.name)

        merged_path = merge_pdfs(filepaths)
        return send_file(merged_path, as_attachment=True, download_name="merged.pdf")
    finally:
        for p in filepaths:
            if os.path.exists(p):
                os.remove(p)
        if 'merged_path' in locals() and os.path.exists(merged_path):
            os.remove(merged_path)

@app.route('/api/split', methods=['POST'])
def api_split():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "Upload one PDF file to split."}), 400
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        f.save(temp_file.name)
        pages, tempdir = split_pdf(temp_file.name)

        import zipfile
        zip_path = tempfile.NamedTemporaryFile(delete=False, suffix=".zip").name
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for page_file in pages:
                zipf.write(page_file, os.path.basename(page_file))

        return send_file(zip_path, as_attachment=True, download_name="split_pages.zip")
    finally:
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)
        for p in pages:
            if os.path.exists(p):
                os.remove(p)
        try:
            os.rmdir(tempdir)
        except Exception:
            pass
        if os.path.exists(zip_path):
            os.remove(zip_path)

@app.route('/api/compress', methods=['POST'])
def api_compress():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "Upload PDF file to compress."}), 400
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        f.save(temp_file.name)
        compressed_path = compress_pdf(temp_file.name)
        return send_file(compressed_path, as_attachment=True, download_name="compressed.pdf")
    finally:
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)
        if 'compressed_path' in locals() and os.path.exists(compressed_path):
            os.remove(compressed_path)

@app.route('/api/pdf2img', methods=['POST'])
def api_pdf2img():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "Upload PDF file to convert to images."}), 400
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        f.save(temp_file.name)
        images, tempdir = pdf_to_images(temp_file.name)

        import zipfile
        zip_path = tempfile.NamedTemporaryFile(delete=False, suffix=".zip").name
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for imgf in images:
                zipf.write(imgf, os.path.basename(imgf))
        return send_file(zip_path, as_attachment=True, download_name="images.zip")
    finally:
        if os.path.exists(temp_file.name):
            os.remove(temp_file.name)
        for imgf in images:
            if os.path.exists(imgf):
                os.remove(imgf)
        try:
            os.rmdir(tempdir)
        except:
            pass
        if os.path.exists(zip_path):
            os.remove(zip_path)


if __name__ == '__main__':
    app.run(debug=True)
