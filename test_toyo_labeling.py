"""
Toyo 데이터 라벨링 테스트 스크립트.
사용자가 제공한 샘플 데이터로 라벨링 기능을 테스트합니다.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from src.toyo_labeling import ToyoDataLabeler, process_toyo_labeling
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_sample_data():
    """샘플 데이터 생성 (사용자 제공 데이터 기반)"""
    
    # Capacity log 샘플 데이터
    capacity_data = {
        'Date': ['2025-02-06', '2025-02-07', None, None, None, None, None, None,
                 None, None, None, None, None, None, None, None, None, None, None, None],
        'Condition': [1, 2, 1, 1, 1, 1, 2, 2,
                     1, 1, 1, 1, 2, 2, 1, 2, 1, 1, 1, 1],
        'Mode': [1, 1, 2, 3, 4, 5, 5, 6,
                2, 3, 4, 5, 5, 6, 7, 7, 8, 9, 10, 11],
        'TotlCycle': [1, 1, 2, 3, 4, 5, 6, 7,
                     487, 488, 489, 490, 490, 491, 492, 492, 493, 494, 495, 496],
        'Cap[mAh]': [889, 1725, 502, 219, 469, 502, 1179, 447,
                    471, 196, 449, 520, 1223, 417, 1669, 1730, 506, 207, 464, 523],
        'Finish': ['Cur', 'Vol', 'Vol', 'Vol', 'Cur', 'Cur', 'Vol', 'Vol',
                  'Vol', 'Vol', 'Cur', 'Cur', 'Vol', 'Vol', 'Cur', 'Vol', 'Vol', 'Vol', 'Cur', 'Cur'],
        'DchCycle': [0, 1, 1, 1, 1, 1, 2, 3,
                    195, 195, 195, 195, 196, 197, 197, 198, 198, 198, 198, 198]
    }
    
    capacity_df = pd.DataFrame(capacity_data)
    
    # Raw data 샘플 데이터
    raw_data = {
        'Date': ['2025-02-06', '2025-02-06', '2025-02-06', '2025-02-06', '2025-02-07'] * 4,
        'Time': ['22:39:00', '22:39:00', '22:49:06', '22:49:06', '3:55:48'] * 4,
        'PassTime[Sec]': [10482, 0, 606, 0, 18402] * 4,
        'Voltage': [4.4995, 4.4995, 4.4895, 4.4895, 2.7425] * 4,
        'Current': [33.6, 0, 0, 0, 337.7] * 4,
        'Temp1[Deg]': [23.65, 23.65, 23.25, 23.25, 23.45] * 4,
        'Condition': [1, 0, 0, 2, 2] * 4,
        'Mode': [1, 1, 1, 1, 1] * 4,
        'Cycle': [1, 1, 1, 1, 1] * 4,
        'TotlCycle': [1, 1, 1, 1, 1] * 4
    }
    
    raw_df = pd.DataFrame(raw_data)
    
    return capacity_df, raw_df


def test_labeling():
    """라벨링 기능 테스트"""
    
    print("=" * 80)
    print("Toyo 데이터 라벨링 테스트")
    print("=" * 80)
    
    # 샘플 데이터 생성
    capacity_df, raw_df = create_sample_data()
    
    print("\n1. 원본 Capacity Log 데이터 (처음 10행):")
    print(capacity_df.head(10))
    
    print("\n2. 원본 Raw Data 데이터 (처음 5행):")
    print(raw_df.head())
    
    # 라벨러 초기화 (정격 용량 1730mAh 사용)
    labeler = ToyoDataLabeler(rated_capacity_mah=1730.0)
    
    # Capacity log 라벨링
    print("\n3. Capacity Log 라벨링 처리중...")
    labeled_capacity = labeler.label_capacity_log(capacity_df, raw_df)
    
    print("\n4. 라벨링된 Capacity Log (처음 10행):")
    print(labeled_capacity[['TotlCycle', 'Cap[mAh]', 'Finish', '계산cycle', '패턴', '스텝', 'C-rate']].head(10))
    
    print("\n5. 보증 패턴 데이터:")
    warranty_data = labeled_capacity[labeled_capacity['패턴'] == '보증']
    print(warranty_data[['TotlCycle', 'Cap[mAh]', '계산cycle', '패턴', '스텝', 'C-rate']].head())
    
    print("\n6. 수명 패턴 데이터:")
    life_data = labeled_capacity[labeled_capacity['패턴'] == '수명']
    print(life_data[['TotlCycle', 'Cap[mAh]', '계산cycle', '패턴', '스텝', 'C-rate']].head(8))
    
    # Raw data 라벨링
    print("\n7. Raw Data 라벨링 처리중...")
    labeled_raw = labeler.label_raw_data(raw_df, labeled_capacity)
    
    print("\n8. 라벨링된 Raw Data (처음 5행):")
    print(labeled_raw[['Voltage', 'Current', 'C-rate', '패턴', '스텝']].head())
    
    # 파일로 저장
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)
    
    labeled_capacity.to_csv(output_dir / "capacity_log_labeled.csv", index=False, encoding='utf-8-sig')
    labeled_raw.to_csv(output_dir / "raw_data_labeled.csv", index=False, encoding='utf-8-sig')
    
    print(f"\n9. 라벨링된 데이터가 저장되었습니다:")
    print(f"   - {output_dir / 'capacity_log_labeled.csv'}")
    print(f"   - {output_dir / 'raw_data_labeled.csv'}")
    
    # 통계 출력
    print("\n10. 라벨링 통계:")
    print(f"   - 전체 사이클 수: {labeled_capacity['계산cycle'].max()}")
    print(f"   - 보증 패턴 수: {len(labeled_capacity[labeled_capacity['패턴'] == '보증'])}")
    print(f"   - 수명 패턴 수: {len(labeled_capacity[labeled_capacity['패턴'] == '수명'])}")
    print(f"   - C-rate 범위: {labeled_capacity['C-rate'].min():.3f} ~ {labeled_capacity['C-rate'].max():.3f}")
    
    print("\n테스트 완료!")
    

def test_with_real_files():
    """실제 파일을 사용한 테스트 (파일이 있는 경우)"""
    
    # 테스트용 파일 경로 (실제 파일이 있는 경우 수정)
    capacity_file = Path("test_data/capacity_log.csv")
    raw_file = Path("test_data/raw_data.csv")
    
    if capacity_file.exists():
        print("\n실제 파일을 사용한 테스트:")
        print("=" * 80)
        
        labeled_capacity, labeled_raw = process_toyo_labeling(
            capacity_file=capacity_file,
            raw_file=raw_file if raw_file.exists() else None,
            rated_capacity=1730.0
        )
        
        print(f"Capacity log 라벨링 완료: {len(labeled_capacity)} rows")
        if labeled_raw is not None:
            print(f"Raw data 라벨링 완료: {len(labeled_raw)} rows")
        
        # 결과 저장
        output_dir = Path("test_output")
        output_dir.mkdir(exist_ok=True)
        
        labeled_capacity.to_csv(output_dir / "real_capacity_labeled.csv", index=False, encoding='utf-8-sig')
        if labeled_raw is not None:
            labeled_raw.to_csv(output_dir / "real_raw_labeled.csv", index=False, encoding='utf-8-sig')
        
        print(f"결과가 {output_dir}에 저장되었습니다.")
    else:
        print(f"\n실제 파일 테스트를 위해 {capacity_file} 파일이 필요합니다.")


if __name__ == "__main__":
    # 샘플 데이터로 테스트
    test_labeling()
    
    # 실제 파일이 있으면 테스트 (선택사항)
    test_with_real_files()