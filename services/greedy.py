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
            'energy': user.calories_required / 3 + 200,
            'protein': user.protein_required / 3,
            'fat': user.fat_required / 3,
            'carbs': user.carbon_required / 3 - 50
        }
        
        # 사용자 정보에서 1순위 선호도를 가져옵니다.
        preference = user.preference[0].label if user.preference else None
        
        if preference:
            print(f"\n사용자 선호 음식(1순위): '{preference}' (선호도 점수 1.5배 적용)")
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

        # 선호 음식 리스트 미리 필터링 (초기 선택용)
        preferred_foods_indices = []
        if preference:
            preferred_foods_indices = [i for i, f in enumerate(self.food_list) if f.get('분류') == preference]

        # 충분한 시도를 위해 반복 횟수 설정 (목표 개수의 10배 시도)
        max_attempts = num_combinations * 10
        
        for attempt in range(max_attempts):
            if len(found_combinations) >= num_combinations:
                break

            # 초기 음식 선택 전략 (Seeding)
            initial_food_index = None
            
            # 70% 확률로 선호 음식 중 하나를 먼저 선택 (선호도가 있다면)
            if preferred_foods_indices and random.random() < 0.7:
                initial_food_index = random.choice(preferred_foods_indices)
            # 30% 확률 (또는 선호도가 없을 때) 전체 중 랜덤 선택 (다양성 확보)
            else:
                initial_food_index = random.randint(0, len(self.food_list) - 1)

            combination, totals = self._find_one_combination_greedy(targets, preference, initial_food_index)

            if combination:
                signature = tuple(sorted([f['식품명'] for f in combination]))
                if signature not in found_signatures:
                    found_signatures.add(signature)
                    found_combinations.append((combination, totals))

        if not found_combinations:
            print("기준을 만족하는 조합을 찾지 못했습니다.")
        else:
            print(f"총 {len(found_combinations)}개의 고유한 조합을 찾았습니다.")

        end_time = time.time()
        print(f"탐욕 알고리즘 총 실행 시간: {end_time - start_time:.4f}초")

        return found_combinations

    def _find_one_combination_greedy(self, targets: Dict, preference: Optional[str], initial_food_index: int, preference_bonus: float = 1.5) -> Tuple[Optional[List[Dict]], Optional[Dict]]:
        """
        탐욕 알고리즘으로 하나의 음식 조합을 찾습니다.
        initial_food_index: 처음에 강제로 포함할 음식의 인덱스
        """
        current_nutrition = {'energy': 0, 'protein': 0, 'fat': 0, 'carbs': 0}
        selected_foods = []
        available_indices = set(range(len(self.food_list)))

        # 1. 초기 음식 추가
        first_food = self.food_list[initial_food_index]
        
        # 초기 음식이 목표 칼로리를 넘으면 실패 처리
        if first_food['에너지(kcal)'] > targets['energy']:
            return None, None
            
        selected_foods.append(first_food)
        current_nutrition['energy'] += first_food['에너지(kcal)']
        current_nutrition['protein'] += first_food['단백질(g)']
        current_nutrition['fat'] += first_food['지방(g)']
        current_nutrition['carbs'] += first_food['탄수화물(g)']
        available_indices.remove(initial_food_index)

        # 2. 나머지 음식 채우기
        while (current_nutrition['protein'] < targets['protein'] or
               current_nutrition['fat'] < targets['fat'] or
               current_nutrition['carbs'] < targets['carbs']):

            candidates = []
            for i in available_indices:
                food = self.food_list[i]
                # 칼로리 초과 시 후보에서 제외
                if current_nutrition['energy'] + food['에너지(kcal)'] > targets['energy']:
                    continue

                # 점수 계산: 부족한 영양소를 채우는 데 얼마나 기여하는가?
                score = 0
                if current_nutrition['protein'] < targets['protein']:
                    score += food['단백질(g)'] / targets['protein']
                if current_nutrition['fat'] < targets['fat']:
                    score += food['지방(g)'] / targets['fat']
                if current_nutrition['carbs'] < targets['carbs']:
                    score += food['탄수화물(g)'] / targets['carbs']

                # 선호도 보너스 적용
                if preference and food.get('분류') == preference:
                    score *= preference_bonus

                if score > 0:
                    candidates.append((score, i))

            if not candidates:
                # 더 이상 추가할 수 있는 음식이 없으면 종료
                return None, None

            # 점수가 높은 상위 10개 후보 중 하나를 무작위로 선택 (다양성 확보를 위해 후보군 확대)
            candidates.sort(key=lambda x: x[0], reverse=True)
            top_candidates = candidates[:10]
            
            # 가중치 랜덤 선택 (점수가 높을수록 뽑힐 확률 높음)
            scores = [c[0] for c in top_candidates]
            indices = [c[1] for c in top_candidates]
            best_food_index = random.choices(indices, weights=scores, k=1)[0]

            best_food = self.food_list[best_food_index]
            selected_foods.append(best_food)

            # 영양 정보 업데이트
            current_nutrition['energy'] += best_food['에너지(kcal)']
            current_nutrition['protein'] += best_food['단백질(g)']
            current_nutrition['fat'] += best_food['지방(g)']
            current_nutrition['carbs'] += best_food['탄수화물(g)']

            available_indices.remove(best_food_index)

        # 최종적으로 목표 영양소를 만족하는지 확인
        if (current_nutrition['protein'] >= targets['protein'] and
                current_nutrition['fat'] >= targets['fat'] and
                current_nutrition['carbs'] >= targets['carbs']):
            return selected_foods, current_nutrition
        else:
            return None, None
