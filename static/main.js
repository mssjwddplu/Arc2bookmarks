function convertToJson() {
    const fileInput = document.getElementById('jsonInput');
    const file = fileInput.files[0];
    if (!file) {
        alert('Please select a JSON file first.');
        return;
    }

    const formData = new FormData();
    formData.append('json', file);

    // 打印要发送的文件信息
    console.log("Sending file:", file.name, "Size:", file.size);

    // 修改这里的 URL
    fetch('/api/importArc2html', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        if (!response.ok) {
            throw new Error(`Server responded with an error. Status: ${response.status}`);
        }
        return response.blob();
    })
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