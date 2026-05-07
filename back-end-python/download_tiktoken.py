"""
下载 tiktoken 编码文件

由于网络限制，需要手动下载 tiktoken 编码文件
"""
import os
import urllib.request

# 缓存目录
CACHE_DIR = os.path.join(os.path.dirname(__file__), ".tiktoken_cache")
os.makedirs(CACHE_DIR, exist_ok=True)

# 文件信息
FILENAME = "cl100k_base.tiktoken"
URL = "https://openaipublic.blob.core.windows.net/encodings/cl100k_base.tiktoken"
EXPECTED_HASH = "223921b76ee99bde995b7ff738513eef100fb51d18c93597a113bcffe865b2a7"

# 备用镜像（如果有的话可以添加）
MIRROR_URLS = [
    URL,
    # 可以添加其他镜像地址
]

def download_file():
    """下载文件"""
    filepath = os.path.join(CACHE_DIR, FILENAME)

    if os.path.exists(filepath):
        print(f"文件已存在: {filepath}")
        return True

    print(f"正在下载 tiktoken 编码文件...")
    print(f"目标路径: {filepath}")

    for url in MIRROR_URLS:
        try:
            print(f"尝试从: {url}")
            urllib.request.urlretrieve(url, filepath)
            print("下载成功!")
            return True
        except Exception as e:
            print(f"下载失败: {e}")
            continue

    print("\n自动下载失败，请手动下载:")
    print(f"1. 下载地址: {URL}")
    print(f"2. 保存到: {filepath}")
    print("3. 或者使用代理后重新运行此脚本")

    return False

if __name__ == "__main__":
    download_file()