import argparse
from typing import List, Dict, Tuple

from models.user_info import UserInfo
from models.enums import Sex, DietPurpose, ActivityLevel, FoodCategory
from services.nutrition_requirement_service import NutritionRequirementService
from services.greedy import GreedyService
from services.genetic import GeneticService
from services.backtracking import BacktrackingService


def percent_error(actual: float, target: float) -> float:
    """절대 백분율 오차(%)"""
    return abs(actual - target) / target * 100


def evaluate_1000_combinations(
    results: List[Tuple[list, Dict[str, float]]],
    user: UserInfo,
    strict_tol: float = 10.0,
):
    """
    results: [(combo, totals), ...] length = 1000
    totals: {"energy","carbs","protein","fat"}

    return:
      kcal_avg_error(%),
      macro_avg_error(%),
      strict_success_rate(%)
    """

    # === 한 끼 목표값 (유저 기준) ===
    target_kcal = user.calories_required / 3 + 200
    target_carbs = user.carbon_required / 3
    target_protein = user.protein_required / 3
    target_fat = user.fat_required / 3

    kcal_errors = []
    macro_errors = []
    strict_success = 0

    for _, totals in results:
        kcal = totals["energy"]
        carbs = totals["carbs"]
        protein = totals["protein"]
        fat = totals["fat"]

        kcal_err = percent_error(kcal, target_kcal)
        carb_err = percent_error(carbs, target_carbs)
        protein_err = percent_error(protein, target_protein)
        fat_err = percent_error(fat, target_fat)

        kcal_errors.append(kcal_err)
        macro_errors.append((carb_err + protein_err + fat_err) / 3)

        if (
            kcal_err <= strict_tol
            and carb_err <= strict_tol
            and protein_err <= strict_tol
            and fat_err <= strict_tol
        ):
            strict_success += 1

    kcal_avg_error = sum(kcal_errors) / len(kcal_errors)
    macro_avg_error = sum(macro_errors) / len(macro_errors)
    strict_success_rate = strict_success / len(results) * 100

    return kcal_avg_error, macro_avg_error, strict_success_rate


# =========================
# 메인 실행
# =========================

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True, help="db/음식DB.xlsx")
    args = parser.parse_args()

    # =========================
    # 1. 사용자 설정 (실험 고정)
    # =========================
    user = UserInfo(
        height=184,
        weight=72,
        age=24,
        sex=Sex.MALE,
        purpose=DietPurpose.NORMAL,
        preference=[FoodCategory.RICE, FoodCategory.STEAMED, FoodCategory.GRILLED],
        activity_factor=ActivityLevel.MODERATE,
    )

    # 영양 요구량 계산
    nutrition_service = NutritionRequirementService()
    nutrition_service.calculate_requirements(user)

    print("=== 사용자 한 끼 목표 영양 ===")
    print(f"kcal: {user.calories_required/3 + 200:.2f}")
    print(f"carbs: {user.carbon_required/3:.2f}")
    print(f"protein: {user.protein_required/3:.2f}")
    print(f"fat: {user.fat_required/3:.2f}")

    # =========================
    # 2. 알고리즘 서비스 생성
    # =========================
    greedy = GreedyService(args.db)
    ga = GeneticService(args.db)
    bt = BacktrackingService(args.db)

    # =========================
    # 3. 1000개 조합 생성
    # =========================
    print("\n[Greedy] 1000개 조합 생성 중...")
    greedy_results = greedy.get_recommendations(user, num_combinations=1000)

    print("[GA] 1000개 조합 생성 중...")
    ga_results = ga.get_recommendations(
        user,
        num_combinations=1000,
        population_size=100,
        generations=50,
    )

    print("[Backtracking] 1000개 조합 생성 중...")
    bt_results = bt.get_recommendations(user, num_combinations=1000)

    # =========================
    # 4. 품질 평가
    # =========================
    print("\n=== 1000개 조합 품질 평가 결과 ===")

    for name, results in [
        ("Greedy", greedy_results),
        ("Genetic Algorithm", ga_results),
        ("Backtracking", bt_results),
    ]:
        kcal_err, macro_err, strict_rate = evaluate_1000_combinations(
            results,
            user,
            strict_tol=25.0,
        )

        print(f"\n[{name}]")
        print(f"kcal 평균 오차: {kcal_err:.2f}%")
        print(f"탄/단/지 평균 오차: {macro_err:.2f}%")
        print(f"제약(±25%) 만족 성공률: {strict_rate:.2f}%")


if __name__ == "__main__":
    main()
