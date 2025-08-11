"""
Toyo 장비 데이터에 대한 라벨링 기능 모듈.
사이클, 패턴, 스텝, C-rate, Cutoff 조건을 자동으로 추가합니다.
"""

import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, Optional, Tuple, Union
import logging

logger = logging.getLogger(__name__)


class ToyoDataLabeler:
    """Toyo 데이터 라벨링 클래스"""
    
    def __init__(self, rated_capacity_mah: float = 1730.0):
        """
        초기화.
        
        Args:
            rated_capacity_mah: 정격 용량 (mAh), C-rate 계산에 사용
        """
        self.rated_capacity = rated_capacity_mah
        
    def label_capacity_log(self, capacity_df: pd.DataFrame, raw_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        capacity_log 데이터에 라벨링 정보 추가.
        
        Args:
            capacity_df: CAPACITY.LOG 데이터
            raw_df: raw data (전류/전압 정보 추출용)
            
        Returns:
            라벨링된 DataFrame
        """
        df = capacity_df.copy()
        
        # 계산 사이클 추가
        df['계산cycle'] = self._calculate_cycles(df)
        
        # 패턴 분류
        df['패턴'] = self._classify_patterns(df)
        
        # 스텝 정의
        df['스텝'] = self._define_steps(df)
        
        # C-rate 계산 (raw_data가 있는 경우)
        if raw_df is not None:
            df['C-rate'] = self._calculate_crate(df, raw_df)
            df['Cutoff-Voltage'] = self._extract_cutoff_voltage(df, raw_df)
            df['Cutoff-Current'] = self._extract_cutoff_current(df, raw_df)
        else:
            # raw_data가 없으면 Cap[mAh]와 Mode를 기준으로 추정
            df['C-rate'] = self._estimate_crate_from_capacity(df)
            df['Cutoff-Voltage'] = None
            df['Cutoff-Current'] = None
        
        return df
    
    def _calculate_cycles(self, df: pd.DataFrame) -> pd.Series:
        """
        실제 사이클 번호 계산.
        Condition과 Mode 변경을 기준으로 사이클 증가.
        """
        cycles = []
        current_cycle = 0
        prev_condition = None
        prev_mode = None
        
        for idx, row in df.iterrows():
            # 첫 행이거나 Condition이 1로 변경되면 새 사이클
            if prev_condition is None or (row['Condition'] == 1 and prev_condition != 1):
                current_cycle += 1
            
            cycles.append(current_cycle)
            prev_condition = row['Condition']
            prev_mode = row['Mode']
        
        return pd.Series(cycles, index=df.index)
    
    def _classify_patterns(self, df: pd.DataFrame) -> pd.Series:
        """
        패턴 분류: 보증(100 사이클마다) vs 수명(나머지).
        """
        patterns = []
        
        for idx, row in df.iterrows():
            cycle = row.get('계산cycle', 0)
            
            # 1, 100, 200, 300... 사이클은 보증 패턴
            if cycle == 1 or (cycle > 0 and cycle % 100 == 0):
                patterns.append('보증')
            else:
                patterns.append('수명')
        
        return pd.Series(patterns, index=df.index)
    
    def _define_steps(self, df: pd.DataFrame) -> pd.Series:
        """
        스텝 정의.
        보증 패턴: 충전/방전
        수명 패턴: step1~4 충전, step1~2 방전
        """
        steps = []
        
        for idx, row in df.iterrows():
            pattern = row.get('패턴', '')
            mode = row.get('Mode', 0)
            condition = row.get('Condition', 0)
            
            if pattern == '보증':
                # Mode 1: 충전, Mode 2 이상: 방전
                if condition == 1:
                    steps.append('충전')
                else:
                    steps.append('방전')
            elif pattern == '수명':
                # Condition과 Mode 조합으로 스텝 결정
                if condition == 1:
                    # 충전 스텝
                    if mode <= 2:
                        steps.append('step1 CC충전')
                    elif mode == 3:
                        steps.append('step2 CC충전')
                    elif mode == 4:
                        steps.append('step3 CCCV충전')
                    elif mode >= 5:
                        steps.append('step4 CCCV충전')
                    else:
                        steps.append('충전')
                else:
                    # 방전 스텝
                    if mode <= 5:
                        steps.append('step1 방전')
                    else:
                        steps.append('step2 방전')
            else:
                steps.append('')
        
        return pd.Series(steps, index=df.index)
    
    def _calculate_crate(self, capacity_df: pd.DataFrame, raw_df: pd.DataFrame) -> pd.Series:
        """
        raw_data에서 전류값을 추출하여 C-rate 계산.
        C-rate = Current(mA) / Rated_Capacity(mAh)
        """
        crates = []
        
        for idx, row in capacity_df.iterrows():
            totl_cycle = row.get('TotlCycle', 0)
            condition = row.get('Condition', 0)
            mode = row.get('Mode', 0)
            
            # raw_data에서 해당 조건의 데이터 찾기
            mask = (raw_df['TotlCycle'] == totl_cycle) & \
                   (raw_df['Condition'] == condition) & \
                   (raw_df['Mode'] == mode)
            
            if mask.any():
                # 해당 구간의 평균 전류 계산 (0이 아닌 값들의 평균)
                current_data = raw_df.loc[mask, 'Current']
                non_zero_current = current_data[current_data != 0]
                
                if len(non_zero_current) > 0:
                    avg_current = abs(non_zero_current.mean())
                    c_rate = avg_current / self.rated_capacity
                    crates.append(round(c_rate, 3))
                else:
                    crates.append(0.0)
            else:
                # raw_data에서 찾을 수 없으면 Cap[mAh]로 추정
                cap = row.get('Cap[mAh]', 0)
                if cap > 0:
                    # 보증 패턴은 대체로 0.2C, 수명 패턴은 다양
                    if row.get('패턴') == '보증':
                        crates.append(0.2)
                    else:
                        # 수명 패턴의 경우 용량으로 대략 추정
                        if cap < 300:  # 낮은 용량 = 높은 C-rate
                            crates.append(1.0)
                        elif cap < 600:
                            crates.append(0.5)
                        else:
                            crates.append(0.3)
                else:
                    crates.append(0.0)
        
        return pd.Series(crates, index=capacity_df.index)
    
    def _estimate_crate_from_capacity(self, df: pd.DataFrame) -> pd.Series:
        """
        raw_data가 없을 때 용량과 패턴으로 C-rate 추정.
        """
        crates = []
        
        for idx, row in df.iterrows():
            pattern = row.get('패턴', '')
            cap = row.get('Cap[mAh]', 0)
            step = row.get('스텝', '')
            
            if pattern == '보증':
                # 보증 패턴은 일반적으로 0.2C
                crates.append(0.2)
            elif pattern == '수명':
                # 수명 패턴은 스텝별로 다름
                if 'step1' in step:
                    crates.append(0.5)  # Step1은 대체로 0.5C
                elif 'step2' in step:
                    if '충전' in step:
                        crates.append(0.3)
                    else:
                        crates.append(0.5)
                elif 'step3' in step or 'step4' in step:
                    crates.append(0.5)  # CCCV 충전
                else:
                    # 용량 기반 추정
                    if cap > 1500:
                        crates.append(0.7)
                    elif cap > 1000:
                        crates.append(0.5)
                    elif cap > 500:
                        crates.append(0.3)
                    else:
                        crates.append(0.2)
            else:
                crates.append(0.0)
        
        return pd.Series(crates, index=df.index)
    
    def _extract_cutoff_voltage(self, capacity_df: pd.DataFrame, raw_df: pd.DataFrame) -> pd.Series:
        """
        종료 시점의 전압값 추출.
        """
        voltages = []
        
        for idx, row in capacity_df.iterrows():
            if row.get('Finish') == 'Vol':
                totl_cycle = row.get('TotlCycle', 0)
                condition = row.get('Condition', 0)
                mode = row.get('Mode', 0)
                
                # raw_data에서 해당 조건의 마지막 데이터 찾기
                mask = (raw_df['TotlCycle'] == totl_cycle) & \
                       (raw_df['Condition'] == condition) & \
                       (raw_df['Mode'] == mode)
                
                if mask.any():
                    # 마지막 전압값
                    last_voltage = raw_df.loc[mask, 'Voltage'].iloc[-1]
                    voltages.append(round(last_voltage, 4))
                else:
                    # 기본값 설정
                    if '충전' in row.get('스텝', ''):
                        voltages.append(4.5)  # 충전 종료 전압
                    else:
                        voltages.append(2.75)  # 방전 종료 전압
            else:
                voltages.append(None)
        
        return pd.Series(voltages, index=capacity_df.index)
    
    def _extract_cutoff_current(self, capacity_df: pd.DataFrame, raw_df: pd.DataFrame) -> pd.Series:
        """
        종료 시점의 전류값 추출 (CV 충전 종료 전류).
        """
        currents = []
        
        for idx, row in capacity_df.iterrows():
            if row.get('Finish') == 'Cur':
                totl_cycle = row.get('TotlCycle', 0)
                condition = row.get('Condition', 0)
                mode = row.get('Mode', 0)
                
                # raw_data에서 해당 조건의 마지막 데이터 찾기
                mask = (raw_df['TotlCycle'] == totl_cycle) & \
                       (raw_df['Condition'] == condition) & \
                       (raw_df['Mode'] == mode)
                
                if mask.any():
                    # 마지막 전류값
                    last_current = abs(raw_df.loc[mask, 'Current'].iloc[-1])
                    currents.append(round(last_current, 1))
                else:
                    # 기본값: 0.05C (약 87mA)
                    currents.append(87.0)
            else:
                currents.append(None)
        
        return pd.Series(currents, index=capacity_df.index)
    
    def label_raw_data(self, raw_df: pd.DataFrame, capacity_df: Optional[pd.DataFrame] = None) -> pd.DataFrame:
        """
        raw_data에 라벨링 정보 추가.
        
        Args:
            raw_df: raw data
            capacity_df: 라벨링된 capacity_log (참조용)
            
        Returns:
            라벨링된 raw_data DataFrame
        """
        df = raw_df.copy()
        
        # C-rate 계산 (실시간)
        df['C-rate'] = abs(df['Current']) / self.rated_capacity
        df['C-rate'] = df['C-rate'].round(3)
        
        # capacity_df가 있으면 패턴 정보 병합
        if capacity_df is not None and '패턴' in capacity_df.columns:
            # TotlCycle 기준으로 패턴 정보 매핑
            pattern_map = {}
            step_map = {}
            
            for idx, row in capacity_df.iterrows():
                key = (row['TotlCycle'], row['Condition'], row['Mode'])
                pattern_map[key] = row.get('패턴', '')
                step_map[key] = row.get('스텝', '')
            
            # raw_data에 패턴과 스텝 추가
            patterns = []
            steps = []
            
            for idx, row in df.iterrows():
                key = (row.get('TotlCycle', 0), row.get('Condition', 0), row.get('Mode', 0))
                patterns.append(pattern_map.get(key, ''))
                steps.append(step_map.get(key, ''))
            
            df['패턴'] = patterns
            df['스텝'] = steps
        
        return df


def process_toyo_labeling(capacity_file: Union[str, Path], 
                         raw_file: Optional[Union[str, Path]] = None,
                         rated_capacity: float = 1730.0) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Toyo 데이터 파일을 읽어서 라벨링 처리.
    
    Args:
        capacity_file: CAPACITY.LOG 파일 경로
        raw_file: raw data 파일 경로 (선택)
        rated_capacity: 정격 용량 (mAh)
        
    Returns:
        (라벨링된 capacity_df, 라벨링된 raw_df)
    """
    # 라벨러 초기화
    labeler = ToyoDataLabeler(rated_capacity)
    
    # capacity_log 읽기
    capacity_df = pd.read_csv(capacity_file, encoding='utf-8-sig')
    logger.info(f"Loaded capacity log: {len(capacity_df)} rows")
    
    # raw_data 읽기 (있는 경우)
    raw_df = None
    if raw_file and Path(raw_file).exists():
        raw_df = pd.read_csv(raw_file, encoding='utf-8-sig')
        logger.info(f"Loaded raw data: {len(raw_df)} rows")
    
    # capacity_log 라벨링
    labeled_capacity = labeler.label_capacity_log(capacity_df, raw_df)
    
    # raw_data 라벨링 (있는 경우)
    labeled_raw = None
    if raw_df is not None:
        labeled_raw = labeler.label_raw_data(raw_df, labeled_capacity)
    
    return labeled_capacity, labeled_raw