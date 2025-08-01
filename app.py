import sys
import os
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# PDF Libraries
from pypdf import PdfReader, PdfWriter, PdfMerger
from pdf2docx import Converter
from PIL import Image
import pikepdf
import fitz  # pymupdf

##############################
# Core PDF Processing Functions
##############################

def merge_pdfs(pdf_list, output):
    merger = PdfMerger()
    for pdf in pdf_list:
        merger.append(pdf)
    merger.write(output)
    merger.close()

def split_pdf(input_pdf, output_folder):
    reader = PdfReader(input_pdf)
    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)
        with open(os.path.join(output_folder, f"page_{i+1}.pdf"), "wb") as f:
            writer.write(f)

def compress_pdf(input_pdf, output_pdf):
    pdf = pikepdf.open(input_pdf)
    pdf.save(output_pdf, compression=pikepdf.Compression.jbig2, optimize_streams=True)
    pdf.close()

def pdf_to_images(input_pdf, output_folder):
    doc = fitz.open(input_pdf)
    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap()
        pix.save(os.path.join(output_folder, f"page_{page_num+1}.png"))

def images_to_pdf(image_paths, output_pdf):
    images = [Image.open(img).convert("RGB") for img in image_paths]
    images[0].save(output_pdf, save_all=True, append_images=images[1:])

def pdf_to_word(input_pdf, output_docx):
    cv = Converter(input_pdf)
    cv.convert(output_docx, start=0, end=None)
    cv.close()

def rotate_pdf(input_pdf, output_pdf, angle):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    for page in reader.pages:
        page.rotate(angle)
        writer.add_page(page)
    with open(output_pdf, "wb") as f:
        writer.write(f)

def extract_text(input_pdf, output_txt):
    reader = PdfReader(input_pdf)
    with open(output_txt, "w", encoding="utf-8") as f:
        for page in reader.pages:
            text = page.extract_text()
            if text:
                f.write(text)

def add_watermark(input_pdf, watermark_pdf, output_pdf):
    reader = PdfReader(input_pdf)
    watermark = PdfReader(watermark_pdf).pages[0]
    writer = PdfWriter()
    for page in reader.pages:
        page.merge_page(watermark)
        writer.add_page(page)
    with open(output_pdf, "wb") as f:
        writer.write(f)

def protect_pdf(input_pdf, output_pdf, password):
    reader = PdfReader(input_pdf)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    writer.encrypt(password)
    with open(output_pdf, "wb") as f:
        writer.write(f)

def unlock_pdf(input_pdf, output_pdf, password):
    reader = PdfReader(input_pdf, password)
    writer = PdfWriter()
    for page in reader.pages:
        writer.add_page(page)
    with open(output_pdf, "wb") as f:
        writer.write(f)

def repair_pdf(input_pdf, output_pdf):
    pdf = pikepdf.open(input_pdf, repair=True)
    pdf.save(output_pdf)
    pdf.close()

##########################
# GUI CODE USING TKINTER
##########################

def main():
    root = tk.Tk()
    root.title("PDF Tool GUI")
    root.geometry("750x600")

    tabControl = ttk.Notebook(root)

    # --- Merge Tab ---
    tab_merge = ttk.Frame(tabControl)
    tabControl.add(tab_merge, text='Merge PDFs')

    merge_files = []

    def add_merge_files():
        files = filedialog.askopenfilenames(title="Select PDFs to merge", filetypes=[("PDF files","*.pdf")])
        if files:
            merge_files.extend(files)
            list_merge.delete(0, tk.END)
            for f in merge_files:
                list_merge.insert(tk.END, f)

    def clear_merge_files():
        merge_files.clear()
        list_merge.delete(0, tk.END)

    def run_merge():
        if len(merge_files) < 2:
            messagebox.showerror("Error", "Select at least two PDF files to merge.")
            return
        out_path = filedialog.asksaveasfilename(title="Save merged PDF as", defaultextension=".pdf", filetypes=[("PDF files","*.pdf")])
        if not out_path:
            return
        try:
            merge_pdfs(merge_files, out_path)
            messagebox.showinfo("Success", f"Merged PDF saved to\n{out_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    ttk.Button(tab_merge, text="Add PDF Files", command=add_merge_files).pack(pady=5)
    list_merge = tk.Listbox(tab_merge, height=8, width=75)
    list_merge.pack(padx=10)
    ttk.Button(tab_merge, text="Clear Files", command=clear_merge_files).pack(pady=5)
    ttk.Button(tab_merge, text="Merge and Save", command=run_merge).pack(pady=10)

    # --- Split Tab ---
    tab_split = ttk.Frame(tabControl)
    tabControl.add(tab_split, text='Split PDF')

    split_pdf_path = tk.StringVar()
    split_output_dir = tk.StringVar()

    def browse_split_pdf():
        p = filedialog.askopenfilename(title="Select PDF to split", filetypes=[("PDF files", "*.pdf")])
        if p:
            split_pdf_path.set(p)

    def browse_split_output():
        d = filedialog.askdirectory(title="Select output folder for split pages")
        if d:
            split_output_dir.set(d)

    def run_split():
        pdf_path = split_pdf_path.get()
        output_dir = split_output_dir.get()
        if not pdf_path or not output_dir:
            messagebox.showerror("Error", "Select both input PDF and output folder.")
            return
        try:
            split_pdf(pdf_path, output_dir)
            messagebox.showinfo("Success", f"PDF split into pages saved in:\n{output_dir}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    ttk.Label(tab_split, text="PDF to split:").pack(anchor='w', padx=10, pady=(10,0))
    ttk.Entry(tab_split, textvariable=split_pdf_path, width=75).pack(padx=10)
    ttk.Button(tab_split, text="Browse PDF", command=browse_split_pdf).pack(padx=10, pady=5)

    ttk.Label(tab_split, text="Output folder for pages:").pack(anchor='w', padx=10)
    ttk.Entry(tab_split, textvariable=split_output_dir, width=75).pack(padx=10)
    ttk.Button(tab_split, text="Browse Folder", command=browse_split_output).pack(padx=10, pady=5)

    ttk.Button(tab_split, text="Split PDF", command=run_split).pack(pady=10)

    # --- Compress Tab ---
    tab_compress = ttk.Frame(tabControl)
    tabControl.add(tab_compress, text='Compress PDF')

    compress_pdf_path = tk.StringVar()
    compress_output_path = tk.StringVar()

    def browse_compress_pdf():
        p = filedialog.askopenfilename(title="Select PDF to compress", filetypes=[("PDF files", "*.pdf")])
        if p:
            compress_pdf_path.set(p)

    def browse_compress_output():
        p = filedialog.asksaveasfilename(title="Save compressed PDF as", defaultextension=".pdf", filetypes=[("PDF files","*.pdf")])
        if p:
            compress_output_path.set(p)

    def run_compress():
        inp = compress_pdf_path.get()
        out = compress_output_path.get()
        if not inp or not out:
            messagebox.showerror("Error", "Select input PDF and output file.")
            return
        try:
            compress_pdf(inp, out)
            messagebox.showinfo("Success", f"Compressed PDF saved to\n{out}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    ttk.Label(tab_compress, text="PDF to compress:").pack(anchor='w', padx=10, pady=(10,0))
    ttk.Entry(tab_compress, textvariable=compress_pdf_path, width=75).pack(padx=10)
    ttk.Button(tab_compress, text="Browse PDF", command=browse_compress_pdf).pack(padx=10, pady=5)

    ttk.Label(tab_compress, text="Output compressed PDF:").pack(anchor='w', padx=10)
    ttk.Entry(tab_compress, textvariable=compress_output_path, width=75).pack(padx=10)
    ttk.Button(tab_compress, text="Save As", command=browse_compress_output).pack(padx=10, pady=5)

    ttk.Button(tab_compress, text="Compress PDF", command=run_compress).pack(pady=10)

    # --- PDF to Word Tab ---
    tab_pdf2word = ttk.Frame(tabControl)
    tabControl.add(tab_pdf2word, text='PDF to Word')

    pdf2word_input = tk.StringVar()
    pdf2word_output = tk.StringVar()

    def browse_pdf2word_input():
        p = filedialog.askopenfilename(title="Select PDF to convert to Word", filetypes=[("PDF files", "*.pdf")])
        if p:
            pdf2word_input.set(p)

    def browse_pdf2word_output():
        p = filedialog.asksaveasfilename(title="Save Word doc as", defaultextension=".docx", filetypes=[("Word files","*.docx")])
        if p:
            pdf2word_output.set(p)

    def run_pdf2word():
        inp = pdf2word_input.get()
        out = pdf2word_output.get()
        if not inp or not out:
            messagebox.showerror("Error", "Select input PDF and output DOCX file.")
            return
        try:
            pdf_to_word(inp, out)
            messagebox.showinfo("Success", f"Word document saved to\n{out}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    ttk.Label(tab_pdf2word, text="PDF to convert:").pack(anchor='w', padx=10, pady=(10,0))
    ttk.Entry(tab_pdf2word, textvariable=pdf2word_input, width=75).pack(padx=10)
    ttk.Button(tab_pdf2word, text="Browse PDF", command=browse_pdf2word_input).pack(padx=10, pady=5)

    ttk.Label(tab_pdf2word, text="Output Word doc:").pack(anchor='w', padx=10)
    ttk.Entry(tab_pdf2word, textvariable=pdf2word_output, width=75).pack(padx=10)
    ttk.Button(tab_pdf2word, text="Save As", command=browse_pdf2word_output).pack(padx=10, pady=5)

    ttk.Button(tab_pdf2word, text="Convert to Word", command=run_pdf2word).pack(pady=10)

    # --- Rotate PDF Tab ---
    tab_rotate = ttk.Frame(tabControl)
    tabControl.add(tab_rotate, text='Rotate PDF')

    rotate_pdf_input = tk.StringVar()
    rotate_pdf_output = tk.StringVar()
    rotate_angle = tk.StringVar(value="90")

    def browse_rotate_input():
        p = filedialog.askopenfilename(title="Select PDF to rotate", filetypes=[("PDF files", "*.pdf")])
        if p:
            rotate_pdf_input.set(p)

    def browse_rotate_output():
        p = filedialog.asksaveasfilename(title="Save rotated PDF as", defaultextension=".pdf", filetypes=[("PDF files","*.pdf")])
        if p:
            rotate_pdf_output.set(p)

    def run_rotate():
        inp = rotate_pdf_input.get()
        out = rotate_pdf_output.get()
        try:
            angle = int(rotate_angle.get())
            if angle % 90 != 0:
                raise ValueError("Angle must be a multiple of 90")
        except Exception as e:
            messagebox.showerror("Error", f"Invalid angle: {e}")
            return
        if not inp or not out:
            messagebox.showerror("Error", "Select input PDF and output PDF.")
            return
        try:
            rotate_pdf(inp, out, angle)
            messagebox.showinfo("Success", f"Rotated PDF saved to\n{out}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    ttk.Label(tab_rotate, text="PDF to rotate:").pack(anchor='w', padx=10, pady=(10,0))
    ttk.Entry(tab_rotate, textvariable=rotate_pdf_input, width=75).pack(padx=10)
    ttk.Button(tab_rotate, text="Browse PDF", command=browse_rotate_input).pack(padx=10, pady=5)

    ttk.Label(tab_rotate, text="Output rotated PDF:").pack(anchor='w', padx=10)
    ttk.Entry(tab_rotate, textvariable=rotate_pdf_output, width=75).pack(padx=10)
    ttk.Button(tab_rotate, text="Save As", command=browse_rotate_output).pack(padx=10, pady=5)

    ttk.Label(tab_rotate, text="Rotation angle (degrees, multiple of 90):").pack(anchor='w', padx=10)
    ttk.Entry(tab_rotate, textvariable=rotate_angle, width=10).pack(padx=10, pady=5)

    ttk.Button(tab_rotate, text="Rotate PDF", command=run_rotate).pack(pady=10)

    # --- Extract Text Tab ---
    tab_extract = ttk.Frame(tabControl)
    tabControl.add(tab_extract, text='Extract Text')

    extract_pdf_input = tk.StringVar()
    extract_txt_output = tk.StringVar()

    def browse_extract_pdf():
        p = filedialog.askopenfilename(title="Select PDF to extract text", filetypes=[("PDF files", "*.pdf")])
        if p:
            extract_pdf_input.set(p)

    def browse_extract_txt():
        p = filedialog.asksaveasfilename(title="Save extracted text as", defaultextension=".txt", filetypes=[("Text files","*.txt")])
        if p:
            extract_txt_output.set(p)

    def run_extract_text():
        inp = extract_pdf_input.get()
        out = extract_txt_output.get()
        if not inp or not out:
            messagebox.showerror("Error", "Select input PDF and output TXT file.")
            return
        try:
            extract_text(inp, out)
            messagebox.showinfo("Success", f"Extracted text saved to\n{out}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    ttk.Label(tab_extract, text="PDF to extract text from:").pack(anchor='w', padx=10, pady=(10,0))
    ttk.Entry(tab_extract, textvariable=extract_pdf_input, width=75).pack(padx=10)
    ttk.Button(tab_extract, text="Browse PDF", command=browse_extract_pdf).pack(padx=10, pady=5)

    ttk.Label(tab_extract, text="Output text file:").pack(anchor='w', padx=10)
    ttk.Entry(tab_extract, textvariable=extract_txt_output, width=75).pack(padx=10)
    ttk.Button(tab_extract, text="Save As", command=browse_extract_txt).pack(padx=10, pady=5)

    ttk.Button(tab_extract, text="Extract Text", command=run_extract_text).pack(pady=10)

    # --- Watermark Tab ---
    tab_watermark = ttk.Frame(tabControl)
    tabControl.add(tab_watermark, text='Add Watermark')

    watermark_pdf_input = tk.StringVar()
    watermark_stamp_input = tk.StringVar()
    watermark_output = tk.StringVar()

    def browse_watermark_pdf():
        p = filedialog.askopenfilename(title="Select PDF to watermark", filetypes=[("PDF files", "*.pdf")])
        if p:
            watermark_pdf_input.set(p)

    def browse_watermark_stamp():
        p = filedialog.askopenfilename(title="Select watermark PDF", filetypes=[("PDF files", "*.pdf")])
        if p:
            watermark_stamp_input.set(p)

    def browse_watermark_output():
        p = filedialog.asksaveasfilename(title="Save watermarked PDF as", defaultextension=".pdf", filetypes=[("PDF files","*.pdf")])
        if p:
            watermark_output.set(p)

    def run_watermark():
        inp = watermark_pdf_input.get()
        stamp = watermark_stamp_input.get()
        out = watermark_output.get()
        if not inp or not stamp or not out:
            messagebox.showerror("Error", "Select input PDF, watermark PDF and output file.")
            return
        try:
            add_watermark(inp, stamp, out)
            messagebox.showinfo("Success", f"Watermarked PDF saved to\n{out}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    ttk.Label(tab_watermark, text="PDF to watermark:").pack(anchor='w', padx=10, pady=(10,0))
    ttk.Entry(tab_watermark, textvariable=watermark_pdf_input, width=75).pack(padx=10)
    ttk.Button(tab_watermark, text="Browse PDF", command=browse_watermark_pdf).pack(padx=10, pady=5)

    ttk.Label(tab_watermark, text="Watermark PDF:").pack(anchor='w', padx=10)
    ttk.Entry(tab_watermark, textvariable=watermark_stamp_input, width=75).pack(padx=10)
    ttk.Button(tab_watermark, text="Browse watermark PDF", command=browse_watermark_stamp).pack(padx=10, pady=5)

    ttk.Label(tab_watermark, text="Output PDF file:").pack(anchor='w', padx=10)
    ttk.Entry(tab_watermark, textvariable=watermark_output, width=75).pack(padx=10)
    ttk.Button(tab_watermark, text="Save As", command=browse_watermark_output).pack(padx=10, pady=5)

    ttk.Button(tab_watermark, text="Add Watermark", command=run_watermark).pack(pady=10)

    # --- Protect PDF Tab ---
    tab_protect = ttk.Frame(tabControl)
    tabControl.add(tab_protect, text='Protect PDF')

    protect_pdf_input = tk.StringVar()
    protect_output = tk.StringVar()
    protect_password = tk.StringVar()

    def browse_protect_pdf():
        p = filedialog.askopenfilename(title="Select PDF to protect", filetypes=[("PDF files", "*.pdf")])
        if p:
            protect_pdf_input.set(p)

    def browse_protect_output():
        p = filedialog.asksaveasfilename(title="Save protected PDF as", defaultextension=".pdf", filetypes=[("PDF files","*.pdf")])
        if p:
            protect_output.set(p)

    def run_protect():
        inp = protect_pdf_input.get()
        out = protect_output.get()
        pwd = protect_password.get()
        if not inp or not out or not pwd:
            messagebox.showerror("Error", "Select input PDF, output file, and enter a password.")
            return
        try:
            protect_pdf(inp, out, pwd)
            messagebox.showinfo("Success", f"Protected PDF saved to\n{out}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    ttk.Label(tab_protect, text="PDF to protect:").pack(anchor='w', padx=10, pady=(10,0))
    ttk.Entry(tab_protect, textvariable=protect_pdf_input, width=75).pack(padx=10)
    ttk.Button(tab_protect, text="Browse PDF", command=browse_protect_pdf).pack(padx=10, pady=5)

    ttk.Label(tab_protect, text="Output PDF file:").pack(anchor='w', padx=10)
    ttk.Entry(tab_protect, textvariable=protect_output, width=75).pack(padx=10)
    ttk.Button(tab_protect, text="Save As", command=browse_protect_output).pack(padx=10, pady=5)

    ttk.Label(tab_protect, text="Password:").pack(anchor='w', padx=10)
    ttk.Entry(tab_protect, textvariable=protect_password, width=30, show="*").pack(padx=10, pady=5)

    ttk.Button(tab_protect, text="Protect PDF", command=run_protect).pack(pady=10)

    # --- Unlock PDF Tab ---
    tab_unlock = ttk.Frame(tabControl)
    tabControl.add(tab_unlock, text='Unlock PDF')

    unlock_pdf_input = tk.StringVar()
    unlock_output = tk.StringVar()
    unlock_password = tk.StringVar()

    def browse_unlock_pdf():
        p = filedialog.askopenfilename(title="Select PDF to unlock", filetypes=[("PDF files", "*.pdf")])
        if p:
            unlock_pdf_input.set(p)

    def browse_unlock_output():
        p = filedialog.asksaveasfilename(title="Save unlocked PDF as", defaultextension=".pdf", filetypes=[("PDF files","*.pdf")])
        if p:
            unlock_output.set(p)

    def run_unlock():
        inp = unlock_pdf_input.get()
        out = unlock_output.get()
        pwd = unlock_password.get()
        if not inp or not out or not pwd:
            messagebox.showerror("Error", "Select input PDF, output file, and enter the password.")
            return
        try:
            unlock_pdf(inp, out, pwd)
            messagebox.showinfo("Success", f"Unlocked PDF saved to\n{out}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    ttk.Label(tab_unlock, text="PDF to unlock:").pack(anchor='w', padx=10, pady=(10,0))
    ttk.Entry(tab_unlock, textvariable=unlock_pdf_input, width=75).pack(padx=10)
    ttk.Button(tab_unlock, text="Browse PDF", command=browse_unlock_pdf).pack(padx=10, pady=5)

    ttk.Label(tab_unlock, text="Output PDF file:").pack(anchor='w', padx=10)
    ttk.Entry(tab_unlock, textvariable=unlock_output, width=75).pack(padx=10)
    ttk.Button(tab_unlock, text="Save As", command=browse_unlock_output).pack(padx=10, pady=5)

    ttk.Label(tab_unlock, text="Password:").pack(anchor='w', padx=10)
    ttk.Entry(tab_unlock, textvariable=unlock_password, width=30, show="*").pack(padx=10, pady=5)

    ttk.Button(tab_unlock, text="Unlock PDF", command=run_unlock).pack(pady=10)

    # --- Repair PDF Tab ---
    tab_repair = ttk.Frame(tabControl)
    tabControl.add(tab_repair, text='Repair PDF')

    repair_pdf_input = tk.StringVar()
    repair_output = tk.StringVar()

    def browse_repair_pdf():
        p = filedialog.askopenfilename(title="Select PDF to repair", filetypes=[("PDF files", "*.pdf")])
        if p:
            repair_pdf_input.set(p)

    def browse_repair_output():
        p = filedialog.asksaveasfilename(title="Save repaired PDF as", defaultextension=".pdf", filetypes=[("PDF files","*.pdf")])
        if p:
            repair_output.set(p)

    def run_repair():
        inp = repair_pdf_input.get()
        out = repair_output.get()
        if not inp or not out:
            messagebox.showerror("Error", "Select input PDF and output file.")
            return
        try:
            repair_pdf(inp, out)
            messagebox.showinfo("Success", f"Repaired PDF saved to\n{out}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    ttk.Label(tab_repair, text="PDF to repair:").pack(anchor='w', padx=10, pady=(10,0))
    ttk.Entry(tab_repair, textvariable=repair_pdf_input, width=75).pack(padx=10)
    ttk.Button(tab_repair, text="Browse PDF", command=browse_repair_pdf).pack(padx=10, pady=5)

    ttk.Label(tab_repair, text="Output PDF file:").pack(anchor='w', padx=10)
    ttk.Entry(tab_repair, textvariable=repair_output, width=75).pack(padx=10)
    ttk.Button(tab_repair, text="Save As", command=browse_repair_output).pack(padx=10, pady=5)

    ttk.Button(tab_repair, text="Repair PDF", command=run_repair).pack(pady=10)

    # --- PDF to Images Tab ---
    tab_pdf2img = ttk.Frame(tabControl)
    tabControl.add(tab_pdf2img, text='PDF to Images')

    pdf2img_input = tk.StringVar()
    pdf2img_output_dir = tk.StringVar()

    def browse_pdf2img_input():
        p = filedialog.askopenfilename(title="Select PDF to convert to images", filetypes=[("PDF files", "*.pdf")])
        if p:
            pdf2img_input.set(p)

    def browse_pdf2img_output():
        d = filedialog.askdirectory(title="Select folder to save images")
        if d:
            pdf2img_output_dir.set(d)

    def run_pdf2img():
        inp = pdf2img_input.get()
        out = pdf2img_output_dir.get()
        if not inp or not out:
            messagebox.showerror("Error", "Select input PDF and output folder.")
            return
        try:
            pdf_to_images(inp, out)
            messagebox.showinfo("Success", f"Images saved in\n{out}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    ttk.Label(tab_pdf2img, text="PDF to convert:").pack(anchor='w', padx=10, pady=(10,0))
    ttk.Entry(tab_pdf2img, textvariable=pdf2img_input, width=75).pack(padx=10)
    ttk.Button(tab_pdf2img, text="Browse PDF", command=browse_pdf2img_input).pack(padx=10, pady=5)

    ttk.Label(tab_pdf2img, text="Output folder for images:").pack(anchor='w', padx=10)
    ttk.Entry(tab_pdf2img, textvariable=pdf2img_output_dir, width=75).pack(padx=10)
    ttk.Button(tab_pdf2img, text="Browse Folder", command=browse_pdf2img_output).pack(padx=10, pady=5)

    ttk.Button(tab_pdf2img, text="Convert to Images", command=run_pdf2img).pack(pady=10)

    # --- Images to PDF Tab ---
    tab_img2pdf = ttk.Frame(tabControl)
    tabControl.add(tab_img2pdf, text='Images to PDF')

    img2pdf_files = []

    def add_img2pdf_files():
        files = filedialog.askopenfilenames(title="Select images to convert", filetypes=[("Image files","*.jpg *.jpeg *.png *.bmp *.tiff")])
        if files:
            img2pdf_files.extend(files)
            list_imgs.delete(0, tk.END)
            for f in img2pdf_files:
                list_imgs.insert(tk.END, f)

    def clear_img2pdf_files():
        img2pdf_files.clear()
        list_imgs.delete(0, tk.END)

    def run_img2pdf():
        if not img2pdf_files:
            messagebox.showerror("Error", "Select at least one image.")
            return
        out_path = filedialog.asksaveasfilename(title="Save as PDF", defaultextension=".pdf", filetypes=[("PDF files","*.pdf")])
        if not out_path:
            return
        try:
            images_to_pdf(img2pdf_files, out_path)
            messagebox.showinfo("Success", f"PDF saved to\n{out_path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    ttk.Button(tab_img2pdf, text="Add Image Files", command=add_img2pdf_files).pack(pady=5)
    list_imgs = tk.Listbox(tab_img2pdf, height=8, width=75)
    list_imgs.pack(padx=10)
    ttk.Button(tab_img2pdf, text="Clear Files", command=clear_img2pdf_files).pack(pady=5)
    ttk.Button(tab_img2pdf, text="Convert Images to PDF", command=run_img2pdf).pack(pady=10)

    # Pack tabs
    tabControl.pack(expand=1, fill="both")

    root.mainloop()

if __name__ == "__main__":
    # If the script is called with CLI args, run CLI commands:
    if len(sys.argv) > 1:
        cmd = sys.argv[1].lower()
        args = sys.argv[2:]
        try:
            if cmd == "merge":
                if len(args) < 3:
                    print("Usage: merge pdf1 pdf2 ... output.pdf")
                    sys.exit(1)
                merge_pdfs(args[:-1], args[-1])
            elif cmd == "split":
                if len(args) != 2:
                    print("Usage: split input.pdf output_folder/")
                    sys.exit(1)
                split_pdf(args[0], args[1])
            elif cmd == "compress":
                if len(args) != 2:
                    print("Usage: compress input.pdf output.pdf")
                    sys.exit(1)
                compress_pdf(args[0], args[1])
            elif cmd == "pdf2img":
                if len(args) != 2:
                    print("Usage: pdf2img input.pdf output_folder/")
                    sys.exit(1)
                pdf_to_images(args[0], args[1])
            elif cmd == "img2pdf":
                if len(args) < 2:
                    print("Usage: img2pdf img1.jpg img2.png ... output.pdf")
                    sys.exit(1)
                images_to_pdf(args[:-1], args[-1])
            elif cmd == "pdf2word":
                if len(args) != 2:
                    print("Usage: pdf2word input.pdf output.docx")
                    sys.exit(1)
                pdf_to_word(args[0], args[1])
            elif cmd == "rotate":
                if len(args) != 3:
                    print("Usage: rotate input.pdf output.pdf angle")
                    sys.exit(1)
                rotate_pdf(args[0], args[1], int(args[2]))
            elif cmd == "extract":
                if len(args) != 2:
                    print("Usage: extract input.pdf output.txt")
                    sys.exit(1)
                extract_text(args[0], args[1])
            elif cmd == "watermark":
                if len(args) != 3:
                    print("Usage: watermark input.pdf watermark.pdf output.pdf")
                    sys.exit(1)
                add_watermark(args[0], args[1], args[2])
            elif cmd == "protect":
                if len(args) != 3:
                    print("Usage: protect input.pdf output.pdf password")
                    sys.exit(1)
                protect_pdf(args[0], args[1], args[2])
            elif cmd == "unlock":
                if len(args) != 3:
                    print("Usage: unlock input.pdf output.pdf password")
                    sys.exit(1)
                unlock_pdf(args[0], args[1], args[2])
            elif cmd == "repair":
                if len(args) != 2:
                    print("Usage: repair input.pdf output.pdf")
                    sys.exit(1)
                repair_pdf(args[0], args[1])
            else:
                print("Unknown command.")
        except Exception as e:
            print("Error:", e)
        sys.exit()
    else:
        # Run the GUI if no CLI command given
        main()
from flask import Flask, request, send_file, jsonify, render_template
import os
import tempfile
from werkzeug.utils import secure_filename
from pypdf import PdfReader, PdfWriter, PdfMerger
import pikepdf
import fitz  # PyMuPDF

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # max upload size 200MB

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

@app.route('/')
def index():
    # Serve the frontend
    return app.send_static_file('index.html')

@app.route('/api/merge', methods=['POST'])
def api_merge():
    uploaded_files = request.files.getlist("files")
    if len(uploaded_files) < 2:
        return jsonify({"error": "Upload at least two PDF files to merge."}), 400
    filepaths = []
    try:
        for f in uploaded_files:
            filename = secure_filename(f.filename)
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
            f.save(temp_file.name)
            filepaths.append(temp_file.name)

        merged_path = merge_pdfs(filepaths)
        return send_file(merged_path, as_attachment=True, download_name="merged.pdf")
    finally:
        # Clean up temp files
        for p in filepaths:
            if os.path.exists(p): os.remove(p)
        if 'merged_path' in locals() and os.path.exists(merged_path):
            os.remove(merged_path)

@app.route('/api/split', methods=['POST'])
def api_split():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "Upload one PDF file to split."}), 400
    filename = secure_filename(f.filename)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        f.save(temp_file.name)
        pages, tempdir = split_pdf(temp_file.name)
        # For demo, just zip and send all pages
        import zipfile
        zip_path = tempfile.NamedTemporaryFile(delete=False, suffix=".zip").name
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for page_file in pages:
                zipf.write(page_file, os.path.basename(page_file))

        return send_file(zip_path, as_attachment=True, download_name="split_pages.zip")
    finally:
        if os.path.exists(temp_file.name): os.remove(temp_file.name)
        for p in pages:
            if os.path.exists(p): os.remove(p)
        if os.path.exists(tempdir):
            try:
                os.rmdir(tempdir)  # remove temp dir if empty
            except OSError:
                pass
        if os.path.exists(zip_path):
            os.remove(zip_path)

@app.route('/api/compress', methods=['POST'])
def api_compress():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "Upload PDF file to compress."}), 400
    filename = secure_filename(f.filename)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        f.save(temp_file.name)
        compressed_path = compress_pdf(temp_file.name)
        return send_file(compressed_path, as_attachment=True, download_name="compressed.pdf")
    finally:
        if os.path.exists(temp_file.name): os.remove(temp_file.name)
        if 'compressed_path' in locals() and os.path.exists(compressed_path):
            os.remove(compressed_path)

@app.route('/api/pdf2img', methods=['POST'])
def api_pdf2img():
    f = request.files.get("file")
    if not f:
        return jsonify({"error": "Upload PDF file to convert to images."}), 400
    filename = secure_filename(f.filename)
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    try:
        f.save(temp_file.name)
        images, tempdir = pdf_to_images(temp_file.name)

        # Return zipped images
        import zipfile
        zip_path = tempfile.NamedTemporaryFile(delete=False, suffix=".zip").name
        with zipfile.ZipFile(zip_path, 'w') as zipf:
            for imgf in images:
                zipf.write(imgf, os.path.basename(imgf))
        return send_file(zip_path, as_attachment=True, download_name="images.zip")

    finally:
        if os.path.exists(temp_file.name): os.remove(temp_file.name)
        for imgf in images:
            if os.path.exists(imgf): os.remove(imgf)
        if os.path.exists(tempdir):
            try:
                os.rmdir(tempdir)
            except:
                pass
        if os.path.exists(zip_path):
            os.remove(zip_path)

if __name__ == '__main__':
    # Serve static files from the 'static' folder (where frontend files will reside)
    app.run(debug=True)
