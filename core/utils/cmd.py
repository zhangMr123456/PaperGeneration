import subprocess
import sys
import os
from typing import List, Optional


def run_python_script(
        script_path: str,
        args: Optional[List[str]] = None,
        env: Optional[dict] = None,
        cwd: Optional[str] = None
) -> int:
    """
    运行Python脚本，复用当前虚拟环境，流式打印输出

    Args:
        script_path: Python脚本路径
        args: 传递给脚本的参数列表
        env: 环境变量字典（默认使用当前虚拟环境）
        cwd: 工作目录

    Returns:
        int: 脚本的退出码
    """
    # 使用当前Python解释器的路径
    python_executable = sys.executable

    # 构建命令
    cmd = [python_executable, script_path]
    if args:
        cmd.extend(args)

    # 如果没有提供环境变量，使用当前虚拟环境
    if env is None:
        # 复制当前环境
        env = os.environ.copy()
        # 确保使用当前虚拟环境的Python
        env['VIRTUAL_ENV'] = sys.prefix

    print(f"执行命令: {' '.join(cmd)}")
    print(f"使用Python: {python_executable}")
    print(f"虚拟环境: {sys.prefix}")
    print("-" * 50)

    try:
        # 创建子进程
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,  # 合并标准错误到标准输出
            universal_newlines=True,  # 文本模式
            bufsize=1,  # 行缓冲
            env=env,
            cwd=cwd
        )

        # 实时流式打印输出
        for line in iter(process.stdout.readline, ''):
            print(line, end='', flush=True)

        # 等待进程完成
        process.wait()

        # 检查退出码
        if process.returncode != 0:
            print(f"\n脚本执行失败，退出码: {process.returncode}")
        else:
            print(f"\n脚本执行成功，退出码: {process.returncode}")

        return process.returncode

    except FileNotFoundError:
        print(f"错误: 脚本文件不存在: {script_path}")
        return 1
    except KeyboardInterrupt:
        print("\n用户中断执行")
        if 'process' in locals():
            process.terminate()
        return 130
    except Exception as e:
        print(f"执行过程中发生错误: {str(e)}")
        return 1


def run_python_command(
        command: str,
        args: Optional[List[str]] = None,
        env: Optional[dict] = None,
        cwd: Optional[str] = None
) -> int:
    """
    直接执行Python命令（不是脚本文件）

    Args:
        command: Python命令字符串（如："print('hello')" 或 "-c 'import sys; print(sys.path)'"）
        args: 额外的参数
        env: 环境变量字典
        cwd: 工作目录

    Returns:
        int: 命令的退出码
    """
    python_executable = sys.executable

    # 构建命令
    cmd = [python_executable, "-c", command]
    if args:
        cmd.extend(args)

    if env is None:
        env = os.environ.copy()
        env['VIRTUAL_ENV'] = sys.prefix

    print(f"执行命令: {' '.join(cmd)}")
    print(f"使用Python: {python_executable}")
    print("-" * 50)

    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1,
            env=env,
            cwd=cwd
        )

        for line in iter(process.stdout.readline, ''):
            print(line, end='', flush=True)

        process.wait()

        if process.returncode != 0:
            print(f"\n命令执行失败，退出码: {process.returncode}")
        else:
            print(f"\n命令执行成功")

        return process.returncode

    except KeyboardInterrupt:
        print("\n用户中断执行")
        if 'process' in locals():
            process.terminate()
        return 130
    except Exception as e:
        print(f"执行过程中发生错误: {str(e)}")
        return 1


# 使用示例
if __name__ == "__main__":
    # 示例1: 运行Python脚本
    print("示例1: 运行Python脚本")
    exit_code = run_python_script(
        script_path="test_script.py",
        args=["arg1", "arg2"],
        cwd="."  # 当前目录
    )

    print("\n" + "=" * 50 + "\n")

    # 示例2: 直接执行Python命令
    print("示例2: 直接执行Python命令")
    exit_code = run_python_command(
        command="import sys; print('Python版本:', sys.version); print('虚拟环境路径:', sys.prefix)"
    )