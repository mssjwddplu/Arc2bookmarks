function convertToJson() {
    const fileInput = document.getElementById('jsonInput');
    const file = fileInput.files[0];
    if (!file) {
        alert('Please select a JSON file first.');
        return;
    }

    const formData = new FormData();
    formData.append('json', file);

    // 修改这里的 URL
    fetch('/api/importArc2html', {
        method: 'POST',
        body: formData
    })
    .then(response => {
        // 检查响应是否正常
        if (!response.ok) {
            // 打印服务器返回的状态和状态文本
            console.error('Server Response:', response.status, response.statusText);
            throw new Error('Server responded with an error.');
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
        alert('An error occurred. Please check the console for more details.');
    });
}
