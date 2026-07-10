# ruff: noqa
# mypy: ignore-errors
# ruff: noqa
# mypy: ignore-errors
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from backend.db.pool import db_pool
from backend.security.auth import get_current_user

router = APIRouter(prefix="/runs", tags=["runs"], dependencies=[Depends(get_current_user)])

class RatingRequest(BaseModel):
    rating: int

@router.patch("/{run_id}/rating")
async def rate_run(run_id: str, payload: RatingRequest):
    if payload.rating < 1 or payload.rating > 5:
        raise HTTPException(status_code=400, detail="Rating must be between 1 and 5.")

    pool = db_pool.get_pool()
    if not pool:
        raise HTTPException(status_code=500, detail="Database pool offline.")

    async with pool.acquire() as conn:
        # Check if evaluation row exists
        eval_row = await conn.fetchrow("SELECT id, overall_score FROM evaluations WHERE run_id = $1", uuid.UUID(run_id))
        
        if not eval_row:
            # Create a mock evaluation row if not run yet to write rating
            eval_id = uuid.uuid4()
            await conn.execute(
                """
                INSERT INTO evaluations (id, run_id, user_rating)
                VALUES ($1, $2, $3)
                """,
                eval_id,
                uuid.UUID(run_id),
                payload.rating
            )
            return {"status": "user_rating_recorded"}
            
        # Update user_rating
        overall_score = float(eval_row["overall_score"]) if eval_row["overall_score"] is not None else 0.0
        norm_rating = payload.rating / 5.0
        calibration_needed = abs(overall_score - norm_rating) > 0.3

        await conn.execute(
            """
            UPDATE evaluations
            SET user_rating = $2, overall_score = COALESCE(overall_score, $3)
            WHERE run_id = $1
            """,
            uuid.UUID(run_id),
            payload.rating,
            overall_score
        )

        return {
            "status": "user_rating_recorded",
            "calibration_needed": calibration_needed
        }
