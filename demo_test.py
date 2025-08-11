#!/usr/bin/env python
"""
Demo test script to verify the simplified main.py functionality.
"""

import sys
import tempfile
import shutil
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.battery_data_processor import BatteryDataProcessor
from src.utils import validate_data_path


def create_demo_pne_structure():
    """Create a demo PNE data structure for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    demo_path = temp_dir / "LGES_G3_MP1_4352mAh_상온수명"
    demo_path.mkdir(parents=True)
    
    # Create M01Ch003[003] folder structure
    channel_dir = demo_path / "M01Ch003[003]"
    restore_dir = channel_dir / "Restore"
    restore_dir.mkdir(parents=True)
    
    # Copy sample data from Reference folder
    reference_path = Path(__file__).parent / "Reference" / "PNE"
    if reference_path.exists():
        for file_name in ["ch03_SaveData0001.csv", "savingFileIndex_start.csv", "savingFileIndex_last.csv"]:
            src_file = reference_path / file_name
            if src_file.exists():
                dst_file = restore_dir / file_name
                shutil.copy2(src_file, dst_file)
                print(f"Copied {file_name}")
    
    return demo_path


def create_demo_toyo_structure():
    """Create a demo Toyo data structure for testing."""
    temp_dir = Path(tempfile.mkdtemp())
    demo_path = temp_dir / "Samsung_SDI_2170_3500mAh_고온수명"
    demo_path.mkdir(parents=True)
    
    # Create channel folder (86)
    channel_dir = demo_path / "86"
    channel_dir.mkdir()
    
    # Copy sample data from Reference folder
    reference_path = Path(__file__).parent / "Reference" / "Toyo"
    if reference_path.exists():
        for file_name in ["000001", "CAPACITY.LOG"]:
            src_file = reference_path / file_name
            if src_file.exists():
                dst_file = channel_dir / file_name
                shutil.copy2(src_file, dst_file)
                print(f"Copied {file_name}")
    
    return demo_path


def test_simplified_processing():
    """Test the simplified processing functionality."""
    print("배터리 데이터 처리 도구 데모 테스트")
    print("=" * 60)
    
    # Test PNE structure
    print("\\n1. PNE 구조 테스트")
    print("-" * 30)
    try:
        demo_pne_path = create_demo_pne_structure()
        print(f"데모 PNE 경로 생성: {demo_pne_path}")
        
        # Validate path
        is_valid, message = validate_data_path(demo_pne_path)
        print(f"경로 검증: {message}")
        
        if is_valid:
            processor = BatteryDataProcessor(demo_pne_path)
            print(f"장비 타입: {processor.equipment_type}")
            
            # Try to load data (limited for demo)
            try:
                channel_data = processor.load_data()
                print(f"로드된 채널 수: {len(channel_data)}")
                
                if channel_data:
                    merged_data = processor.merge_channels()
                    print(f"병합된 데이터 행 수: {len(merged_data)}")
                    
                    # Test CSV export
                    exported_files = processor.export_to_csv(separate_channels=False)
                    print(f"출력된 파일 수: {len(exported_files)}")
                    
            except Exception as e:
                print(f"데이터 처리 중 오류: {e}")
        
        # Cleanup
        shutil.rmtree(demo_pne_path.parent)
        
    except Exception as e:
        print(f"PNE 테스트 오류: {e}")
    
    # Test Toyo structure
    print("\\n2. Toyo 구조 테스트")
    print("-" * 30)
    try:
        demo_toyo_path = create_demo_toyo_structure()
        print(f"데모 Toyo 경로 생성: {demo_toyo_path}")
        
        # Validate path
        is_valid, message = validate_data_path(demo_toyo_path)
        print(f"경로 검증: {message}")
        
        if is_valid:
            processor = BatteryDataProcessor(demo_toyo_path)
            print(f"장비 타입: {processor.equipment_type}")
            
            # Try to load data (limited for demo)
            try:
                channel_data = processor.load_data()
                print(f"로드된 채널 수: {len(channel_data)}")
                
                if channel_data:
                    merged_data = processor.merge_channels()
                    print(f"병합된 데이터 행 수: {len(merged_data)}")
                    
                    # Test statistics
                    stats = processor.get_summary_statistics()
                    print(f"통계 정보: {len(stats)} 항목")
                    
            except Exception as e:
                print(f"데이터 처리 중 오류: {e}")
        
        # Cleanup
        shutil.rmtree(demo_toyo_path.parent)
        
    except Exception as e:
        print(f"Toyo 테스트 오류: {e}")
    
    print("\\n데모 테스트 완료!")
    print("=" * 60)
    print("실제 사용법:")
    print('  python main.py "D:/your/battery/data/path"')
    print('  python run_simple.py')


if __name__ == "__main__":
    test_simplified_processing()