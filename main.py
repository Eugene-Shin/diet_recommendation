import os
from controllers.get_user_info import get_user_info
from controllers.display_user_info import display_user_info
from controllers.display_daily_requirements import display_daily_requirements
from services.nutrition_requirement_service import NutritionRequirementService
from services.genetic import GeneticService
from services.greedy import GreedyService

def display_recommendations(combinations):
    """추천된 음식 조합을 보기 쉽게 출력하는 함수"""
    if not combinations:
        print("\n추천된 식단이 없습니다.")
        return

    print(f"\n--- 총 {len(combinations)}개의 식단 조합을 찾았습니다. ---")
    for i, (combo, totals) in enumerate(combinations):
        print(f"\n--- 조합 {i+1} ---")
        total_calories = totals['energy']
        total_protein = totals['protein']
        total_carbs = totals['carbs']
        total_fat = totals['fat']

        for food in combo:
            print(f"- {food['식품명']} (에너지: {food['에너지(kcal)']}kcal, 단백질: {food['단백질(g)']}g)")

        print("\n[영양 정보 요약]")
        print(f"총 칼로리: {total_calories:.2f} kcal")
        print(f"총 단백질: {total_protein:.2f} g")
        print(f"총 탄수화물: {total_carbs:.2f} g")
        print(f"총 지방: {total_fat:.2f} g")
        print("-" * 20)


def main() -> None:
    print("=========== 식단 추천 프로그램 (외식용) ===========")
    user = get_user_info()
    display_user_info(user)

    # 영양 요구량 계산
    req_service = NutritionRequirementService()
    req_service.calculate_requirements(user)
    display_daily_requirements(user)

    # 알고리즘 선택
    print("\n============ 알고리즘 선택 ============")
    print("1. 그리디 알고리즘 (빠른 추천)")
    print("2. 유전 알고리즘 (최적화된 추천)")

    while True:
        try:
            choice = int(input("사용할 알고리즘을 선택하세요 (1 또는 2): "))
            if choice in [1, 2]:
                break
            else:
                print("1 또는 2를 입력해주세요.")
        except ValueError:
            print("숫자를 입력해주세요.")

    print("\n============ 데이터를 불러오는 중... ============")

    # 데이터 파일 경로 설정 (db 폴더 안에 파일이 있다고 가정)
    # 현재 파일의 위치를 기준으로 상대 경로를 사용해 db 폴더의 경로를 만듭니다.
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, 'db', '음식DB.xlsx')

    try:
        print("\n=============== 식단 구성 중... ===============")

        if choice == 1:
            # 그리디 알고리즘 사용
            greedy_service = GreedyService(db_path=db_path)
            combinations = greedy_service.get_recommendations(
                user,
                num_combinations=5
            )
        else:
            # 유전 알고리즘 사용
            genetic_service = GeneticService(db_path=db_path)
            # population_size: 세대당 개체 수, generations: 진화 세대 수
            combinations = genetic_service.get_recommendations(
                user,
                num_combinations=5,
                population_size=100,
                generations=50
            )

        # 결과 출력
        display_recommendations(combinations)

    except FileNotFoundError:
        print(f"\n[오류] 데이터 파일을 찾을 수 없습니다. '{db_path}' 경로를 확인해주세요.")
    except Exception as e:
        print(f"\n[오류] 프로그램 실행 중 문제가 발생했습니다: {e}")


    print("\n프로그램을 종료합니다.")

if __name__ == "__main__":
    main()
