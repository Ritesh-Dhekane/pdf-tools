from flask import Flask, request, send_file, jsonify
import tempfile
import os
import zipfile
from werkzeug.utils import secure_filename

from pypdf import PdfMerger, PdfReader, PdfWriter
import pikepdf
import fitz  # pymupdf
from PIL import Image

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024

############################
# PDF Operation Functions
############################

def merge_pdfs(files):
    merger = PdfMerger()
    for path in files:
        merger.append(path)
    out_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    merger.write(out_file.name)
    merger.close()
    out_file.close()
    return out_file.name

def split_pdf(input_path):
    reader = PdfReader(input_path)
    out_dir = tempfile.mkdtemp()
    out_files = []
    for i, page in enumerate(reader.pages, start=1):
        writer = PdfWriter()
        writer.add_page(page)
        out_path = os.path.join(out_dir, f"page_{i}.pdf")
        with open(out_path, "wb") as f_out:
            writer.write(f_out)
        out_files.append(out_path)
    return out_files, out_dir

def compress_pdf(input_path):
    out_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pdf = pikepdf.open(input_path)
    pdf.save(out_file.name, compression=pikepdf.Compression.jbig2, optimize_streams=True)
    pdf.close()
    out_file.close()
    return out_file.name

def pdf_to_images(input_path):
    doc = fitz.open(input_path)
    out_dir = tempfile.mkdtemp()
    image_files = []
    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap()
        img_path = os.path.join(out_dir, f"page_{page_num + 1}.png")
        pix.save(img_path)
        image_files.append(img_path)
    return image_files, out_dir

def images_to_pdf(files):
    imgs = [Image.open(f).convert("RGB") for f in files]
    out_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    imgs[0].save(out_file.name, save_all=True, append_images=imgs[1:])
    [im.close() for im in imgs]
    out_file.close()
    return out_file.name

############################
# Flask Routes & API
############################

@app.route('/')
def index():
    return HTML_PAGE

@app.route('/api/merge', methods=['POST'])
def api_merge():
    uploaded_files = request.files.getlist("files")
    if len(uploaded_files) < 2:
        return jsonify({"error": "Upload at least two PDF files to merge."}), 400

    temp_files = []
    merged_path = None
    try:
        for f in uploaded_files:
            tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            f.save(tf.name)
            temp_files.append(tf.name)

        merged_path = merge_pdfs(temp_files)
        return send_file(merged_path, as_attachment=True, download_name="merged.pdf")
    finally:
        for tf in temp_files:
            if os.path.exists(tf):
                os.remove(tf)
        if merged_path and os.path.exists(merged_path):
            os.remove(merged_path)

@app.route('/api/split', methods=['POST'])
def api_split():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "Upload one PDF file to split."}), 400

    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    pages, out_dir, zip_path = [], None, None
    try:
        f.save(tf.name)
        pages, out_dir = split_pdf(tf.name)

        zip_path = tempfile.NamedTemporaryFile(delete=False, suffix=".zip").name
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for p in pages:
                zipf.write(p, os.path.basename(p))

        return send_file(zip_path, as_attachment=True, download_name="split_pages.zip")
    finally:
        if os.path.exists(tf.name):
            os.remove(tf.name)
        for p in pages:
            if os.path.exists(p):
                os.remove(p)
        if out_dir and os.path.exists(out_dir):
            try:
                os.rmdir(out_dir)
            except Exception:
                pass
        if zip_path and os.path.exists(zip_path):
            os.remove(zip_path)

@app.route('/api/compress', methods=['POST'])
def api_compress():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "Upload PDF file to compress."}), 400

    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    compressed_path = None
    try:
        f.save(tf.name)
        compressed_path = compress_pdf(tf.name)
        return send_file(compressed_path, as_attachment=True, download_name="compressed.pdf")
    finally:
        if os.path.exists(tf.name):
            os.remove(tf.name)
        if compressed_path and os.path.exists(compressed_path):
            os.remove(compressed_path)

@app.route('/api/pdf2img', methods=['POST'])
def api_pdf2img():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "Upload PDF file to convert to images."}), 400

    tf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    images, out_dir, zip_path = [], None, None
    try:
        f.save(tf.name)
        images, out_dir = pdf_to_images(tf.name)

        zip_path = tempfile.NamedTemporaryFile(delete=False, suffix=".zip").name
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for img in images:
                zipf.write(img, os.path.basename(img))

        return send_file(zip_path, as_attachment=True, download_name="pdf_images.zip")
    finally:
        if os.path.exists(tf.name):
            os.remove(tf.name)
        for img in images:
            if os.path.exists(img):
                os.remove(img)
        if out_dir and os.path.exists(out_dir):
            try:
                os.rmdir(out_dir)
            except Exception:
                pass
        if zip_path and os.path.exists(zip_path):
            os.remove(zip_path)

@app.route('/api/img2pdf', methods=['POST'])
def api_img2pdf():
    uploaded_files = request.files.getlist("images")
    if len(uploaded_files) < 1:
        return jsonify({"error": "Upload at least one image (JPG, PNG)."}), 400

    temp_imgs = []
    out_pdf = None
    try:
        for f in uploaded_files:
            ext = os.path.splitext(f.filename)[1].lower()
            tf = tempfile.NamedTemporaryFile(delete=False, suffix=ext if ext in [".jpg", ".jpeg", ".png"] else ".png")
            f.save(tf.name)
            temp_imgs.append(tf.name)

        out_pdf = images_to_pdf(temp_imgs)
        return send_file(out_pdf, as_attachment=True, download_name="images.pdf")
    finally:
        for tf in temp_imgs:
            if os.path.exists(tf):
                os.remove(tf)
        if out_pdf and os.path.exists(out_pdf):
            os.remove(out_pdf)

############################
# Embedded HTML + CSS + JS
############################

HTML_PAGE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <title>Simple PDF Tool</title>
  <meta name="viewport" content="width=device-width, initial-scale=1" />
  <style>
    body {
      font-family: Arial, sans-serif;
      max-width: 720px;
      margin: auto;
      padding: 1rem;
      background: #f9f9f9;
      color: #222;
    }
    header {
      text-align: center;
      margin-bottom: 2rem;
    }
    #operations {
      text-align: center;
      margin-bottom: 2rem;
    }
    .op-btn {
      margin: 0 0.5rem;
      padding: 0.6rem 1.2rem;
      font-size: 1.1rem;
      cursor: pointer;
    }
    #upload-section {
      background: white;
      border: 1px solid #ccc;
      padding: 1.5rem 2rem;
      border-radius: 6px;
    }
    .hidden {
      display: none;
    }
    label.btn-choose-file {
      background-color: #007bff;
      color: white;
      padding: 0.5rem 1rem;
      cursor: pointer;
      border-radius: 4px;
      display: inline-block;
      font-weight: 600;
      user-select: none;
      margin-bottom: 1rem;
    }
    label.btn-choose-file:hover {
      background-color: #0056b3;
    }
    input[type="file"] {
      display: none;
    }
    button[type="submit"], #cancel-btn {
      margin-right: 1rem;
      padding: 0.5rem 1.2rem;
      font-size: 1rem;
      cursor: pointer;
    }
    #status {
      margin-top: 1rem;
      font-weight: bold;
    }
    #file-name {
      margin-left: 10px;
      font-style: italic;
    }
  </style>
</head>
<body>
  <header>
    <h1>Simple PDF Tool</h1>
    <p>Merge, Split, Compress PDFs, Convert PDF Images, or Images to PDF</p>
  </header>
  <main>
    <section id="operations">
      <button data-op="merge" class="op-btn">Merge PDFs</button>
      <button data-op="split" class="op-btn">Split PDF</button>
      <button data-op="compress" class="op-btn">Compress PDF</button>
      <button data-op="pdf2img" class="op-btn">PDF to Images</button>
      <button data-op="img2pdf" class="op-btn">Images to PDF</button>
    </section>
    <section id="upload-section" class="hidden">
      <h2 id="op-title"></h2>
      <form id="upload-form" enctype="multipart/form-data">
        <label for="pdf-file" class="btn-choose-file" id="choose-label">Choose File(s)</label>
        <input type="file" id="pdf-file" name="file" accept="application/pdf" required />
        <span id="file-name">No file chosen</span>
        <br/><br/>
        <button type="submit" id="run-button" disabled>Run Operation</button>
        <button type="button" id="cancel-btn">Cancel</button>
      </form>
      <div id="status"></div>
    </section>
  </main>
  <script>
    const ops = {
      merge: {
        title: "Merge PDFs",
        multipleFiles: true,
        accept: "application/pdf",
        api: "/api/merge",
        param: "files"
      },
      split: {
        title: "Split PDF",
        multipleFiles: false,
        accept: "application/pdf",
        api: "/api/split",
        param: "file"
      },
      compress: {
        title: "Compress PDF",
        multipleFiles: false,
        accept: "application/pdf",
        api: "/api/compress",
        param: "file"
      },
      pdf2img: {
        title: "Convert PDF to Images",
        multipleFiles: false,
        accept: "application/pdf",
        api: "/api/pdf2img",
        param: "file"
      },
      img2pdf: {
        title: "Images to PDF",
        multipleFiles: true,
        accept: ".jpg,.jpeg,.png,.bmp,.tiff",
        api: "/api/img2pdf",
        param: "images"
      }
    };
    const operationsSection = document.getElementById("operations");
    const uploadSection = document.getElementById("upload-section");
    const uploadForm = document.getElementById("upload-form");
    const opTitle = document.getElementById("op-title");
    const statusDiv = document.getElementById("status");
    const cancelBtn = document.getElementById("cancel-btn");
    const fileInput = document.getElementById("pdf-file");
    const fileNameSpan = document.getElementById("file-name");
    const runButton = document.getElementById("run-button");
    const chooseLabel = document.getElementById("choose-label");
    let currentOp = null;
    operationsSection.addEventListener("click", (e) => {
      if (e.target.tagName !== "BUTTON") return;
      const opKey = e.target.dataset.op;
      if (!ops[opKey]) return;
      currentOp = ops[opKey];
      showUploadForm(currentOp);
    });
    cancelBtn.addEventListener("click", () => {
      resetForm();
    });
    fileInput.addEventListener("change", () => {
      if (fileInput.files.length > 0) {
        let names = [];
        for(let i = 0; i < fileInput.files.length; i++) {
          names.push(fileInput.files[i].name);
        }
        fileNameSpan.textContent = names.join(", ");
        runButton.disabled = false;
      } else {
        fileNameSpan.textContent = "No file chosen";
        runButton.disabled = true;
      }
    });
    function showUploadForm(op) {
      uploadSection.classList.remove("hidden");
      operationsSection.classList.add("hidden");
      opTitle.textContent = op.title;
      statusDiv.textContent = "";
      fileInput.value = "";
      fileNameSpan.textContent = "No file chosen";
      runButton.disabled = true;
      fileInput.accept = op.accept;
      chooseLabel.textContent = op.multipleFiles ? "Choose File(s)" : "Choose File";
      // Reset multiple attribute and input name
      if(op.multipleFiles) {
        fileInput.setAttribute("multiple", "");
      } else {
        fileInput.removeAttribute("multiple");
      }
    }
    function resetForm() {
      currentOp = null;
      uploadSection.classList.add("hidden");
      operationsSection.classList.remove("hidden");
      statusDiv.textContent = "";
      fileInput.value = "";
      fileNameSpan.textContent = "No file chosen";
      runButton.disabled = true;
      uploadForm.reset();
    }
    uploadForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      if (!currentOp) return;
      if (fileInput.files.length === 0) {
        statusDiv.style.color = "red";
        statusDiv.textContent = "Please choose file(s) before running.";
        return;
      }
      const formData = new FormData();
      if(currentOp.multipleFiles) {
        for(let f of fileInput.files) {
          formData.append(currentOp.param, f);
        }
      } else {
        formData.append(currentOp.param, fileInput.files[0]);
      }
      statusDiv.style.color = "black";
      statusDiv.textContent = "Processing... please wait.";
      try {
        const response = await fetch(currentOp.api, {
          method: "POST",
          body: formData,
        });
        if (!response.ok) {
          const errData = await response.json();
          statusDiv.style.color = "red";
          statusDiv.textContent = `Error: ${errData.error || "Unknown error"}`;
          return;
        }
        const blob = await response.blob();
        let filename = "output.pdf";
        const disposition = response.headers.get("content-disposition");
        if (disposition && disposition.includes("filename=")) {
          filename = disposition
            .split("filename=")[1]
            .split(";")[0]
            .replace(/"/g, "");
        }
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);
        statusDiv.style.color = "green";
        statusDiv.textContent = "Download started.";
      } catch (err) {
        statusDiv.style.color = "red";
        statusDiv.textContent = "An error occurred: " + err.message;
      }
    });
  </script>
</body>
</html>
"""

if __name__ == '__main__':
    app.run(debug=True)
