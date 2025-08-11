# 배터리 테스트 데이터 처리 도구 (Battery Test Data Processing Tool)

배터리 충방전 테스트 데이터를 전처리하고 분석하는 Python 도구입니다. PNE, Toyo1, Toyo2 장비에서 생성된 데이터를 지원합니다.

## 주요 기능

- ✅ **경로 분석**: 데이터 경로에서 배터리 정보 자동 추출 (제조사, 모델, 용량)
- ✅ **장비 자동 감지**: PNE, Toyo 장비 자동 구분
- ✅ **채널별 데이터 로드**: 다중 채널 데이터 로드 및 병합
- ✅ **CSV 출력**: 처리된 데이터를 CSV 형식으로 저장
- ✅ **데이터 시각화**: 전압/전류 프로파일, 용량 감소, 통계 분석 차트
- ✅ **단위 변환**: µV/µA ↔ V/mA 자동 변환
- ✅ **한국어 지원**: 한국어 파일명 및 경로 처리

## 설치 방법

### 1. Python 환경 설정

```bash
# 가상 환경 생성
python -m venv venv

# 가상 환경 활성화
# Windows:
venv\\Scripts\\activate
# Linux/Mac:
source venv/bin/activate

# 의존성 설치
pip install -r requirements.txt
```

### 2. 필수 패키지

```bash
pip install pandas numpy matplotlib seaborn tqdm
```

## 사용 방법

### 1. 간단한 사용법 (권장)

```bash
# 경로만 입력하면 모든 처리가 자동으로 실행됩니다
python main.py "D:/pne/LGES_G3_MP1_4352mAh_상온수명"

# 출력 디렉토리를 지정하려면
python main.py "D:/toyo/battery_data" --output-dir "results/"

# 상세 로그를 보려면
python main.py "D:/data" --verbose
```

### 2. 대화형 실행

```bash
# 경로를 대화형으로 입력
python run_simple.py
```

### 3. 자동 실행 기능

경로만 입력하면 다음이 모두 자동으로 실행됩니다:
- ✅ 모든 채널 데이터 로드
- ✅ 채널별 + 병합된 CSV 파일 출력  
- ✅ 모든 시각화 차트 생성 (전압/전류, 용량감소, 통계, 채널비교)
- ✅ 통계 요약 출력

### 4. Python 스크립트에서 사용

```python
from src.battery_data_processor import BatteryDataProcessor

# 프로세서 초기화
data_path = "D:/pne/LGES_G3_MP1_4352mAh_상온수명"
processor = BatteryDataProcessor(data_path)

# 자동 처리 (한 번에 모든 기능 실행)
def auto_process(data_path):
    processor = BatteryDataProcessor(data_path)
    
    # 1. 데이터 로드 (모든 채널)
    channel_data = processor.load_data()
    merged_data = processor.merge_channels()
    
    # 2. CSV 출력 (병합 + 채널별)
    exported_files = processor.export_to_csv(separate_channels=True)
    
    # 3. 시각화 (모든 차트)
    processor.visualize_data()
    
    # 4. 통계 정보
    stats = processor.get_summary_statistics()
    
    return stats, exported_files

# 실행
stats, files = auto_process("D:/your/data/path")
```

## 데이터 구조 지원

### PNE 장비
```
data_path/
├── M01Ch003[003]/
│   └── Restore/
│       ├── ch03_SaveData0001.csv
│       ├── ch03_SaveData0002.csv
│       ├── ...
│       ├── savingFileIndex_start.csv
│       └── savingFileIndex_last.csv
├── M01Ch004[004]/
└── ...
```

### Toyo 장비 (Toyo1/Toyo2)
```
data_path/
├── 86/
│   ├── 000001
│   ├── 000002
│   ├── ...
│   └── CAPACITY.LOG
├── 93/
└── ...
```

## 출력 결과

### CSV 파일
- `{battery_info}_{timestamp}_merged.csv`: 모든 채널 병합 데이터
- `{battery_info}_{timestamp}_{channel}.csv`: 채널별 개별 데이터 (--separate-channels 옵션)
- `{battery_info}_{timestamp}_summary.txt`: 처리 요약 정보

### 시각화 차트
- `voltage_current_{timestamp}.png`: 전압/전류 프로파일
- `capacity_fade_{timestamp}.png`: 용량 감소 분석
- `statistics_{timestamp}.png`: 사이클 통계 분석
- `channels_{timestamp}.png`: 채널 간 비교

## 명령줄 옵션 (간소화됨)

| 옵션 | 설명 | 예시 |
|------|------|------|
| `data_path` | 배터리 테스트 데이터 경로 (필수) | `"D:/pne/data"` |
| `--output-dir` | 출력 디렉토리 지정 (선택) | `--output-dir "results/"` |
| `--verbose` | 상세 로그 출력 (선택) | |

**자동 실행되는 기능들:**
- 모든 채널 자동 로드
- CSV 파일 자동 출력 (병합 + 채널별)
- 모든 시각화 차트 자동 생성
- 통계 요약 자동 출력

## 지원되는 데이터 형식

### PNE 데이터
- 46개 컬럼의 상세 테스트 파라미터
- µV, µA 단위 (자동으로 V, mA로 변환)
- 다중 SaveData 파일 자동 병합
- Index 파일을 통한 파일 범위 확인

### Toyo 데이터
- CAPACITY.LOG 요약 정보
- 연속 번호 파일 (000001, 000002, ...)
- V, mA 단위
- 채널별 폴더 구조

## 배터리 정보 자동 추출

데이터 경로에서 다음 정보를 자동으로 추출합니다:

```python
# 경로 예시: "D:/pne/LGES_G3_MP1_4352mAh_상온수명"
{
    'manufacturer': 'LGES',      # 제조사
    'model': 'G3_MP1',          # 모델
    'capacity_mah': 4352,       # 용량 (mAh)
    'test_condition': '상온수명'  # 테스트 조건
}
```

## 문제 해결

### 1. 인코딩 오류
한국어 파일명/경로 처리 시 UTF-8 인코딩을 사용합니다. 문제 발생 시:
```python
# 파일 읽기 시 인코딩 명시적 지정
pd.read_csv(file_path, encoding='utf-8-sig')
```

### 2. 메모리 부족
대용량 데이터 처리 시:
```python
# 청크 단위로 읽기
chunk_size = 10000
for chunk in pd.read_csv(file_path, chunksize=chunk_size):
    process_chunk(chunk)
```

### 3. 의존성 오류
필수 패키지 설치:
```bash
pip install pandas numpy matplotlib seaborn tqdm
```

## 예시 사용 시나리오

### 1. 기본 자동 처리 (가장 간단)
```bash
python main.py "D:/pne/LGES_G3_MP1_4352mAh_상온수명"
```
→ 모든 기능이 자동으로 실행됩니다 (로드, CSV출력, 시각화, 통계)

### 2. 대화형 실행
```bash
python run_simple.py
```
→ 경로를 대화형으로 입력하고 자동 처리

### 3. 커스텀 출력 디렉토리
```bash
python main.py "D:/data" --output-dir "analysis_results/" --verbose
```
→ 지정된 디렉토리에 결과 저장

## 참고사항

- 실제 테스트 데이터는 별도 PC 환경에 저장되어 있어야 합니다
- Reference 폴더는 데이터 구조 예시이며 실제 처리용이 아닙니다
- 대용량 데이터 처리 시 충분한 메모리와 저장 공간을 확보하세요
- 처리 시간은 데이터 크기와 채널 수에 따라 달라집니다

## 라이선스

이 프로젝트는 배터리 테스트 데이터 분석을 위한 내부 도구입니다.