from fastapi import APIRouter
from app.database.collections import schemes_collection
from app.services.recommendation_engine import recommend_schemes

router = APIRouter()

@router.post("/recommend")
def recommend(user: dict):

    schemes = list(schemes_collection.find({}, {"_id": 0}))
    
    results = recommend_schemes(user, schemes)

    return {
        "total": len(results),
        "schemes": results
    }