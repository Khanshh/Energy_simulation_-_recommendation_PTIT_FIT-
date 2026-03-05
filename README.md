# React + TypeScript + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is enabled on this template. See [this documentation](https://react.dev/learn/react-compiler) for more information.

Note: This will impact Vite dev & build performances.

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```
# EnergyPlus Modular JSON-Python Simulation System

Hệ thống tự động hóa mô phỏng năng lượng tòa nhà với EnergyPlus sử dụng cấu hình JSON và Python scripts.


## 📋 Tổng quan

Hệ thống này cho phép bạn:
- ✅ Định nghĩa cấu hình phòng/tòa nhà bằng file JSON dễ chỉnh sửa
- ✅ Tự động generate file IDF từ JSON
- ✅ Chạy nhiều kịch bản mô phỏng song song
- ✅ Phân tích và so sánh kết quả tự động
- ✅ Tạo báo cáo và biểu đồ trực quan


## 🏗️ Cấu trúc thư mục

```
EEiB-Demo/
├── config/                    # File JSON config
│   ├── building/
│   │   ├── geometry.json     # Kích thước phòng, cửa sổ, cửa
│   │   └── materials.json    # Vật liệu xây dựng
│   ├── hvac/
│   │   └── hvac_config.json  # Cấu hình HVAC
│   ├── schedules/
│   │   └── schedules.json    # Lịch hoạt động
│   └── scenarios/            # Các kịch bản test
│       ├── baseline.json
│       ├── high_occupancy.json
│       └── energy_saving.json
├── scripts/                   # Python scripts
│   ├── generators/
│   │   └── idf_generator.py  # Generate IDF từ JSON
│   ├── runners/
│   │   ├── run_simulation.py # Chạy EnergyPlus
│   │   └── batch_runner.py   # Chạy nhiều kịch bản
│   ├── parsers/
│   │   └── result_parser.py  # Parse kết quả
│   └── utils/
│       └── helpers.py        # Utility functions
├── outputs/                   # Kết quả
│   ├── idf/                  # File IDF đã generate
│   ├── results/              # Kết quả simulation
│   └── logs/                 # Log files
├── data/
│   └── weather/              # Weather files (.epw)
├── main.py                   # Script chính
├── requirements.txt
└── README.md
```

## 🚀 Cài đặt

### 1. Cài đặt EnergyPlus

Download và cài đặt EnergyPlus từ: https://energyplus.net/downloads

**Khuyến nghị**: EnergyPlus 9.6 hoặc 23.2

### 2. Cài đặt Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Download Weather File

Download weather file cho TP. Hồ Chí Minh từ: https://energyplus.net/weather

Tìm kiếm: **Vietnam, Ho Chi Minh City**

Lưu file `.epw` vào thư mục `data/weather/`

## 📖 Hướng dẫn sử dụng

### Chạy một kịch bản đơn lẻ

```bash
# Generate IDF file
python main.py generate --scenario config/scenarios/generic_scenario.json

# Chạy simulation
python main.py run --scenario config/scenarios/generic_scenario.json

# Hoặc chạy kịch bản khác
python main.py run --scenario config/scenarios/scheduled_scenario.json
python main.py run --scenario config/scenarios/surveys_scenario.json
```

### Chạy tất cả kịch bản

```bash
# Chạy tuần tự
python main.py run-all

# Chạy song song (nhanh hơn)
python main.py run-all --parallel --max-workers 4

# Chạy và tạo báo cáo so sánh
python main.py run-all --parallel --compare
```

### Tạo báo cáo so sánh

```bash
python main.py compare
```

### Tạo báo cáo cho một kịch bản

```bash
python main.py report --scenario-name baseline --result-dir outputs/results/baseline
```

## 🎯 Tạo kịch bản mới

1. Copy một file scenario hiện có:
```bash
cp config/scenarios/generic_scenario.json config/scenarios/my_scenario.json
```

2. Chỉnh sửa file JSON:
```json
{
  "scenario_name": "My_Scenario",
  "description": "Mô tả kịch bản của bạn",
  
  "overrides": {
    "hvac": {
      "thermostat": {
        "cooling_setpoint": 25.0
      }
    },
    "schedules": {
      "occupancy_data": {
        "max_occupants": 6
      }
    }
  }
}
```

3. Chạy kịch bản mới:
```bash
python main.py run --scenario config/scenarios/my_scenario.json
```

## 📊 Các kịch bản có sẵn

### 1. Generic Scenario (Kịch bản chung)
- **Mô tả**: Kịch bản với số người ngẫu nhiên theo trọng số
- **Đặc điểm**:
  - Giờ làm việc: 8h-17h, Thứ 2 - Thứ 6
  - Số người: 4-8 người
  - Phân bố: 60% có 6 người, 40% random từ 4-8 người
  - Mỗi giờ sẽ random lại số người theo phân bố trên
- **File**: `config/scenarios/generic_scenario.json`

### 2. Scheduled Scenario (Kịch bản theo lịch)
- **Mô tả**: Kịch bản với lịch cố định theo giờ
- **Đặc điểm**:
  - 8h: 4 người (50% - đến sớm)
  - 9h: 6 người (75% - đã đến đủ)
  - 10-11h: 8 người (100% - đầy đủ)
  - 12h: 5 người (62.5% - giờ ăn trưa)
  - 13h: 6 người (75% - trở lại)
  - 14-15h: 8 người (100% - đầy đủ)
  - 16h: 7 người (87.5% - bắt đầu về)
  - 17h: 4 người (50% - cuối ngày)
- **File**: `config/scenarios/scheduled_scenario.json`

### 3. Surveys Scenario (Kịch bản khảo sát)
- **Mô tả**: Kịch bản dựa trên dữ liệu khảo sát thực tế
- **Đặc điểm**:
  - Dữ liệu từ khảo sát 2 tuần (Jan 2024)
  - Số người trung bình theo giờ từ khảo sát
  - Nhiệt độ ưa thích: 24°C (từ khảo sát)
  - Độ ẩm ưa thích: 50-60%
  - Phản ánh hành vi thực tế: họp, nghỉ trưa, làm việc linh hoạt
- **File**: `config/scenarios/surveys_scenario.json`

## 📈 So sánh kịch bản

Các kịch bản này cho phép bạn so sánh:
- **Generic vs Scheduled**: So sánh giữa mô hình ngẫu nhiên và lịch cố định
- **Generic vs Surveys**: So sánh mô hình lý thuyết với dữ liệu thực tế
- **Scheduled vs Surveys**: So sánh lịch dự đoán với hành vi thực tế từ khảo sát
- Đánh giá ảnh hưởng của các mô hình occupancy khác nhau đến năng lượng HVAC


## 🔧 Tùy chỉnh cấu hình

### Geometry (geometry.json)
```json
{
  "dimensions": {
    "length": 6.0,    // Chiều dài phòng (m)
    "width": 4.0,     // Chiều rộng (m)
    "height": 3.0     // Chiều cao (m)
  },
  "windows": [
    {
      "name": "Window_South",
      "wall": "South",
      "width": 2.0,
      "height": 1.5
    }
  ]
}
```

### HVAC (hvac_config.json)
```json
{
  "thermostat": {
    "heating_setpoint": 20.0,  // °C
    "cooling_setpoint": 24.0   // °C
  }
}
```

### Schedules (schedules.json)
```json
{
  "occupancy_data": {
    "max_occupants": 4,
    "activity_level": 120  // W/person
  },
  "lighting_data": {
    "power_density": 10.0  // W/m²
  }
}
```

## 📈 Kết quả

Sau khi chạy simulation, kết quả sẽ được lưu trong `outputs/results/<scenario_name>/`:

- `eplusout.csv` - Dữ liệu hourly
- `eplustbl.htm` - Báo cáo HTML
- `report.json` - Metrics tổng hợp
- `plots/` - Biểu đồ
  - `*_temperature.png` - Biểu đồ nhiệt độ
  - `*_energy.png` - Biểu đồ năng lượng

### Metrics được tính toán

- ⚡ **Năng lượng**:
  - Cooling energy (kWh)
  - Heating energy (kWh)
  - Lighting energy (kWh)
  - Equipment energy (kWh)
  - Total energy (kWh)

- 🌡️ **Nhiệt độ**:
  - Trung bình, min, max (°C)

- 💧 **Độ ẩm**:
  - Trung bình, min, max (%)

## 🐛 Troubleshooting

### EnergyPlus không tìm thấy

```bash
# Chỉ định đường dẫn EnergyPlus
python main.py run --scenario config/scenarios/baseline.json \
  --energyplus-path /usr/local/EnergyPlus-9-6-0/energyplus
```

### Weather file không tìm thấy

1. Download từ: https://energyplus.net/weather
2. Lưu vào `data/weather/`
3. Đảm bảo tên file trong scenario JSON khớp với tên file thực tế

### Lỗi khi chạy simulation

Kiểm tra file `.err` trong output directory:
```bash
cat outputs/results/<scenario_name>/eplusout.err
```

## 🔬 Tích hợp dữ liệu sensor

Để tích hợp dữ liệu sensor thực tế:

1. Lưu dữ liệu sensor vào `data/sensor_data/`
2. Sử dụng dữ liệu để calibrate model
3. So sánh kết quả simulation với dữ liệu thực tế

## 📚 Tài liệu tham khảo

- [EnergyPlus Documentation](https://energyplus.net/documentation)
- [EnergyPlus Weather Data](https://energyplus.net/weather)
- [Input Output Reference](https://energyplus.net/documentation)

## 💡 Tips

1. **Bắt đầu với baseline**: Luôn chạy baseline trước để có tham chiếu
2. **Chạy song song**: Sử dụng `--parallel` khi có nhiều kịch bản
3. **Kiểm tra .err file**: Luôn kiểm tra file .err để phát hiện warnings/errors
4. **Calibrate model**: So sánh với dữ liệu sensor để điều chỉnh parameters
5. **Backup configs**: Lưu lại các config files trước khi thay đổi lớn

## 🤝 Đóng góp

Nếu bạn muốn thêm features hoặc cải thiện hệ thống:

1. Thêm kịch bản mới trong `config/scenarios/`
2. Mở rộng IDF generator để hỗ trợ thêm objects
3. Thêm metrics mới trong result parser
4. Tạo visualization mới

## 📝 License

MIT License

## 👤 Tác giả

Hệ thống được xây dựng để hỗ trợ nghiên cứu mô phỏng năng lượng tòa nhà.

---

**Lưu ý**: Đây là hệ thống cho **một phòng làm việc**. Nếu muốn mở rộng sang toàn tòa nhà, cần điều chỉnh geometry và thêm nhiều zones.
