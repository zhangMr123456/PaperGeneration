import hashlib


def get_file_md5(file_path, chunk_size=4096):
    """
    计算文件的MD5值（适合大文件，分块读取）

    参数:
        file_path: 文件路径
        chunk_size: 每次读取的块大小（字节），默认4096
    """
    md5_hash = hashlib.md5()

    try:
        with open(file_path, 'rb') as f:
            # 分块读取文件，避免内存占用过高
            while chunk := f.read(chunk_size):
                md5_hash.update(chunk)

        return md5_hash.hexdigest()
    except FileNotFoundError:
        print(f"错误：文件 '{file_path}' 不存在")
        return None
    except Exception as e:
        print(f"读取文件时出错：{e}")
        return None


