const ops = {
  merge: {
    title: "Merge PDFs",
    multiple: true,
    inputCount: null, // multiple files, user selects how many
    api: "/api/merge",
    multipleFiles: true,
  },
  split: {
    title: "Split PDF",
    multiple: false,
    inputCount: 1,
    api: "/api/split",
    multipleFiles: false,
  },
  compress: {
    title: "Compress PDF",
    multiple: false,
    inputCount: 1,
    api: "/api/compress",
    multipleFiles: false,
  },
  pdf2img: {
    title: "Convert PDF to Images (PNG)",
    multiple: false,
    inputCount: 1,
    api: "/api/pdf2img",
    multipleFiles: false,
  },
};

const operationsSection = document.getElementById("operations");
const uploadSection = document.getElementById("upload-section");
const uploadForm = document.getElementById("upload-form");
const opTitle = document.getElementById("op-title");
const fileInputsContainer = document.getElementById("file-inputs-container");
const statusDiv = document.getElementById("status");
const cancelBtn = document.getElementById("cancel-btn");

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

function showUploadForm(op) {
  uploadSection.classList.remove("hidden");
  operationsSection.classList.add("hidden");
  opTitle.textContent = op.title;
  statusDiv.textContent = "";
  fileInputsContainer.innerHTML = "";

  if (op.multipleFiles) {
    // allow multiple files selector for this op
    const input = document.createElement("input");
    input.type = "file";
    input.name = "files";
    input.multiple = true;
    input.accept = "application/pdf";
    fileInputsContainer.appendChild(input);
  } else {
    // single file input
    const input = document.createElement("input");
    input.type = "file";
    input.name = "file";
    input.accept = "application/pdf";
    fileInputsContainer.appendChild(input);
  }
}

function resetForm() {
  currentOp = null;
  uploadSection.classList.add("hidden");
  operationsSection.classList.remove("hidden");
  fileInputsContainer.innerHTML = "";
  statusDiv.textContent = "";
  uploadForm.reset();
}

uploadForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  if (!currentOp) return;

  const formData = new FormData(uploadForm);
  statusDiv.textContent = "Processing... please wait.";

  try {
    const response = await fetch(currentOp.api, {
      method: "POST",
      body: formData,
    });

    if (!response.ok) {
      const errData = await response.json();
      statusDiv.textContent = `Error: ${errData.error || "Unknown error"}`;
      return;
    }

    // Handle download
    const blob = await response.blob();

    // Get filename from content-disposition header
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

    statusDiv.textContent = "Download started.";
  } catch (err) {
    statusDiv.textContent = "An error occurred: " + err.message;
  }
});
