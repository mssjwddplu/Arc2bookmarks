$(document).ready(function() {
    $("#upload-form").submit(function(e) {
        e.preventDefault();

        const fileInput = document.getElementById('jsonInput');
        const file = fileInput.files[0];
        if (!file) {
            alert('Please select a JSON file first.');
            return;
        }

        // 用户已选择文件，显示 "Uploading..."
        $("#upload-status").text("Uploading...");

        const formData = new FormData();
        formData.append('json', file);

        // 打印要发送的文件信息
        console.log("Sending file:", file.name, "Size:", file.size);

        $.ajax({
            url: '/api/importArc2html',
            type: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            
            success: function(data) {
                const response = JSON.parse(data);  // 解析服务器返回的 JSON 响应

                // 显示 "Upload successful. Estimated wait time: XX seconds"
                $("#upload-status").text("Upload successful. Estimated wait time: " + response.estimated_wait_time + " seconds");

                const downloadLink = document.getElementById('downloadLink');
                const blob = new Blob([response.html_content], {type: 'text/html'});
                const blobURL = URL.createObjectURL(blob);
                downloadLink.href = blobURL;
                
                downloadLink.download = 'converted.html';
                downloadLink.style.display = 'block';

                // 使用 setTimeout 在3秒后显示 "Conversion completed. Please download using the link below."
                setTimeout(function() {
                    $("#upload-status").text("Conversion completed. Please download using the link below.");
                }, 1000);  // 3秒的延迟
            },
            error: function(jqXHR, textStatus, errorMessage) {
                console.error('Error:', errorMessage);
                // 显示错误消息
                $("#upload-status").text("An error occurred. Please try again.");
            }
        });
    });
});
