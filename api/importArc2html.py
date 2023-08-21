import os
import json
from bs4 import BeautifulSoup, NavigableString
from http.server import BaseHTTPRequestHandler
from io import BytesIO
from werkzeug.datastructures import FileStorage
from werkzeug.formparser import parse_form_data

'''
class HTTPRequest(BaseHTTPRequestHandler):
    def __init__(self, request_text):
        self.rfile = BytesIO(request_text)
        self.raw_requestline = self.rfile.readline()
        self.error_code = self.error_message = None
        self.parse_request()

    def send_error(self, code, message):
        self.error_code = code
        self.error_message = message
'''


class handler(BaseHTTPRequestHandler):

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        content_type = self.headers['Content-Type']

        environ = {
            'CONTENT_LENGTH': content_length,
            'CONTENT_TYPE': content_type,
            'wsgi.input': self.rfile,
        }
        stream, form, files = parse_form_data(environ)
        json_file = files.get('json')

        # 打印接收到的 POST 数据
        print("Received POST data:")

        # 检查请求体是否为空
        if not json_file:
            self.send_response(400)  # Bad Request
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Empty request body received.")
            return

        # 尝试解析 JSON 数据
        try:
            json_data = json.loads(json_file)
            print("Successfully parsed JSON data:")
        except json.JSONDecodeError as e:
            print("JSON decoding error:", str(e))
            self.send_response(400)  # Bad Request
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b"Invalid JSON received.")
            return

        # 调用 convert_json_to_html 函数
        html_output = convert_json_to_html(json_data)

        # 返回生成的HTML
        self.send_response(200)  # OK
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html_output.encode('utf-8'))


def convert_json_to_html(json_data):
    # 使用内存中的 JSON 数据，而不是从文件中读取
    to_process, processed, spaces_data = parse_json_and_extract_data(json_data)
    html_content = create_html_bookmark_file()
    update_html_and_process_items(html_content, to_process, processed, spaces_data)
    move_topapps_and_update_html(html_content, to_process, processed)
    remove_empty_items(to_process)
    process_items_without_savedURL(html_content, to_process, processed)
    process_remaining_items_and_update_html(html_content, to_process, processed)
    formatted_content = format_html(html_content)
    return formatted_content


def create_html_bookmark_file(json_path):
    print(json_path)
    directory = os.path.dirname(json_path) or '.'
    html_path = os.path.join(directory, "bookmark_output.html")
    bookmark_template = """
<!DOCTYPE NETSCAPE-Bookmark-file-1>
<HTML>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<Title>BOOKMARKS</Title>
<H1>ARC BOOKMARKS</H1>

<DT><H3 FOLDED>ArcBookmarks</H3>
<DL><p>
<DT><H3 FOLDED>TopApps</H3>
<DL><p>
</DL><p>
</DL><p>

</HTML>
    """
    with open(html_path, 'w', encoding='utf-8') as file:
        file.write(bookmark_template)
    print(f"书签文件已创建在: {html_path}")

def parse_json_and_extract_data(json_path): 
    with open(json_path, 'r', encoding='utf-8') as file:
        data = json.load(file)
    items_list = data.get("sidebar", {}).get("containers", [])
    to_process = [] 
    for item in items_list: 
        items = item.get("items", [])
        for i in range(0, len(items), 2): 
            id_ = items[i]
            details = items[i+1]
            # 从 details 中提取相关信息
            item_data = {
                "ID": details.get("id", ""),
                "Title": details.get("title", ""),
                "savedTitle": details["data"].get("tab", {}).get("savedTitle", ""),
                "savedURL": details["data"].get("tab", {}).get("savedURL", ""),
                "parentID": details.get("parentID", ""),
                "_0": details["data"].get("itemContainer", {}).get("containerType", {}).get("spaceItems", {}).get("_0", ""),
                "containerType": list(details["data"].get("itemContainer", {}).get("containerType", {}).keys())[0] if "itemContainer" in details["data"] else ""
            }
            to_process.append(item_data) 
    
    spaces_data = []  
    for container in items_list:  
        spaces = container.get("spaces", [])
        for i in range(0, len(spaces), 2):
            space_id = spaces[i]
            details = spaces[i+1]
            container_ids = details.get("containerIDs", [])
            space_data = {
                "ID": space_id,
                "unpinnedID": container_ids[container_ids.index("unpinned")+1] if "unpinned" in container_ids else "",
                "pinnedID": container_ids[container_ids.index("pinned")+1] if "pinned" in container_ids else "",
                "title": details.get("title", "")
            }
            spaces_data.append(space_data)
    processed = []
    return to_process, processed, spaces_data

def update_html_and_process_items(json_path, to_process, processed, spaces_data): 
    # 获取 JSON 文件所在的目录
    directory = os.path.dirname(json_path)
    # 构造 HTML 文件的路径
    html_path = os.path.join(directory, "bookmark_output.html")
    with open(html_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    index = content.find('<H3 FOLDED>ArcBookmarks</H3>\n<DL><p>') 
    if index == -1:
        print("HTML格式不正确！")
        return
    # 保留该标记之前的所有内容，以及该标记自身
    prefix_content = content[:index + len('<H3 FOLDED>ArcBookmarks</H3>\n<DL><p>')]
    # 初始化 new_content 为 prefix_content
    new_content = prefix_content
    
    # 遍历每个空间和待处理的 items
    for space in spaces_data: 
        for item in to_process[:]:
            if item["ID"] == space["pinnedID"]: # 处理1，如果 item 的 ID 与空间的 pinnedID 相匹配
                new_content += f'\n<DT><H3 FOLDED>{space["title"] + " pinned"}</H3>\n<DL><p>\n</DL><p>'
                item["Foldername"] = space["title"]  + " pinned"
                to_process.remove(item)
                processed.append(item)
            elif item["ID"] == space["unpinnedID"]: # 处理2，如果 item 的 ID 与空间的 unpinnedID 直接删掉
                # new_content += f'\n<DT><H3 FOLDED>{space["title"] + " unpinned"}</H3>\n<DL><p></DL><p>'
                # item["Foldername"] = space["title"] + " unpinned"
                to_process.remove(item)
                # processed.append(item)
            elif item["ID"] == space["ID"]: # 处理1，如果 item 的 ID 与空间的 id 相匹配，直接删掉
                to_process.remove(item)
    
    new_content += content[index + len('<H3 FOLDED>ArcBookmarks</H3>\n<DL><p>'):]
    with open(html_path, 'w', encoding='utf-8') as file:
        file.write(new_content)
    print(f"space文件夹已新建: {html_path}")


def move_topapps_and_update_html(json_path, to_process, processed):
    directory = os.path.dirname(json_path)
    html_path = os.path.join(directory, "bookmark_output.html")
    with open(html_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    topApps_ID = ""
    for item in to_process: 
        if item["containerType"] == "topApps":
            topApps_ID = item["ID"]
            to_process.remove(item)
            processed.append(item)
            break

    bookmarks_to_add = ""
    items_to_remove = [] 

    for item in to_process: 
        if item["parentID"] == topApps_ID:
            bookmarks_to_add += f'\n<DT><A HREF="{item["savedURL"]}">{item["savedTitle"] if item["savedTitle"] else item["Title"]}</A>'
            items_to_remove.append(item) 
    for item in items_to_remove:
        to_process.remove(item)

    marker = '<DT><H3 FOLDED>TopApps</H3>\n<DL><p>'
    start_index = content.find(marker)
    if start_index != -1:
        start_index += len(marker)  # 计算标记的结束位置
        content = content[:start_index] + bookmarks_to_add + content[start_index:]
    
    with open(html_path, 'w', encoding='utf-8') as file:
        file.write(content)
    print(f"TopApps已处理完成: {html_path}")

def remove_empty_items(to_process):
    # 使用浅拷贝来迭代
    for item in to_process[:]:  
        # 检查所需的键是否都为空或为 None
        if not item.get("Title") and not item.get("savedTitle") and not item.get("savedURL") and not item.get("parentID"):
            to_process.remove(item)  # 从列表中移除 item

# 下面是两个，供另外函数使用的小操作函数
def create_subfolder_in_html(content, parent_foldername, subfolder_name):
    marker = f'<H3 FOLDED>{parent_foldername}</H3>\n<DL><p>'
    start_index = content.find(marker)

    if start_index != -1:
        start_index += len(marker)
        subfolder_html = f'\n<DT><H3 FOLDED>{subfolder_name}</H3>\n<DL><p>\n</DL><p>'
        content = content[:start_index] + subfolder_html + content[start_index:]
    return content

def create_bookmark_in_html(content, foldername, title, url, item): 
    marker = f'<H3 FOLDED>{foldername}</H3>\n<DL><p>'
    start_index = content.find(marker)
    
    if start_index != -1:
        start_index += len(marker) # 计算标记的结束位置
        bookmark_html = f'\n<DT><A HREF="{url}">{title}</A>'
        content = content[:start_index] + bookmark_html + content[start_index:]
        return content, True # 返回更新的内容和一个标记表示书签已成功添加
    return content, False  # 返回原始内容和一个标记表示书签没有被添加

def process_items_without_savedURL(json_path, to_process, processed):
    # 获取 JSON 文件和 HTML 文件所在的目录，然后打开 HTML
    directory = os.path.dirname(json_path)
    html_path = os.path.join(directory, "bookmark_output.html")
    with open(html_path, 'r', encoding='utf-8') as file:
        content = file.read()
    
    # 定义内部函数，传入待处理列表中的一个 item，和已处理的列表对比，并做出移动处理
    # 这里的精妙之处在于，把上面的 content 作为参数传递给 move_item_to_processed
    def move_item_to_processed(item, content): 
        for processed_item in processed: # 循环已处理列表
            if item["parentID"] == processed_item["ID"]:
                parent_foldername = processed_item["Foldername"]
                subfolder_name = item.get("savedTitle") or item.get("Title") or "" # 按需要的格式命名
                content = create_subfolder_in_html(content, parent_foldername, subfolder_name) # 传入参数，执行创建子文件夹的过程
                
                item["Foldername"] = subfolder_name
                processed.append(item)
                to_process.remove(item) 
                return True, content # 返回两个值：一个布尔值和更新后的 content
        return False, content

    # 外部的 while 循环确保只要 to_process 列表中还存在没有 "savedURL" 的 item，就会持续执行循环体
    while any(not item["savedURL"] for item in to_process): # 这里是用来“重复扫”待处理列表
        # 使用 for 循环迭代 to_process 列表的浅拷贝，以便在循环体中安全地修改原始 to_process 列表
        for item in reversed(to_process[:]): 
            # 检查当前 item 是否缺少 "savedURL"
            if not item["savedURL"]:
                moved, content = move_item_to_processed(item, content)  # 调用函数并接收返回的两个值
                if moved:
                    continue
    with open(html_path, 'w', encoding='utf-8') as file:
        file.write(content)
    print(f"子文件夹处理完成: {html_path}")

def process_remaining_items_and_update_html(json_path, to_process, processed):
    directory = os.path.dirname(json_path)
    html_path = os.path.join(directory, "bookmark_output.html")
    with open(html_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # 在循环中使用列表的浅拷贝，并在循环结束后，从原始列表中删除已处理的元素
    items_to_remove = []
    # 使用浅拷贝遍历 to_process 列表
    for item in to_process[:]:
        # 如果 item 的 savedURL 不为空
        if item["savedURL"]:
            # 对于每个 savedURL 不为空的 item，查找其 parentID 在 processed 列表中的匹配项
            for processed_item in processed:
                if item["parentID"] == processed_item["ID"]:

                    # 获取文件夹名和书签信息
                    foldername = processed_item["Foldername"]
                    title = item["savedTitle"] if item["savedTitle"] else item["Title"]
                    url = item["savedURL"]
                    
                    # 在 HTML 内容中为 item 创建书签，这里的 item_removed 其实代表的是添加了书签，但我懒得改参数名字了
                    content, item_removed = create_bookmark_in_html(content, foldername, title, url, item)
                    # 如果 item 被成功移除，将其添加到待删除列表中，然后中断内部循环
                    if item_removed:
                        items_to_remove.append(item) # 把后续要删除的item暂存到这里作为索引
                        break

    # 从原始 to_process 列表中删除已处理的 item
    for item in items_to_remove:
        to_process.remove(item)

    # 将修改后的内容写回 HTML 文件
    with open(html_path, 'w', encoding='utf-8') as file:
        file.write(content)
    print(f"剩下的书签处理完成: {html_path}")

# 格式化 html 文件增加缩进等，天坑，导入书签文件的时候，书签和文件夹之间的嵌套关系居然会因为 html 里面的格式化而发生变化，就很离谱
def format_html(json_path):
    directory = os.path.dirname(json_path)
    html_path = os.path.join(directory, "bookmark_output.html")
    with open(html_path, 'r', encoding='utf-8') as file:
        content = file.read()

    # 按行切割内容
    lines = content.split('\n')
    formatted_lines = [] # 一个空列表，用于存储格式化后的行
    indent_level = 0 # 一个整数，表示当前的缩进级别。每次遇到<DL><p>时增加，每次遇到</DL><p>时减少。

    # 遍历每一行，并使用strip()方法去除每行前后的空格或制表符，根据行内容来决定缩进的级别
    for line in lines:
        stripped_line = line.strip()
        
        # 如果这一行包含 '<DL><p>'，在添加到结果列表前先缩进，然后增加缩进级别
        if '<DL><p>' in stripped_line:
            formatted_lines.append('    ' * indent_level + stripped_line)
            indent_level += 1
        # 如果这一行包含 '</DL><p>'，首先减少缩进级别，然后再添加到结果列表前缩进
        elif '</DL><p>' in stripped_line:
            indent_level -= 1
            formatted_lines.append('    ' * indent_level + stripped_line)
        else:
            # 对于其他行，直接根据当前的缩进级别进行缩进，然后添加到结果列表
            formatted_lines.append('    ' * indent_level + stripped_line)

    # 将处理后的行重新拼接成字符串
    formatted_content = '\n'.join(formatted_lines)

    # 将格式化后的内容写回文件
    with open(html_path, 'w', encoding='utf-8') as file:
        file.write(formatted_content)