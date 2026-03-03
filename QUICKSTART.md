# Hướng dẫn nhanh - Quick Start Guide

## Bước 1: Cài đặt

```bash
# Cài đặt Python dependencies
pip install -r requirements.txt

# Download weather file
# Truy cập: https://energyplus.net/weather
# Tìm: Vietnam, Ho Chi Minh City
# Lưu file .epw vào: data/weather/
```

## Bước 2: Chạy simulation đầu tiên

```bash
# Chạy kịch bản baseline
python main.py run --scenario config/scenarios/baseline.json
```

## Bước 3: Xem kết quả

Kết quả sẽ được lưu trong: `outputs/results/Baseline/`

- `eplusout.csv` - Dữ liệu chi tiết
- `eplustbl.htm` - Báo cáo HTML (mở bằng browser)
- `report.json` - Metrics tổng hợp
- `plots/` - Biểu đồ

## Bước 4: Chạy tất cả kịch bản và so sánh

```bash
# Chạy tất cả kịch bản song song và tạo báo cáo so sánh
python main.py run-all --parallel --compare
```

Báo cáo so sánh: `outputs/results/comparison_report.xlsx`

## Bước 5: Tạo kịch bản của riêng bạn

1. Copy file baseline:
```bash
cp config/scenarios/baseline.json config/scenarios/my_test.json
```

2. Chỉnh sửa `my_test.json`:
```json
{
  "scenario_name": "My_Test",
  "description": "Test của tôi",
  
  "overrides": {
    "hvac": {
      "thermostat": {
        "cooling_setpoint": 25.0
      }
    }
  }
}
```

3. Chạy:
```bash
python main.py run --scenario config/scenarios/my_test.json
```

## Các lệnh hữu ích

```bash
# Chỉ generate IDF (không chạy simulation)
python main.py generate --scenario config/scenarios/baseline.json

# Chạy với EnergyPlus path tùy chỉnh
python main.py run --scenario config/scenarios/baseline.json \
  --energyplus-path /path/to/energyplus

# Tạo báo cáo cho một kịch bản cụ thể
python main.py report --scenario-name baseline \
  --result-dir outputs/results/Baseline

# So sánh tất cả kịch bản đã chạy
python main.py compare
```

## Troubleshooting

**Lỗi: EnergyPlus not found**
```bash
# Cài đặt EnergyPlus từ: https://energyplus.net/downloads
# Hoặc chỉ định path:
python main.py run --scenario config/scenarios/baseline.json \
  --energyplus-path /usr/local/EnergyPlus-9-6-0/energyplus
```

**Lỗi: Weather file not found**
```bash
# Download weather file và lưu vào data/weather/
# Đảm bảo tên file trong scenario JSON khớp với file thực tế
```

**Kiểm tra lỗi simulation**
```bash
# Xem file .err để biết chi tiết lỗi
cat outputs/results/<scenario_name>/eplusout.err
```

## Cấu trúc file quan trọng

- `config/building/geometry.json` - Kích thước phòng, cửa sổ
- `config/building/materials.json` - Vật liệu xây dựng
- `config/hvac/hvac_config.json` - Cấu hình HVAC
- `config/schedules/schedules.json` - Lịch hoạt động
- `config/scenarios/*.json` - Các kịch bản test

Xem `README.md` để biết thêm chi tiết!
