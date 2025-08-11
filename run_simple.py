#!/usr/bin/env python
"""
간단한 배터리 데이터 처리 실행 스크립트

사용법:
    python run_simple.py
    
경로를 입력하라는 프롬프트가 나타나면 데이터 경로를 입력하세요.
"""

import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.battery_data_processor import BatteryDataProcessor
from src.utils import validate_data_path


def get_data_path():
    """사용자로부터 데이터 경로 입력받기"""
    print("=" * 60)
    print("🔋 배터리 테스트 데이터 자동 처리 도구")
    print("=" * 60)
    print()
    
    print("📁 데이터 경로 예시:")
    print('  • "D:\\pne\\LGES_G3_MP1_4352mAh_상온수명"')
    print('  • "D:/toyo/battery_data"')
    print('  • "C:\\Users\\data\\Samsung_SDI_2170_3500mAh"')
    print()
    
    while True:
        data_path = input("🔍 배터리 데이터 경로를 입력하세요: ").strip()
        
        if not data_path:
            print("❌ 경로를 입력해주세요.")
            continue
            
        # 따옴표 제거 (사용자가 따옴표와 함께 입력한 경우)
        data_path = data_path.strip('"\'')
        
        # 경로 검증
        is_valid, message = validate_data_path(data_path)
        if is_valid:
            print(f"✅ {message}")
            return data_path
        else:
            print(f"❌ {message}")
            print("다시 입력해주세요.")
            print()


def main():
    """메인 함수"""
    try:
        # 데이터 경로 입력받기
        data_path = get_data_path()
        
        print()
        print("🚀 처리를 시작합니다...")
        print("-" * 60)
        
        # 프로세서 초기화
        processor = BatteryDataProcessor(data_path)
        
        # 배터리 정보 출력
        print("📋 배터리 정보:")
        for key, value in processor.battery_info.items():
            if value is not None:
                print(f"  • {key}: {value}")
        print(f"  • 장비 타입: {processor.equipment_type}")
        print()
        
        # 1. 데이터 로드
        print("📂 데이터 로드 중...")
        channel_data = processor.load_data()
        
        if not channel_data:
            print("❌ 로드된 데이터가 없습니다.")
            return
        
        merged_data = processor.merge_channels()
        print(f"✅ 총 {len(merged_data):,}행의 데이터를 로드했습니다.")
        print()
        
        # 2. 통계 요약
        print("📊 통계 요약:")
        stats = processor.get_summary_statistics()
        for key, value in stats.items():
            if key != 'battery_info':
                if isinstance(value, (int, float)):
                    print(f"  • {key}: {value:,}")
                else:
                    print(f"  • {key}: {value}")
        print()
        
        # 3. CSV 출력
        print("💾 CSV 파일 출력 중...")
        exported_files = processor.export_to_csv(separate_channels=True)
        print(f"✅ {len(exported_files)}개 파일을 출력했습니다:")
        for file_path in exported_files:
            print(f"  📄 {Path(file_path).name}")
        print()
        
        # 4. 시각화
        print("📈 시각화 생성 중...")
        try:
            plots_dir = Path(processor.data_path) / "processed_data" / "plots"
            plots_dir.mkdir(parents=True, exist_ok=True)
            
            processor.visualize_data(
                output_dir=str(plots_dir),
                plots=None  # 모든 차트 생성
            )
            print("✅ 시각화 완료")
        except ImportError:
            print("❌ 시각화 패키지가 설치되지 않았습니다.")
            print("다음 명령어로 설치하세요: pip install matplotlib seaborn")
        except Exception as e:
            print(f"❌ 시각화 오류: {e}")
        
        print()
        print("🎉 모든 처리가 완료되었습니다!")
        print()
        
        # 결과 요약
        print("=" * 60)
        print("📋 처리 결과 요약")
        print("=" * 60)
        print(f"• 배터리: {processor.battery_info.get('manufacturer', '')} "
               f"{processor.battery_info.get('model', '')} "
               f"{processor.battery_info.get('capacity_mah', '')}mAh")
        print(f"• 장비 타입: {processor.equipment_type}")
        print(f"• 처리된 채널 수: {len(channel_data)}")
        print(f"• 총 데이터 행 수: {len(merged_data):,}")
        print(f"• 출력 파일 수: {len(exported_files)}")
        print()
        print(f"📁 출력 위치: {Path(processor.data_path) / 'processed_data'}")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n❌ 사용자에 의해 중단되었습니다.")
    except Exception as e:
        print(f"\n❌ 처리 중 오류가 발생했습니다: {e}")
        print("상세한 오류 정보를 보려면 --verbose 옵션을 사용하세요.")


if __name__ == "__main__":
    main()