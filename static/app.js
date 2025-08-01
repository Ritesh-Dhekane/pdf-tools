const ops = {
  merge: {
    title: "Merge PDFs",
    multipleFiles: true,
    api: "/api/merge",
  },
  split: {
    title: "Split PDF",
    multipleFiles: false,
    api: "/api/split",
  },
  compress: {
    title: "Compress PDF",
    multipleFiles: false,
    api: "/api/compress",
  },
  pdf2img: {
    title: "Convert PDF to Images (PNG)",
    multipleFiles: false,
    api: "/api/pdf2img",
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

  const input = document.createElement("input");
  input.type = "file";
  input.name = op.multipleFiles ? "files" : "file";
  input.accept = "application/pdf";
  if (op.multipleFiles) {
    input.multiple = true;
  }
  fileInputsContainer.appendChild(input);
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
