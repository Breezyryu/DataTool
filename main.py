#!/usr/bin/env python
"""
배터리 테스트 데이터 자동 처리 도구

사용법:
    python main.py <data_path> [--output-dir OUTPUT_DIR] [--verbose]
    
예시:
    python main.py "D:/pne/LGES_G3_MP1_4352mAh_상온수명"
    python main.py "D:/toyo/battery_data" --output-dir "results/"
"""

import argparse
import sys
import logging
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from src.battery_data_processor import BatteryDataProcessor
from src.utils import validate_data_path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('battery_processing.log')
    ]
)
logger = logging.getLogger(__name__)


def main():
    """메인 함수 - 경로만 입력받아 모든 처리를 자동 실행"""
    parser = argparse.ArgumentParser(
        description="배터리 테스트 데이터 자동 처리 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
자동 실행 기능:
  • 모든 채널 데이터 로드
  • 채널별 + 병합된 CSV 파일 출력
  • 모든 시각화 차트 생성
  • 통계 요약 출력

예시:
  python main.py "D:/pne/LGES_G3_MP1_4352mAh_상온수명"
  python main.py "D:/toyo/battery_data" --output-dir "results/"
        """
    )
    
    # 필수 인수
    parser.add_argument(
        'data_path',
        type=str,
        help='배터리 테스트 데이터 디렉토리 경로'
    )
    
    # 선택적 인수 (최소한으로 유지)
    parser.add_argument(
        '--output-dir',
        type=str,
        default=None,
        help='출력 디렉토리 (기본값: data_path/processed_data)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='상세 로그 출력'
    )
    
    args = parser.parse_args()
    
    # 로깅 레벨 설정
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # 데이터 경로 검증
    logger.info(f"🔍 데이터 경로 검증 중: {args.data_path}")
    
    is_valid, message = validate_data_path(args.data_path)
    if not is_valid:
        logger.error(f"❌ 유효하지 않은 데이터 경로: {message}")
        sys.exit(1)
    
    logger.info(f"✅ {message}")
    
    try:
        # 프로세서 초기화
        logger.info("🚀 배터리 데이터 프로세서 초기화 중...")
        processor = BatteryDataProcessor(args.data_path)
        
        # 배터리 정보 출력
        logger.info("📋 배터리 정보:")
        for key, value in processor.battery_info.items():
            if value is not None:
                logger.info(f"  • {key}: {value}")
        
        logger.info(f"  • 장비 타입: {processor.equipment_type}")
        
        # 1. 데이터 로드 (모든 채널)
        logger.info("📂 배터리 테스트 데이터 로드 중...")
        channel_data = processor.load_data()  # 모든 채널 자동 로드
        
        if not channel_data:
            logger.error("❌ 로드된 데이터가 없습니다")
            sys.exit(1)
        
        # 채널 병합
        merged_data = processor.merge_channels()
        logger.info(f"✅ 총 데이터 행 수: {len(merged_data):,}")
        
        # 2. 통계 요약 자동 출력
        logger.info("📊 통계 요약:")
        stats = processor.get_summary_statistics()
        for key, value in stats.items():
            if key != 'battery_info':  # 이미 출력했으므로 제외
                if isinstance(value, (int, float)):
                    logger.info(f"  • {key}: {value:,}")
                else:
                    logger.info(f"  • {key}: {value}")
        
        # 출력 디렉토리 설정
        if args.output_dir:
            output_path = args.output_dir
            plots_dir = Path(args.output_dir) / "plots"
        else:
            output_path = None  # 기본 위치 사용
            plots_dir = Path(processor.data_path) / "processed_data" / "plots"
        
        # 3. CSV 자동 출력 (병합 + 채널별)
        logger.info("💾 CSV 파일 출력 중...")
        exported_files = processor.export_to_csv(
            output_path=output_path,
            separate_channels=True  # 채널별 파일도 생성
        )
        logger.info(f"✅ {len(exported_files)}개 파일 출력 완료:")
        for file_path in exported_files:
            logger.info(f"  📄 {file_path}")
        
        # 4. 시각화 자동 생성 (모든 차트)
        logger.info("📈 데이터 시각화 생성 중...")
        try:
            plots_dir.mkdir(parents=True, exist_ok=True)
            processor.visualize_data(
                output_dir=str(plots_dir),
                plots=None  # 모든 차트 생성
            )
            logger.info("✅ 시각화 완료")
        except ImportError as e:
            logger.error(f"❌ 시각화 오류: {e}")
            logger.error("필수 패키지를 설치하세요: pip install matplotlib seaborn")
        except Exception as e:
            logger.error(f"❌ 시각화 오류: {e}")
            if args.verbose:
                import traceback
                logger.error(traceback.format_exc())
        
        logger.info("🎉 모든 처리가 성공적으로 완료되었습니다!")
        
        # 최종 결과 요약
        logger.info("\n" + "="*60)
        logger.info("📋 처리 결과 요약")
        logger.info("="*60)
        logger.info(f"• 배터리: {processor.battery_info.get('manufacturer', '')} "
                   f"{processor.battery_info.get('model', '')} "
                   f"{processor.battery_info.get('capacity_mah', '')}mAh")
        logger.info(f"• 장비 타입: {processor.equipment_type}")
        logger.info(f"• 처리된 채널 수: {len(channel_data)}")
        logger.info(f"• 총 데이터 행 수: {len(merged_data):,}")
        logger.info(f"• 출력 파일 수: {len(exported_files)}")
        logger.info("="*60)
        
    except Exception as e:
        logger.error(f"❌ 처리 실패: {e}")
        if args.verbose:
            import traceback
            logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()