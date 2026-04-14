import random
import time
import asyncio
from datetime import datetime
from influxdb_client import Point

try:
    from .client import influx_manager
except ImportError:
    from client import influx_manager

def simulate_battery_data():
    """
    模拟电池数据并同步写入 InfluxDB
    """
    print("Starting continuous synchronous battery data simulation (Ctrl+C to stop)...")
    battery_ids = ["BATT-001", "BATT-002", "BATT-003"]
    
    try:
        while True:
            for batt_id in battery_ids:
                voltage = round(random.uniform(3.2, 4.2), 2)
                current = round(random.uniform(0.5, 2.0), 2)
                temperature = round(random.uniform(20.0, 45.0), 1)
                
                # 创建 Point 对象
                point = Point("battery_stats") \
                    .tag("battery_id", batt_id) \
                    .tag("location", "Warehouse-A") \
                    .field("voltage", voltage) \
                    .field("current", current) \
                    .field("temperature", temperature) \
                    .time(datetime.utcnow())
                
                print(f"Writing: {batt_id} | Voltage: {voltage}V, Current: {current}A, Temp: {temperature}C")
                try:
                    influx_manager.write_point(point)
                except Exception as e:
                    print(f"Error writing to InfluxDB: {e}")
            
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nSimulation stopped by user.")

async def simulate_battery_data_async():
    """
    模拟电池数据并异步写入 InfluxDB (持续运行)
    """
    print("\nStarting continuous asynchronous battery data simulation (Ctrl+C to stop)...")
    battery_ids = ["BATT-001", "BATT-002", "BATT-003"]
    
    try:
        while True:
            tasks = []
            for batt_id in battery_ids:
                voltage = round(random.uniform(3.2, 4.2), 2)
                current = round(random.uniform(0.5, 2.0), 2)
                temperature = round(random.uniform(20.0, 45.0), 1)
                
                point = Point("battery_stats") \
                    .tag("battery_id", batt_id) \
                    .tag("location", "Warehouse-B") \
                    .field("voltage", voltage) \
                    .field("current", current) \
                    .field("temperature", temperature) \
                    .time(datetime.utcnow())
                
                print(f"Writing (Async): {batt_id} | Voltage: {voltage}V")
                tasks.append(influx_manager.write_point_async(point))
            
            await asyncio.gather(*tasks)
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("\nAsync simulation stopped by user.")
    finally:
        await influx_manager.close()

if __name__ == "__main__":
    # 执行同步模拟
    try:
        simulate_battery_data()
    except Exception as e:
        print(f"Sync simulation failed: {e}")
        print("Tip: Make sure InfluxDB is running and settings are correct in .env or config.py")

    # 执行异步模拟
    # asyncio.run(simulate_battery_data_async())
