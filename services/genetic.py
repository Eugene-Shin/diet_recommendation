import pandas as pd
import random
import time
from typing import List, Dict, Optional, Tuple

from models.user_info import UserInfo


class GeneticService:
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

    def get_recommendations(self, user: UserInfo, num_combinations: int = 5,
                          population_size: int = 100, generations: int = 50) -> List[Tuple[List[Dict], Dict]]:
        """
        사용자 정보에 기반하여 유전 알고리즘으로 음식 조합을 추천합니다.
        목표 조합 개수를 채울 때까지 알고리즘을 반복 실행합니다 (Restart Strategy).
        """
        # 목표 영양소를 3으로 나누어 한 끼 분량을 계산합니다.
        targets = {
            'energy': user.calories_required / 3 + 200,
            'protein': user.protein_required / 3,
            'fat': user.fat_required / 3,
            'carbs': user.carbon_required / 3 - 50
        }
        
        preference = user.preference[0].label if user.preference else None
        
        if preference:
            print(f"\n사용자 선호 음식(1순위): '{preference}'")
        else:
            print("\n사용자 선호 음식이 설정되지 않았습니다.")
            
        print("\n[한 끼 식사 목표 영양소]")
        print(f"에너지 <= {targets['energy']:.2f}kcal, 단백질 >= {targets['protein']:.2f}g, 지방 >= {targets['fat']:.2f}g, 탄수화물 >= {targets['carbs']:.2f}g")

        # --- 반복 실행 로직 시작 ---
        print(f"\n--- 유전 알고리즘 시작 (목표: {num_combinations}개 조합) ---")
        total_start_time = time.time()
        
        all_unique_combinations = []
        global_signatures = set()
        
        attempt = 0
        max_attempts = 20  # 무한 루프 방지용 최대 시도 횟수
        
        while len(all_unique_combinations) < num_combinations and attempt < max_attempts:
            attempt += 1
            needed = num_combinations - len(all_unique_combinations)

            # 한 번의 GA 실행
            # 인구수와 세대수는 실행 속도를 위해 조절 가능 (여기서는 입력값 유지)
            batch_results = self._run_single_ga_batch(targets, population_size, generations, preference)
            
            # 결과 통합 (중복 제거)
            new_count = 0
            for combo, totals, fitness in batch_results:
                signature = tuple(sorted([f['식품명'] for f in combo]))
                if signature not in global_signatures:
                    global_signatures.add(signature)
                    all_unique_combinations.append((combo, totals))
                    new_count += 1
                    
            # 만약 이번 실행에서 새로운 조합을 하나도 못 찾았다면, 다음 실행에서는 돌연변이율을 높이거나 다양성을 위한 조치가 필요할 수 있음

        total_end_time = time.time()
        print(f"\n=== 유전 알고리즘 최종 완료 ===")
        print(f"총 실행 시간: {total_end_time - total_start_time:.4f}초")
        print(f"최종 발견된 조합 수: {len(all_unique_combinations)}개")
        
        # 결과가 너무 많으면 적합도 순으로 정렬하거나 해야 하지만, 
        # 현재 구조상 적합도 정보는 저장하지 않고 있으므로 발견된 순서대로 반환하거나 
        # 필요하다면 다시 평가하여 정렬할 수 있습니다. 
        # 여기서는 발견된 순서대로 반환하되, 요청된 개수만큼 자릅니다.
        return all_unique_combinations[:num_combinations]

    def _run_single_ga_batch(self, targets: Dict, population_size: int, generations: int,
                               preference: Optional[str]) -> List[Tuple[List[Dict], Dict, float]]:
        """
        유전 알고리즘을 1회 실행하여 유효한 조합들을 반환합니다.
        """
        # 초기 개체군 생성
        population = self._initialize_population(population_size, targets)

        best_solutions_in_run = []
        local_signatures = set()

        for gen in range(generations):
            # 적합도 계산
            fitness_scores = [(individual, self._calculate_fitness(individual, targets, preference))
                            for individual in population]
            
            # 적합도 순 정렬
            fitness_scores.sort(key=lambda x: x[1], reverse=True)

            # 마지막 세대이거나, 중간중간 우수한 개체 수집
            # 여기서는 매 세대 상위 20%를 후보로 등록 (중복 제거하며)
            top_count = max(1, int(population_size * 0.2))
            for individual, fitness in fitness_scores[:top_count]:
                if fitness > 0: # 유효한 해만
                    signature = tuple(sorted([idx for idx in individual if idx != -1]))
                    if signature not in local_signatures and len(signature) > 0:
                        local_signatures.add(signature)
                        combination = [self.food_list[idx] for idx in individual if idx != -1]
                        totals = self._calculate_nutrition(combination)
                        best_solutions_in_run.append((combination, totals, fitness))

            # 다음 세대 생성
            population = self._evolve_population(fitness_scores, population_size, targets)

        return best_solutions_in_run

    def _initialize_population(self, population_size: int, targets: Dict) -> List[List[int]]:
        """
        초기 개체군을 생성합니다.
        각 개체는 식품 인덱스의 리스트로 표현됩니다.
        """
        population = []
        max_foods = 7  # 한 끼에 포함될 최대 음식 개수

        for _ in range(population_size):
            # 랜덤하게 3~7개의 음식 선택
            num_foods = random.randint(3, max_foods)
            individual = random.sample(range(len(self.food_list)), num_foods)

            # 고정 길이로 만들기 위해 -1로 패딩
            while len(individual) < max_foods:
                individual.append(-1)

            population.append(individual)

        return population

    def _calculate_fitness(self, individual: List[int], targets: Dict, preference: Optional[str]) -> float:
        """
        개체의 적합도를 계산합니다.
        높은 점수일수록 목표에 가까운 조합입니다.
        """
        # 실제 음식만 추출 (-1 제외)
        foods = [self.food_list[idx] for idx in individual if idx != -1]

        if len(foods) == 0:
            return 0.0

        # 현재 영양소 합계 계산
        totals = self._calculate_nutrition(foods)

        # 에너지 초과 시 큰 페널티
        if totals['energy'] > targets['energy']:
            energy_penalty = (totals['energy'] - targets['energy']) / targets['energy']
            return -1000 * energy_penalty

        # 목표 달성도 계산
        protein_score = min(totals['protein'] / targets['protein'], 1.0) if targets['protein'] > 0 else 1.0
        fat_score = min(totals['fat'] / targets['fat'], 1.0) if targets['fat'] > 0 else 1.0
        carbs_score = min(totals['carbs'] / targets['carbs'], 1.0) if targets['carbs'] > 0 else 1.0

        # 에너지 활용도 (목표에 가까울수록 좋음)
        energy_utilization = totals['energy'] / targets['energy'] if targets['energy'] > 0 else 0

        # 기본 점수 (영양소 달성도의 평균)
        base_score = (protein_score + fat_score + carbs_score) * 10

        # 에너지 활용도 보너스
        energy_bonus = energy_utilization * 2

        # 선호 음식 보너스
        preference_bonus = 0
        if preference:
            preference_count = sum(1 for food in foods if food.get('분류') == preference)
            preference_bonus = preference_count * 1.5

        # 음식 개수 페널티 (너무 많거나 적으면 감점)
        food_count_penalty = abs(len(foods) - 5) * 0.5

        total_score = base_score + energy_bonus + preference_bonus - food_count_penalty

        return max(total_score, 0.0)

    def _calculate_nutrition(self, foods: List[Dict]) -> Dict:
        """음식 리스트의 총 영양소를 계산합니다."""
        return {
            'energy': sum(f['에너지(kcal)'] for f in foods),
            'protein': sum(f['단백질(g)'] for f in foods),
            'fat': sum(f['지방(g)'] for f in foods),
            'carbs': sum(f['탄수화물(g)'] for f in foods)
        }

    def _evolve_population(self, fitness_scores: List[Tuple[List[int], float]],
                          population_size: int, targets: Dict) -> List[List[int]]:
        """
        선택, 교차, 돌연변이를 통해 다음 세대를 생성합니다.
        """
        # 엘리트 선택 (상위 10% 보존)
        elite_count = max(2, population_size // 10)
        new_population = [individual for individual, _ in fitness_scores[:elite_count]]

        # 토너먼트 선택을 통한 부모 선택 및 교차
        while len(new_population) < population_size:
            parent1 = self._tournament_selection(fitness_scores)
            parent2 = self._tournament_selection(fitness_scores)

            # 교차
            child1, child2 = self._crossover(parent1, parent2)

            # 돌연변이
            child1 = self._mutate(child1, targets)
            child2 = self._mutate(child2, targets)

            new_population.append(child1)
            if len(new_population) < population_size:
                new_population.append(child2)

        return new_population[:population_size]

    def _tournament_selection(self, fitness_scores: List[Tuple[List[int], float]],
                              tournament_size: int = 5) -> List[int]:
        """토너먼트 선택으로 부모를 선택합니다."""
        tournament = random.sample(fitness_scores, min(tournament_size, len(fitness_scores)))
        winner = max(tournament, key=lambda x: x[1])
        return winner[0].copy()

    def _crossover(self, parent1: List[int], parent2: List[int]) -> Tuple[List[int], List[int]]:
        """
        단일 점 교차를 수행합니다.
        """
        if random.random() > 0.7:  # 70% 확률로 교차
            return parent1.copy(), parent2.copy()

        # 교차점 선택
        crossover_point = random.randint(1, len(parent1) - 1)

        child1 = parent1[:crossover_point] + parent2[crossover_point:]
        child2 = parent2[:crossover_point] + parent1[crossover_point:]

        # 중복 제거
        child1 = self._remove_duplicates(child1)
        child2 = self._remove_duplicates(child2)

        return child1, child2

    def _remove_duplicates(self, individual: List[int]) -> List[int]:
        """개체에서 중복된 음식 인덱스를 제거합니다."""
        seen = set()
        result = []
        for idx in individual:
            if idx == -1 or idx not in seen:
                result.append(idx)
                if idx != -1:
                    seen.add(idx)

        # 길이 맞추기
        while len(result) < len(individual):
            result.append(-1)

        return result[:len(individual)]

    def _mutate(self, individual: List[int], targets: Dict, mutation_rate: float = 0.3) -> List[int]:
        """
        돌연변이를 수행합니다.
        """
        individual = individual.copy()

        if random.random() < mutation_rate:
            mutation_type = random.choice(['add', 'remove', 'replace'])

            if mutation_type == 'add':
                # 새로운 음식 추가
                for i in range(len(individual)):
                    if individual[i] == -1:
                        new_food = random.randint(0, len(self.food_list) - 1)
                        if new_food not in individual:
                            individual[i] = new_food
                        break

            elif mutation_type == 'remove':
                # 음식 제거
                valid_indices = [i for i, idx in enumerate(individual) if idx != -1]
                if valid_indices:
                    remove_idx = random.choice(valid_indices)
                    individual[remove_idx] = -1

            elif mutation_type == 'replace':
                # 음식 교체
                valid_indices = [i for i, idx in enumerate(individual) if idx != -1]
                if valid_indices:
                    replace_idx = random.choice(valid_indices)
                    new_food = random.randint(0, len(self.food_list) - 1)
                    if new_food not in individual:
                        individual[replace_idx] = new_food

        return individual
