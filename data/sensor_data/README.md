# Sensor Data

Thư mục này dùng để lưu dữ liệu sensor thực tế từ phòng làm việc.

## Định dạng đề xuất

### CSV Format
```csv
timestamp,temperature,humidity,co2,occupancy
2024-01-01 08:00:00,25.5,60.2,450,2
2024-01-01 09:00:00,26.1,58.5,520,4
```

### JSON Format
```json
{
  "timestamp": "2024-01-01T08:00:00",
  "temperature": 25.5,
  "humidity": 60.2,
  "co2": 450,
  "occupancy": 2
}
```

## Sử dụng

Dữ liệu sensor có thể được dùng để:
1. Calibrate simulation model
2. Validate kết quả simulation
3. So sánh predicted vs actual
4. Điều chỉnh parameters

## Ví dụ

Xem file `example_sensor_data.csv` để biết format mẫu.
