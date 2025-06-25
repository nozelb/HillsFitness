# Add these imports at the top of your main.py
from dashboard import DashboardService, TodaysWorkoutService, ProgressService, AnalyticsService

# Initialize services after creating the database
db = RealDatabase()
dashboard_service = DashboardService(db)
workout_service = TodaysWorkoutService(db)
progress_service = ProgressService(db)
analytics_service = AnalyticsService(db)

# Replace the dashboard endpoints with these cleaner versions:

@app.get("/api/dashboard")
async def get_dashboard(current_user: dict = Depends(get_current_user)):
    """Get real dashboard data (no mock data)"""
    try:
        dashboard_data = dashboard_service.get_dashboard_data(current_user["id"])
        return dashboard_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/todays-workout")
async def get_todays_workout(current_user: dict = Depends(get_current_user)):
    """Get today's workout based on user's active plan and progress"""
    try:
        workout_data = workout_service.get_todays_workout(current_user["id"])
        return workout_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/progress")
async def log_progress(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Log daily progress entry"""
    try:
        raw_body = await request.body()
        progress_data = json.loads(raw_body.decode())
        result = progress_service.log_progress(current_user["id"], progress_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/workout-log")
async def log_workout(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Log completed workout"""
    try:
        raw_body = await request.body()
        workout_data = json.loads(raw_body.decode())
        result = progress_service.log_workout(current_user["id"], workout_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/weight")
async def log_weight(
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Log weight entry"""
    try:
        raw_body = await request.body()
        weight_data = json.loads(raw_body.decode())
        result = progress_service.log_weight(current_user["id"], weight_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/insights")
async def get_user_insights(current_user: dict = Depends(get_current_user)):
    """Get AI-powered insights for the user"""
    try:
        insights = analytics_service.get_user_insights(current_user["id"])
        return insights
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))