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
            
            xhr: function() {
                var xhr = new window.XMLHttpRequest();
                xhr.upload.addEventListener("progress", function(evt) {
                    if (evt.lengthComputable) {
                        var percentComplete = evt.loaded / evt.total;
                        percentComplete = parseInt(percentComplete * 95);  // 将进度条的最大值设置为95%
                        $('#upload-progress-bar').width(percentComplete + '%');
                        $('#upload-progress-bar').html(percentComplete + '%');
                    }
                }, false);
                return xhr;
            },

            success: function(data) {
                // 将进度条设置为100%
                $('#upload-progress-bar').width('100%');
                $('#upload-progress-bar').html('100%');
                const response = JSON.parse(data);  // 解析服务器返回的 JSON 响应

                // 显示 "Upload successful. Estimated wait time: XX seconds"
                $("#upload-status").text("Upload successful. Estimated wait time: " + response.estimated_wait_time + " seconds");

                // 使用 setTimeout 在3秒后显示 "Conversion completed. Please download using the link below."
                setTimeout(function() {
                    const downloadLink = document.getElementById('downloadLink');
                    const blob = new Blob([response.html_content], {type: 'text/html'});
                    const blobURL = URL.createObjectURL(blob);
                    downloadLink.href = blobURL;
                    
                    downloadLink.download = 'converted.html';
                    downloadLink.style.display = 'block';

                    $("#upload-status").text("Conversion completed. Please download using the link below.");
                }, 3000);  // 3秒的延迟
            },
            error: function(jqXHR, textStatus, errorMessage) {
                console.error('Error:', errorMessage);
                // 显示错误消息
                $("#upload-status").text("An error occurred. Please try again.");
            }
        });
    });
});
