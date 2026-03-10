import time
import threading
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class SnowflakeConfig:
    """雪花算法配置类"""
    epoch: int = 1609459200000  # 2021-01-01 00:00:00 UTC
    machine_id_bits: int = 10  # 机器ID位数
    sequence_bits: int = 12  # 序列号位数

    def __post_init__(self):
        self.max_machine_id = (1 << self.machine_id_bits) - 1
        self.max_sequence = (1 << self.sequence_bits) - 1
        self.machine_id_shift = self.sequence_bits
        self.timestamp_shift = self.sequence_bits + self.machine_id_bits


class SnowflakeIDGenerator:
    """雪花ID生成器"""

    def __init__(self, machine_id: int, config: Optional[SnowflakeConfig] = None):
        """
        初始化雪花ID生成器

        Args:
            machine_id: 机器ID (0-1023)
            config: 雪花算法配置
        """
        self.config = config or SnowflakeConfig()

        if machine_id < 0 or machine_id > self.config.max_machine_id:
            raise ValueError(f"机器ID必须在0到{self.config.max_machine_id}之间")

        self.machine_id = machine_id
        self.sequence = 0
        self.last_timestamp = -1
        self.lock = threading.Lock()

    def _current_millis(self) -> int:
        """获取当前毫秒时间戳"""
        return int(time.time() * 1000)

    def _til_next_millis(self, last_timestamp: int) -> int:
        """等待到下一毫秒"""
        timestamp = self._current_millis()
        while timestamp <= last_timestamp:
            timestamp = self._current_millis()
        return timestamp

    def generate(self) -> int:
        """生成雪花ID"""
        with self.lock:
            timestamp = self._current_millis()

            # 时钟回拨处理
            if timestamp < self.last_timestamp:
                raise Exception(f"时钟回拨 detected. 拒绝生成ID直到 {self.last_timestamp}")

            # 同一毫秒内生成
            if timestamp == self.last_timestamp:
                self.sequence = (self.sequence + 1) & self.config.max_sequence
                if self.sequence == 0:  # 当前毫秒序列号用尽
                    timestamp = self._til_next_millis(self.last_timestamp)
            else:
                self.sequence = 0

            self.last_timestamp = timestamp

            # 生成ID
            elapsed_time = timestamp - self.config.epoch
            snowflake_id = (elapsed_time << self.config.timestamp_shift) | \
                           (self.machine_id << self.config.machine_id_shift) | \
                            self.sequence

            return snowflake_id

    def parse(self, snowflake_id: int) -> dict:
        """解析雪花ID"""
        sequence = snowflake_id & self.config.max_sequence
        machine_id = (snowflake_id >> self.config.machine_id_shift) & self.config.max_machine_id
        timestamp = (snowflake_id >> self.config.timestamp_shift) + self.config.epoch

        return {
            "timestamp": timestamp,
            "datetime": datetime.fromtimestamp(timestamp / 1000),
            "machine_id": machine_id,
            "sequence": sequence,
            "snowflake_id": snowflake_id
        }


generator = SnowflakeIDGenerator(machine_id=1)


class DistributedSnowflakeGenerator:
    """分布式雪花ID生成器（多进程/多线程安全）"""

    def __init__(self, machine_id: int, config: Optional[SnowflakeConfig] = None):
        self.generator = SnowflakeIDGenerator(machine_id, config)

    def generate(self) -> int:
        """生成ID（线程安全）"""
        return self.generator.generate()

    def batch_generate(self, count: int) -> list:
        """批量生成ID"""
        ids = []
        for _ in range(count):
            ids.append(self.generate())
        return ids


# 使用示例
def example_usage():
    # 1. 基本使用
    print("=== 基本使用示例 ===")

    # 生成单个ID
    snowflake_id = generator.generate()
    print(f"生成的雪花ID: {snowflake_id}")
    print(f"ID的二进制表示: {bin(snowflake_id)}")

    # 解析ID
    parsed = generator.parse(snowflake_id)
    print(f"\n解析结果:")
    for key, value in parsed.items():
        print(f"  {key}: {value}")

    # 2. 批量生成
    print("\n=== 批量生成示例 ===")
    batch_ids = []
    for i in range(5):
        batch_ids.append(generator.generate())
    print(f"批量生成的ID: {batch_ids}")

    # 3. 分布式生成器
    print("\n=== 分布式生成器示例 ===")
    distributed_gen = DistributedSnowflakeGenerator(machine_id=2)

    # 多线程生成ID
    import concurrent.futures

    def generate_ids(gen, count):
        return [gen.generate() for _ in range(count)]

    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(generate_ids, distributed_gen, 3)
                   for _ in range(3)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    print(f"多线程生成的ID: {results}")

    # 4. 自定义配置
    print("\n=== 自定义配置示例 ===")
    custom_config = SnowflakeConfig(
        epoch=1577836800000,  # 2020-01-01
        machine_id_bits=8,  # 256台机器
        sequence_bits=14  # 每毫秒16384个ID
    )

    custom_generator = SnowflakeIDGenerator(
        machine_id=100,
        config=custom_config
    )

    custom_id = custom_generator.generate()
    print(f"自定义配置生成的ID: {custom_id}")
    print(f"自定义配置解析: {custom_generator.parse(custom_id)}")


def performance_test():
    """性能测试"""
    print("\n=== 性能测试 ===")
    generator = SnowflakeIDGenerator(machine_id=1)

    import time
    start_time = time.time()
    count = 10000

    ids = set()
    for _ in range(count):
        id_ = generator.generate()
        ids.add(id_)

    elapsed = time.time() - start_time
    print(f"生成 {count} 个ID耗时: {elapsed:.4f}秒")
    print(f"平均每个ID耗时: {elapsed / count * 1000000:.2f}微秒")
    print(f"生成的ID数量: {len(ids)} (应该等于{count})")

    # 检查是否有重复
    if len(ids) != count:
        print("警告: 检测到重复ID!")
    else:
        print("所有ID都是唯一的!")


if __name__ == "__main__":
    # 运行示例
    example_usage()

    # 运行性能测试
    performance_test()
