from controllers.get_user_info import get_user_info
from controllers.display_user_info import display_user_info
from controllers.display_daily_requirements import display_daily_requirements
from services.nutrition_requirement_service import NutritionRequirementService

def main() -> None:
    print("=========== 식단 추천 프로그램 (외식용) ===========")
    user = get_user_info()
    display_user_info(user)
    
    service = NutritionRequirementService()
    service.calculate_requirements(user)
    display_daily_requirements(user)
    
    print("\n============ 데이터를 불러오는 중... ============")
    
    # db_1, db_2, db_3, db_rest = pass
    
    print("\n=============== 식단 구성 중... ===============")
    
    # 각 알고리즘 적용해 식단 구성
    
    print("프로그램을 종료합니다.")

if __name__ == "__main__":
    main()