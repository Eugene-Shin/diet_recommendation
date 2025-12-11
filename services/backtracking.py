import pandas as pd
import random
import time
import sys
from typing import List, Dict, Optional, Tuple

sys.setrecursionlimit(3000)

from models.user_info import UserInfo


class BacktrackingService:
    def __init__(self, db_path: str):
        self.df = self._load_nutrition_data(db_path)
        if self.df is None:
            raise FileNotFoundError(f"'{db_path}'에서 데이터를 불러오는 데 실패했습니다.")

        self.df = self.df[self.df['에너지(kcal)'] > 0]
        self.food_list = self.df.to_dict('records')
        print(f"전체 {len(self.food_list)}개 식품 데이터를 사용합니다. (백트래킹용)")

    def _load_nutrition_data(self, file_path: str) -> Optional[pd.DataFrame]:
        """Excel 파일에서 영양 데이터를 불러옵니다. (GreedyService와 동일)"""
        try:
            df = pd.read_excel(file_path)
            required_cols = ['식품명', '분류', '에너지(kcal)', '단백질(g)', '지방(g)', '탄수화물(g)']
            df = df[required_cols]
            for col in required_cols[2:]:
                df[col] = pd.to_numeric(df[col], errors='coerce')

            df['분류'] = df['분류'].fillna('기타')
            df = df.fillna(0)

            return df
        except FileNotFoundError:
            print(f"오류: '{file_path}' 경로에서 파일을 찾을 수 없습니다.")
            return None
        except Exception as e:
            print(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
            return None

    def get_recommendations(self, user: UserInfo, num_combinations: int = 5) -> List[Tuple[List[Dict], Dict]]:
        """
        사용자 정보에 기반하여 백트래킹 알고리즘으로 음식 조합을 추천합니다.
        """
        # 목표치 설정 (조건 완화)
        # 백트래킹은 정확한 해를 찾기 어려울 수 있으므로 범위를 넓게 잡습니다.
        targets = {
            'energy': user.calories_required / 3 + 200,
            'protein': user.protein_required / 3 * 0.8,
            'fat': user.fat_required / 3 * 0.8,
            'carbs': user.carbon_required / 3 * 0.8
        }

        preference = user.preference[0].label if user.preference else None

        # 데이터 셔플링 (다양성 확보를 위해 먼저 섞음)
        random.shuffle(self.food_list)

        if preference:
            print(f"\n[Backtracking] 사용자 선호 음식(1순위): '{preference}'")
            # 선호 음식을 앞으로 보냄 (Stable sort이므로 섞인 순서 유지됨)
            self.food_list.sort(key=lambda x: x['분류'] == preference, reverse=True)
        else:
            print("\n[Backtracking] 사용자 선호 음식이 설정되지 않았습니다.")

        print("\n[한 끼 식사 목표 영양소 (최소 기준)]")
        print(
            f"에너지 <= {targets['energy']:.2f}kcal, 단백질 >= {targets['protein']:.2f}g, 지방 >= {targets['fat']:.2f}g, 탄수화물 >= {targets['carbs']:.2f}g")

        return self._find_combinations_backtracking(targets, num_combinations)

    def _find_combinations_backtracking(self, targets: Dict, num_combinations: int) -> List[Tuple[List[Dict], Dict]]:
        """
        백트래킹 알고리즘을 사용하여 조건에 맞는 조합을 찾습니다.
        """
        print(f"\n--- Backtracking 알고리즘 ({num_combinations}개 조합 탐색) ---")
        start_time = time.time()

        found_combinations = []
        found_signatures = set()

        self.steps = 0
        MAX_STEPS = 5000000  # 탐색 횟수 대폭 증가
        MAX_MENU_ITEMS = 6   # 메뉴 개수 제한 완화 (5 -> 8)

        # 탐색 공간 설정 (너무 많으면 느리므로 상위 N개만 사용)
        search_space_size = 2000
        search_space = self.food_list[:search_space_size] if len(self.food_list) > search_space_size else self.food_list
        print(f"탐색 공간 크기: {len(search_space)}개 (최대 스텝: {MAX_STEPS})")

        def backtrack(start_idx, current_menu, current_nutrition):
            if len(found_combinations) >= num_combinations:
                return
            if self.steps > MAX_STEPS:
                return

            self.steps += 1

            # 가지치기: 에너지가 목표를 초과하면 중단
            if current_nutrition['energy'] > targets['energy']:
                return

            # 가지치기: 메뉴 개수 초과 시 중단
            if len(current_menu) > MAX_MENU_ITEMS:
                return

            # 조건 만족 확인
            if (current_nutrition['protein'] >= targets['protein'] and
                    current_nutrition['fat'] >= targets['fat'] and
                    current_nutrition['carbs'] >= targets['carbs']):

                # 중복 조합 방지 (식품명 정렬하여 시그니처 생성)
                signature = tuple(sorted([f['식품명'] for f in current_menu]))
                if signature not in found_signatures:
                    found_signatures.add(signature)
                    found_combinations.append((list(current_menu), current_nutrition.copy()))
                    return

            # 다음 음식 탐색
            for i in range(start_idx, len(search_space)):
                if self.steps > MAX_STEPS: break
                if len(found_combinations) >= num_combinations: break

                food = search_space[i]

                # 미래 예측 가지치기: 현재 칼로리에 이 음식을 더했을 때 이미 초과라면 스킵
                if current_nutrition['energy'] + food['에너지(kcal)'] > targets['energy']:
                    continue

                new_nutrition = current_nutrition.copy()
                new_nutrition['energy'] += food['에너지(kcal)']
                new_nutrition['protein'] += food['단백질(g)']
                new_nutrition['fat'] += food['지방(g)']
                new_nutrition['carbs'] += food['탄수화물(g)']

                backtrack(i + 1, current_menu + [food], new_nutrition)

        backtrack(0, [], {'energy': 0, 'protein': 0, 'fat': 0, 'carbs': 0})

        end_time = time.time()

        if not found_combinations:
            print("기준을 만족하는 조합을 찾지 못했습니다.")
            print("팁: 목표 영양소가 너무 높거나, 칼로리 제한이 너무 낮을 수 있습니다.")
        else:
            print(f"총 {len(found_combinations)}개의 조합을 발견했습니다.")

        print(f"백트래킹 알고리즘 총 실행 시간: {end_time - start_time:.4f}초 (탐색 횟수: {self.steps})")

        return found_combinations
