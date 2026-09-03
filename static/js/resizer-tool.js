const imageInput = document.getElementById("imageInput");
const dropZone = document.getElementById("dropZone");
const previewBox = document.getElementById("previewBox");
const previewImage = document.getElementById("previewImage");
const fileName = document.getElementById("fileName");
const originalSize = document.getElementById("originalSize");
const removeImageBtn = document.getElementById("removeImage");
const clearAllBtn = document.getElementById("clearAll");
const widthInput = document.getElementById("width");
const heightInput = document.getElementById("height");
const aspectRatioCheckbox = document.getElementById("aspectRatio");
const qualitySlider = document.getElementById("quality");
const qualityValue = document.getElementById("qualityValue");
const formatInput = document.getElementById("format");
const form = document.getElementById("resizerForm");
const processButton = document.querySelector(".process-btn");
const themeToggle = document.getElementById("themeToggle");

const MAX_FILES = 10;
const MAX_TOTAL_BYTES = 20 * 1024 * 1024;
let aspectRatio = 1;
let previewUrl = null;

// -------- Dark / Light mode --------
function setTheme(theme) {
    document.body.classList.toggle("dark-mode", theme === "dark");
    themeToggle.innerText = theme === "dark" ? "☀️ Light Mode" : "🌙 Dark Mode";
    localStorage.setItem("imageToolTheme", theme);
}
setTheme(localStorage.getItem("imageToolTheme") === "dark" ? "dark" : "light");
themeToggle.addEventListener("click", () => {
    setTheme(document.body.classList.contains("dark-mode") ? "light" : "dark");
});

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + " Bytes";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + " KB";
    return (bytes / (1024 * 1024)).toFixed(2) + " MB";
}

function showError(message) {
    const old = document.getElementById("errorMessage");
    if (old) old.remove();
    const box = document.createElement("div");
    box.className = "error-message";
    box.id = "errorMessage";
    box.innerHTML = `<span class="error-icon">⚠️</span><div class="error-content"><strong>Something went wrong</strong><p>${message}</p></div><button type="button" id="closeError">✕</button>`;
    document.querySelector(".container").insertBefore(box, document.querySelector(".container").firstChild);
    document.getElementById("closeError").addEventListener("click", () => box.remove());
}

function totalSizeOf(files) {
    let total = 0;
    for (let i = 0; i < files.length; i++) total += files[i].size;
    return total;
}

function isTotalSizeAllowed(files) {
    const totalSize = totalSizeOf(files);
    if (totalSize > MAX_TOTAL_BYTES) {
        showError("Selected images are too large (" + formatFileSize(totalSize) + "). Maximum upload size is " + formatFileSize(MAX_TOTAL_BYTES) + " combined.");
        return false;
    }
    return true;
}

function showImages(files) {
    if (files.length > MAX_FILES) {
        showError("You can select maximum " + MAX_FILES + " images at once.");
        imageInput.value = "";
        return;
    }
    if (!isTotalSizeAllowed(files)) {
        imageInput.value = "";
        return;
    }
    if (previewUrl) URL.revokeObjectURL(previewUrl);

    const firstFile = files[0];
    previewUrl = URL.createObjectURL(firstFile);
    previewImage.src = previewUrl;
    previewBox.style.display = "block";
    fileName.innerText = files.length + " image" + (files.length > 1 ? "s" : "") + " selected";
    originalSize.innerText = "Total File Size: " + formatFileSize(totalSizeOf(files));

    const image = new Image();
    image.onload = function () {
        aspectRatio = image.width / image.height;
        if (!widthInput.value && !heightInput.value) {
            widthInput.value = image.width;
            heightInput.value = image.height;
        }
    };
    image.src = previewUrl;
}

imageInput.addEventListener("change", function () {
    if (this.files.length === 0) return;
    showImages(this.files);
});

dropZone.addEventListener("click", function (event) {
    if (event.target.tagName === "LABEL" || event.target.tagName === "INPUT" || event.target.closest("label")) return;
    imageInput.click();
});

dropZone.addEventListener("dragover", function (event) {
    event.preventDefault();
    dropZone.classList.add("dragover");
});
dropZone.addEventListener("dragleave", function () {
    dropZone.classList.remove("dragover");
});
dropZone.addEventListener("drop", function (event) {
    event.preventDefault();
    dropZone.classList.remove("dragover");
    const files = event.dataTransfer.files;
    if (!files || files.length === 0) return;
    if (files.length > MAX_FILES) {
        showError("You can select maximum " + MAX_FILES + " images at once.");
        return;
    }
    for (let i = 0; i < files.length; i++) {
        if (!files[i].type.startsWith("image/")) {
            showError("Please select image files only.");
            return;
        }
    }
    const dt = new DataTransfer();
    for (let i = 0; i < files.length; i++) dt.items.add(files[i]);
    imageInput.files = dt.files;
    showImages(imageInput.files);
});

widthInput.addEventListener("input", function () {
    if (!aspectRatioCheckbox.checked) return;
    const width = parseInt(this.value);
    if (isNaN(width) || aspectRatio <= 0) return;
    heightInput.value = Math.round(width / aspectRatio);
});
heightInput.addEventListener("input", function () {
    if (!aspectRatioCheckbox.checked) return;
    const height = parseInt(this.value);
    if (isNaN(height) || aspectRatio <= 0) return;
    widthInput.value = Math.round(height * aspectRatio);
});

qualitySlider.addEventListener("input", function () {
    qualityValue.innerText = this.value + "%";
});
qualityValue.innerText = qualitySlider.value + "%";

function resetForm() {
    imageInput.value = "";
    previewImage.src = "";
    previewBox.style.display = "none";
    fileName.innerText = "";
    originalSize.innerText = "";
    widthInput.value = "";
    heightInput.value = "";
    if (previewUrl) { URL.revokeObjectURL(previewUrl); previewUrl = null; }
}

removeImageBtn.addEventListener("click", resetForm);
clearAllBtn.addEventListener("click", function () {
    resetForm();
    aspectRatioCheckbox.checked = true;
    aspectRatio = 1;
    qualitySlider.value = 80;
    qualityValue.innerText = "80%";
    formatInput.value = "JPEG";
    processButton.disabled = false;
    processButton.innerText = "🚀 Resize & Compress Images";
    const resultSection = document.getElementById("resultSection");
    if (resultSection) resultSection.remove();
    dropZone.scrollIntoView({ behavior: "smooth", block: "center" });
});

form.addEventListener("submit", function (event) {
    if (imageInput.files.length === 0) return;
    if (imageInput.files.length > MAX_FILES) {
        event.preventDefault();
        showError("You can process maximum " + MAX_FILES + " images at once.");
        return;
    }
    if (!isTotalSizeAllowed(imageInput.files)) {
        event.preventDefault();
        return;
    }
    processButton.innerText = "⏳ Processing... Please wait";
    processButton.disabled = true;
    processButton.style.cursor = "not-allowed";
});
