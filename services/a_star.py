import pandas as pd
import random
import time
import sys
from typing import List, Dict, Optional, Tuple

sys.setrecursionlimit(2000)

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
        targets = {
            'energy': user.calories_required / 3 + 300,
            'protein': user.protein_required / 3,
            'fat': user.fat_required / 3,
            'carbs': user.carbon_required / 3 - 50
        }
        
        preference = user.preference[0].label if user.preference else None
        
        if preference:
            print(f"\n[Backtracking] 사용자 선호 음식(1순위): '{preference}'")
            self.food_list.sort(key=lambda x: x['분류'] == preference, reverse=True)
        else:
            print("\n[Backtracking] 사용자 선호 음식이 설정되지 않았습니다.")
            random.shuffle(self.food_list) 
            
        print("\n[한 끼 식사 목표 영양소]")
        print(f"에너지 <= {targets['energy']:.2f}kcal, 단백질 >= {targets['protein']:.2f}g, 지방 >= {targets['fat']:.2f}g, 탄수화물 >= {targets['carbs']:.2f}g")

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
        MAX_STEPS = 1000000 
        
        MAX_MENU_ITEMS = 5 

        def backtrack(start_idx, current_menu, current_nutrition):
            if len(found_combinations) >= num_combinations:
                return
            if self.steps > MAX_STEPS:
                return

            self.steps += 1

            if current_nutrition['energy'] > targets['energy']:
                return
            
            if len(current_menu) > MAX_MENU_ITEMS:
                return

            if (current_nutrition['protein'] >= targets['protein'] and
                current_nutrition['fat'] >= targets['fat'] and
                current_nutrition['carbs'] >= targets['carbs']):
                
                signature = tuple(sorted([f['식품명'] for f in current_menu]))
                if signature not in found_signatures:
                    found_signatures.add(signature)
                    found_combinations.append((list(current_menu), current_nutrition.copy()))
                    return 

            for i in range(start_idx, len(self.food_list)):
                if self.steps > MAX_STEPS: break
                
                food = self.food_list[i]
                
                new_nutrition = current_nutrition.copy()
                new_nutrition['energy'] += food['에너지(kcal)']
                new_nutrition['protein'] += food['단백질(g)']
                new_nutrition['fat'] += food['지방(g)']
                new_nutrition['carbs'] += food['탄수화물(g)']
                
                backtrack(i + 1, current_menu + [food], new_nutrition)
                
                if len(found_combinations) >= num_combinations:
                    return

        search_space = self.food_list[:1000] if len(self.food_list) > 1000 else self.food_list
        
        backtrack(0, [], {'energy': 0, 'protein': 0, 'fat': 0, 'carbs': 0})

        end_time = time.time()
        
        if not found_combinations:
            print("기준을 만족하는 조합을 찾지 못했습니다.")
        else:
            print(f"총 {len(found_combinations)}개의 조합을 발견했습니다.")
            
        print(f"백트래킹 알고리즘 총 실행 시간: {end_time - start_time:.4f}초 (탐색 횟수: {self.steps})")

        return found_combinations