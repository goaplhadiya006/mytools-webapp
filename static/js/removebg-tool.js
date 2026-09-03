const imageInput = document.getElementById("imageInput");
const dropZone = document.getElementById("dropZone");
const previewContainer = document.getElementById("previewContainer");
const imagePreview = document.getElementById("imagePreview");
const previewLabel = document.getElementById("previewLabel");
const removeImageBtn = document.getElementById("removeImageBtn");
const form = document.getElementById("uploadForm");
const processing = document.getElementById("processing");
const removeBtn = document.getElementById("removeBtn");
const bgColorField = document.getElementById("bg_color");
const customColor = document.getElementById("customColor");
const transparentBtn = document.getElementById("transparentBtn");
const colorOptions = document.querySelectorAll(".color-option");

const MAX_FILES = 10;
const MAX_TOTAL_BYTES = 20 * 1024 * 1024;
let previewUrl = null;

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + " Bytes";
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(2) + " KB";
    return (bytes / (1024 * 1024)).toFixed(2) + " MB";
}

function showError(message) {
    const old = document.querySelector(".error-message");
    if (old) old.remove();
    const box = document.createElement("div");
    box.className = "error-message";
    box.innerText = "⚠️ " + message;
    form.parentNode.insertBefore(box, form);
}

function totalSizeOf(files) {
    let total = 0;
    for (let i = 0; i < files.length; i++) total += files[i].size;
    return total;
}

imageInput.addEventListener("change", function () {
    if (this.files.length === 0) return;
    handleFiles(this.files);
});

dropZone.addEventListener("click", function (event) {
    if (event.target.tagName === "LABEL" || event.target.closest("label")) return;
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
    const dt = new DataTransfer();
    for (let i = 0; i < files.length; i++) dt.items.add(files[i]);
    imageInput.files = dt.files;
    handleFiles(imageInput.files);
});

function handleFiles(files) {
    if (files.length > MAX_FILES) {
        showError("You can select maximum " + MAX_FILES + " images at once.");
        imageInput.value = "";
        return;
    }
    if (totalSizeOf(files) > MAX_TOTAL_BYTES) {
        showError("Selected images are too large. Maximum combined size is " + formatFileSize(MAX_TOTAL_BYTES) + ".");
        imageInput.value = "";
        return;
    }
    if (previewUrl) URL.revokeObjectURL(previewUrl);
    previewUrl = URL.createObjectURL(files[0]);
    imagePreview.src = previewUrl;
    previewLabel.innerText = files.length > 1 ? files.length + " images selected" : "Selected Image";
    previewContainer.style.display = "block";
}

removeImageBtn.addEventListener("click", function () {
    imageInput.value = "";
    imagePreview.src = "";
    previewContainer.style.display = "none";
    if (previewUrl) { URL.revokeObjectURL(previewUrl); previewUrl = null; }
});

// -------- Background color presets --------
function selectColor(color) {
    bgColorField.value = color;
    colorOptions.forEach((btn) => btn.classList.remove("selected"));
    if (transparentBtn) transparentBtn.classList.remove("selected");
    if (color === "") {
        if (transparentBtn) transparentBtn.classList.add("selected");
    } else {
        colorOptions.forEach((btn) => {
            if (btn.dataset.color === color) btn.classList.add("selected");
        });
        customColor.value = color;
    }
}
colorOptions.forEach((btn) => {
    btn.addEventListener("click", () => selectColor(btn.dataset.color));
});
if (transparentBtn) {
    transparentBtn.addEventListener("click", () => selectColor(""));
}
customColor.addEventListener("input", () => selectColor(customColor.value));

form.addEventListener("submit", function () {
    if (imageInput.files.length === 0) return;
    processing.style.display = "block";
    removeBtn.disabled = true;
    removeBtn.innerText = "⏳ Processing...";
});
