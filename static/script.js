let selectedOption = "text";

function selectOption(option) {
    selectedOption = option;

    // Hide all inputs initially
    document.getElementById("inputText").style.display = "none";
    document.getElementById("inputUrl").style.display = "none";
    document.getElementById("inputFile").style.display = "none";

    // Clear previous bionic text output
    document.getElementById("bionicTextOutput").innerHTML = "<ul></ul>";  // Clear previous output

    // Show the appropriate input field based on selected option
    if (option === "text") {
        document.getElementById("inputText").style.display = "block";
    } else if (option === "url") {
        document.getElementById("inputUrl").style.display = "block";
    } else if (option === "upload") {
        document.getElementById("inputFile").style.display = "block";
    }
}

async function showSummary() {
    if (selectedOption === "text") {
        await handleTextInput();
    } else if (selectedOption === "url") {
        await handleUrlInput();
    } else if (selectedOption === "upload") {
        await handleFileUpload();
    }
}

async function handleTextInput() {
    const text = document.getElementById("inputText").value;
    const formData = new FormData();
    formData.append("text", text);

    try {
        const response = await fetch("/convert", {
            method: "POST",
            body: formData
        });
        const data = await response.json();
        displayBionicText(data.bionic_text);  // Display only bionic text after summarization
    } catch (error) {
        console.error("Error processing text input:", error);
    }
}

async function handleUrlInput() {
    const url = document.getElementById("inputUrl").value;
    const formData = new FormData();
    formData.append("url", url);

    try {
        const response = await fetch("/url", {
            method: "POST",
            body: formData
        });
        const data = await response.json();
        displayBionicText(data.bionic_text);  // Display only bionic text after summarization
    } catch (error) {
        console.error("Error processing URL input:", error);
    }
}

async function handleFileUpload() {
    const fileInput = document.getElementById("inputFile");
    const formData = new FormData();
    
    if (fileInput.files.length === 0) {
        alert("Please select a file to upload.");
        return;
    }

    formData.append("file", fileInput.files[0]);

    try {
        const response = await fetch("/upload", {
            method: "POST",
            body: formData
        });
        const data = await response.json();
        displayBionicText(data.bionic_text);  // Display only bionic text after summarization
    } catch (error) {
        console.error("Error processing file upload:", error);
    }
}

function displayBionicText(bionicText) {
    const bionicTextOutput = document.getElementById("bionicTextOutput");
    bionicTextOutput.innerHTML = ""; // Clear previous content

    // Split text into sentences and display as bullet points
    const sentences = bionicText.split('. ').map(sentence => sentence.trim() + '.');
    sentences.forEach(sentence => {
        const li = document.createElement("li");
        li.innerHTML = sentence; // Sentence as a bullet point
        bionicTextOutput.appendChild(li);
    });
}

function resetForm() {
    // Reset inputs and outputs
    document.getElementById("inputText").value = "";
    document.getElementById("inputUrl").value = "";
    document.getElementById("inputFile").value = "";
    document.getElementById("bionicTextOutput").innerHTML = "<ul></ul>";
}
