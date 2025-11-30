import pandas as pd
import random
import time
from typing import List, Dict, Optional, Tuple

from models.user_info import UserInfo


class GreedyService:
    def __init__(self, db_path: str):
        self.df = self._load_nutrition_data(db_path)
        if self.df is None:
            raise FileNotFoundError(f"'{db_path}'에서 데이터를 불러오는 데 실패했습니다.")
        self.food_list = self.df.to_dict('records')
        print(f"전체 {len(self.food_list)}개 식품 데이터를 사용합니다.")

    def _load_nutrition_data(self, file_path: str) -> Optional[pd.DataFrame]:
        """Excel 파일에서 영양 데이터를 불러옵니다."""
        try:
            df = pd.read_excel(file_path)
            required_cols = ['식품명', '분류', '에너지(kcal)', '단백질(g)', '지방(g)', '탄수화물(g)']
            df = df[required_cols]
            for col in required_cols[2:]:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # FutureWarning 수정을 위해 inplace=True 대신 재할당 방식 사용
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
        사용자 정보에 기반하여 탐욕 알고리즘으로 음식 조합을 추천합니다.
        """
        # 목표 영양소를 3으로 나누어 한 끼 분량을 계산합니다.
        targets = {
            'energy': user.calories_required / 3 + 300,
            'protein': user.protein_required / 3,
            'fat': user.fat_required / 3,
            'carbs': user.carbon_required / 3 - 50
        }
        
        # 사용자 정보에서 1순위 선호도를 가져옵니다.
        preference = user.preference[0].label if user.preference else None
        
        if preference:
            print(f"\n사용자 선호 음식(1순위): '{preference}'")
        else:
            print("\n사용자 선호 음식이 설정되지 않았습니다.")
            
        print("\n[한 끼 식사 목표 영양소]")
        print(f"에너지 <= {targets['energy']:.2f}kcal, 단백질 >= {targets['protein']:.2f}g, 지방 >= {targets['fat']:.2f}g, 탄수화물 >= {targets['carbs']:.2f}g")

        return self._find_multiple_greedy_combinations(targets, num_combinations, preference)

    def _find_multiple_greedy_combinations(self, targets: Dict, num_combinations: int, preference: Optional[str]) -> List[Tuple[List[Dict], Dict]]:
        """
        Randomized Greedy 알고리즘을 여러 번 실행하여 다양한 조합을 찾습니다.
        """
        print(f"\n--- Randomized Greedy 알고리즘 ({num_combinations}개 조합 탐색) ---")
        start_time = time.time()

        found_combinations = []
        found_signatures = set()

        for _ in range(num_combinations * 3):  # 충분한 시도를 위해 목표 개수의 3배만큼 반복
            if len(found_combinations) >= num_combinations:
                break

            combination, totals = self._find_one_combination_greedy(targets, preference)

            if combination:
                signature = tuple(sorted([f['식품명'] for f in combination]))
                if signature not in found_signatures:
                    found_signatures.add(signature)
                    found_combinations.append((combination, totals))

        if not found_combinations:
            print("기준을 만족하는 조합을 찾지 못했습니다.")

        end_time = time.time()
        print(f"탐욕 알고리즘 총 실행 시간: {end_time - start_time:.4f}초")

        return found_combinations

    def _find_one_combination_greedy(self, targets: Dict, preference: Optional[str], preference_bonus: float = 1.5) -> Tuple[Optional[List[Dict]], Optional[Dict]]:
        """
        탐욕 알고리즘으로 하나의 음식 조합을 찾습니다. (Randomized 버전)
        """
        current_nutrition = {'energy': 0, 'protein': 0, 'fat': 0, 'carbs': 0}
        selected_foods = []
        available_indices = set(range(len(self.food_list)))

        while (current_nutrition['protein'] < targets['protein'] or
               current_nutrition['fat'] < targets['fat'] or
               current_nutrition['carbs'] < targets['carbs']):

            candidates = []
            for i in available_indices:
                food = self.food_list[i]
                if current_nutrition['energy'] + food['에너지(kcal)'] > targets['energy']:
                    continue

                score = 0
                if current_nutrition['protein'] < targets['protein']:
                    score += food['단백질(g)'] / targets['protein']
                if current_nutrition['fat'] < targets['fat']:
                    score += food['지방(g)'] / targets['fat']
                if current_nutrition['carbs'] < targets['carbs']:
                    score += food['탄수화물(g)'] / targets['carbs']

                if preference and food.get('분류') == preference:
                    score *= preference_bonus

                if score > 0:
                    candidates.append((score, i))

            if not candidates:
                return None, None

            candidates.sort(key=lambda x: x[0], reverse=True)
            top_candidates = candidates[:5]
            _, best_food_index = random.choice(top_candidates)

            best_food = self.food_list[best_food_index]
            selected_foods.append(best_food)

            current_nutrition['energy'] += best_food['에너지(kcal)']
            current_nutrition['protein'] += best_food['단백질(g)']
            current_nutrition['fat'] += best_food['지방(g)']
            current_nutrition['carbs'] += best_food['탄수화물(g)']

            available_indices.remove(best_food_index)

        if (current_nutrition['protein'] >= targets['protein'] and
                current_nutrition['fat'] >= targets['fat'] and
                current_nutrition['carbs'] >= targets['carbs']):
            return selected_foods, current_nutrition
        else:
            return None, None
