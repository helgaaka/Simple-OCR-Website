document.addEventListener("DOMContentLoaded", () => {
  const ocrForm = document.getElementById("ocrForm");
  const uploadArea = document.getElementById("uploadArea");
  const uploadPrompt = document.getElementById("upload-prompt");
  const imageFile = document.getElementById("imageFile");
  const previewArea = document.getElementById("preview");
  const submitButton = document.getElementById("submitButton");
  const statusDiv = document.getElementById("status");
  const resultContainer = document.getElementById("resultContainer");
  const resultText = document.getElementById("resultText");
  const copyButton = document.getElementById("copyButton");

  let selectedFile = null;

  const handleFile = (file) => {
    const validTypes = ["image/jpeg", "image/png", "image/jpg"];
    if (!validTypes.includes(file.type)) {
      statusDiv.innerHTML = `<span style="color: red;">❌ Tipe file tidak valid. Harap pilih JPG, PNG, JPEG</span>`;
      return;
    }

    selectedFile = file;
    submitButton.disabled = false;

    uploadPrompt.innerHTML = `<p>File dipilih: <strong>${file.name}</strong></p>`;
    previewFile(file);
  };

//  Fungsi Pratinjau Gambar
  const previewFile = (file) => {
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onloadend = () => {
      previewArea.innerHTML = `<img src="${reader.result}" alt="Pratinjau Gambar">`;
      previewArea.style.display = "block";
    };
  };

// Fungsi Upload
  uploadArea.addEventListener("click", () => imageFile.click());

  uploadArea.addEventListener("dragover", (e) => {
    e.preventDefault();
    uploadArea.classList.add("drag-over");
  });

  uploadArea.addEventListener("dragleave", () => {
    uploadArea.classList.remove("drag-over");
  });

  uploadArea.addEventListener("drop", (e) => {
    e.preventDefault();
    uploadArea.classList.remove("drag-over");
    const file = e.dataTransfer.files[0];
    if (file) {
      handleFile(file);
    }
  });

  imageFile.addEventListener("change", () => {
    if (imageFile.files.length > 0) {
      handleFile(imageFile.files[0]);
    }
  });

// Fungsi Submit
  ocrForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (!selectedFile) {
      statusDiv.innerHTML = `<span style="color: red;">❌ Silakan pilih file terlebih dahulu</span>`;
      return;
    }

    statusDiv.innerHTML = `<div class="spinner"></div><span>Sedang memproses...</span>`;

    resultContainer.style.display = "none";
    submitButton.disabled = true;

    const formData = new FormData();
    formData.append("image_file", selectedFile);

    try {
      const response = await fetch("/api/ocr-process", {
        method: "POST",
        body: formData,
      });
      const data = await response.json();
      if (!response.ok) {
        throw new Error(data.error || `HTTP error! Status: ${response.status}`);
      }
      resultText.textContent = data.structured_text;
      resultContainer.style.display = "block";
      statusDiv.innerHTML = `<span style="color: green;">✔ Proses berhasil</span>`;
    } catch (error) {
      console.error("Error during OCR process:", error);
      statusDiv.innerHTML = `<span style="color: red;">❌ Gagal: ${error.message}</span>`;
    } finally {
      if (!statusDiv.innerHTML.includes("✔ Proses berhasil")) {
        statusDiv.innerHTML = statusDiv.innerHTML; 
      }
      submitButton.disabled = false;
    }
  });

// Fungsi Button Copy
  copyButton.addEventListener("click", () => {
    navigator.clipboard
      .writeText(resultText.textContent)
      .then(() => {
        copyButton.innerHTML = `
                Done
            `;
        setTimeout(() => {
          copyButton.innerHTML = `
                    Copy
                `;
        }, 2000);
      })
      .catch((err) => {
        console.error("Gagal menyalin teks: ", err);
      });
  });
});
