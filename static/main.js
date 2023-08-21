function convertToJson() {
    const fileInput = document.getElementById('jsonInput');
    const file = fileInput.files[0];
    if (!file) {
        alert('Please select a JSON file first.');
        return;
    }

    const formData = new FormData();
    formData.append('json', file);

    fetch('/api/convert', {
        method: 'POST',
        body: formData
    })
    .then(response => response.blob())
    .then(blob => {
        const downloadLink = document.getElementById('downloadLink');
        downloadLink.href = URL.createObjectURL(blob);
        downloadLink.download = 'converted.html';
        downloadLink.style.display = 'block';
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred. Please try again.');
    });
}