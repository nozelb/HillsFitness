# backend/workers/vision_worker.py
"""
Vision Pipeline Worker Service
Runs vision analysis as a separate microservice for GPU optimization
"""

import cv2
import redis
import json
import logging
import os
import time
from typing import Dict, Any
from services.vision_pipeline import EnhancedVisionPipeline
from concurrent.futures import ThreadPoolExecutor
import asyncio
from dataclasses import asdict

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VisionWorker:
    """
    Background worker for processing vision analysis tasks
    Recommended to run on GPU-enabled instance for optimal performance
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url)
        self.vision_pipeline = EnhancedVisionPipeline()
        self.executor = ThreadPoolExecutor(max_workers=2)  # Adjust based on GPU memory
        
        # Queue names
        self.input_queue = "vision_input"
        self.output_queue = "vision_output"
        self.error_queue = "vision_errors"
        
        logger.info("Vision Worker initialized")
    
    def process_vision_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process a single vision analysis task"""
        try:
            task_id = task_data.get("task_id")
            user_id = task_data.get("user_id")
            image_path = task_data.get("image_path")
            user_height_cm = task_data.get("user_height_cm", 175.0)
            user_weight_kg = task_data.get("user_weight_kg", 70.0)
            user_sex = task_data.get("user_sex", "male")
            
            logger.info(f"Processing vision task {task_id} for user {user_id}")
            
            # Validate image exists
            if not os.path.exists(image_path):
                raise FileNotFoundError(f"Image not found: {image_path}")
            
            # Run vision pipeline
            start_time = time.time()
            result = self.vision_pipeline.process_image(
                image_path=image_path,
                user_height_cm=user_height_cm,
                user_weight_kg=user_weight_kg,
                user_sex=user_sex
            )
            
            processing_time = time.time() - start_time
            logger.info(f"Vision analysis completed in {processing_time:.2f}s")
            
            # Add metadata
            result.update({
                "task_id": task_id,
                "user_id": user_id,
                "processing_time_seconds": round(processing_time, 2),
                "worker_timestamp": time.time()
            })
            
            return result
            
        except Exception as e:
            logger.error(f"Vision processing failed: {str(e)}")
            return {
                "task_id": task_data.get("task_id"),
                "user_id": task_data.get("user_id"),
                "error": str(e),
                "error_type": type(e).__name__,
                "worker_timestamp": time.time()
            }
    
    async def run_worker(self):
        """Main worker loop - processes tasks from Redis queue"""
        logger.info("Starting vision worker...")
        
        while True:
            try:
                # Block for up to 1 second waiting for a task
                task_data = self.redis_client.brpop(self.input_queue, timeout=1)
                
                if task_data:
                    queue_name, task_json = task_data
                    task_dict = json.loads(task_json.decode('utf-8'))
                    
                    # Process task in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    result = await loop.run_in_executor(
                        self.executor,
                        self.process_vision_task,
                        task_dict
                    )
                    
                    # Publish result
                    if "error" in result:
                        self.redis_client.lpush(self.error_queue, json.dumps(result))
                        logger.error(f"Task {result.get('task_id')} failed: {result.get('error')}")
                    else:
                        self.redis_client.lpush(self.output_queue, json.dumps(result))
                        logger.info(f"Task {result.get('task_id')} completed successfully")
                        
                        # Also publish to specific user channel for real-time updates
                        user_channel = f"vision_done:{result.get('user_id')}"
                        self.redis_client.publish(user_channel, json.dumps(result))
                
                else:
                    # No tasks available, brief sleep
                    await asyncio.sleep(0.1)
                    
            except KeyboardInterrupt:
                logger.info("Worker interrupted by user")
                break
            except Exception as e:
                logger.error(f"Worker error: {str(e)}")
                await asyncio.sleep(1)  # Brief pause before retrying
        
        logger.info("Vision worker stopped")
    
    def queue_vision_task(self, task_data: Dict[str, Any]) -> str:
        """Queue a vision analysis task"""
        task_id = task_data.get("task_id", f"task_{int(time.time())}")
        task_data["task_id"] = task_id
        
        self.redis_client.lpush(self.input_queue, json.dumps(task_data))
        logger.info(f"Queued vision task {task_id}")
        
        return task_id
    
    def get_task_result(self, task_id: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Get result for a specific task (blocking)
        Used for synchronous API calls
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check completed tasks
            result_json = self.redis_client.rpop(self.output_queue)
            if result_json:
                result = json.loads(result_json.decode('utf-8'))
                if result.get("task_id") == task_id:
                    return result
                else:
                    # Put back if not our task
                    self.redis_client.lpush(self.output_queue, result_json)
            
            # Check error queue
            error_json = self.redis_client.rpop(self.error_queue)
            if error_json:
                error = json.loads(error_json.decode('utf-8'))
                if error.get("task_id") == task_id:
                    return error
                else:
                    # Put back if not our task
                    self.redis_client.lpush(self.error_queue, error_json)
            
            time.sleep(0.1)
        
        raise TimeoutError(f"Task {task_id} timed out after {timeout} seconds")
    
    def health_check(self) -> Dict[str, Any]:
        """Check worker health and queue status"""
        try:
            info = self.redis_client.info()
            queue_length = self.redis_client.llen(self.input_queue)
            completed_count = self.redis_client.llen(self.output_queue)
            error_count = self.redis_client.llen(self.error_queue)
            
            return {
                "status": "healthy",
                "redis_connected": True,
                "queue_length": queue_length,
                "completed_count": completed_count,
                "error_count": error_count,
                "redis_info": {
                    "connected_clients": info.get("connected_clients"),
                    "used_memory_human": info.get("used_memory_human")
                }
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "redis_connected": False
            }

# FastAPI integration for the main app
class VisionQueueClient:
    """
    Client for interacting with the vision worker from the main FastAPI app
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_client = redis.from_url(redis_url)
        self.input_queue = "vision_input"
        self.output_queue = "vision_output"
    
    async def queue_and_wait(self, image_path: str, user_id: str, 
                           user_height_cm: float, user_weight_kg: float, 
                           user_sex: str, timeout: int = 30) -> Dict[str, Any]:
        """
        Queue a vision task and wait for the result
        Used by the main API for synchronous responses
        """
        import uuid
        task_id = str(uuid.uuid4())
        
        task_data = {
            "task_id": task_id,
            "user_id": user_id,
            "image_path": image_path,
            "user_height_cm": user_height_cm,
            "user_weight_kg": user_weight_kg,
            "user_sex": user_sex
        }
        
        # Queue the task
        self.redis_client.lpush(self.input_queue, json.dumps(task_data))
        
        # Wait for result
        start_time = time.time()
        while time.time() - start_time < timeout:
            # Check for result on user-specific channel
            user_channel = f"vision_done:{user_id}"
            message = self.redis_client.get(user_channel)
            if message:
                result = json.loads(message.decode('utf-8'))
                if result.get("task_id") == task_id:
                    # Clean up
                    self.redis_client.delete(user_channel)
                    return result
            
            await asyncio.sleep(0.1)
        
        raise TimeoutError(f"Vision analysis timed out after {timeout} seconds")
    
    def queue_async(self, image_path: str, user_id: str, 
                   user_height_cm: float, user_weight_kg: float, 
                   user_sex: str) -> str:
        """
        Queue a vision task asynchronously
        Returns task_id for later polling
        """
        import uuid
        task_id = str(uuid.uuid4())
        
        task_data = {
            "task_id": task_id,
            "user_id": user_id,
            "image_path": image_path,
            "user_height_cm": user_height_cm,
            "user_weight_kg": user_weight_kg,
            "user_sex": user_sex
        }
        
        self.redis_client.lpush(self.input_queue, json.dumps(task_data))
        return task_id
    
    def get_result(self, task_id: str) -> Dict[str, Any]:
        """Get result for a specific task (non-blocking)"""
        # This would require a more sophisticated result storage system
        # For now, we'll use the synchronous approach
        pass

# Standalone worker script
async def main():
    """Main function to run the vision worker"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Vision Pipeline Worker")
    parser.add_argument("--redis-url", default="redis://localhost:6379", 
                       help="Redis connection URL")
    parser.add_argument("--workers", type=int, default=1, 
                       help="Number of worker processes")
    
    args = parser.parse_args()
    
    if args.workers > 1:
        # Multi-process setup
        import multiprocessing
        
        def run_worker():
            worker = VisionWorker(args.redis_url)
            asyncio.run(worker.run_worker())
        
        processes = []
        for i in range(args.workers):
            p = multiprocessing.Process(target=run_worker)
            p.start()
            processes.append(p)
            logger.info(f"Started worker process {i+1}")
        
        try:
            for p in processes:
                p.join()
        except KeyboardInterrupt:
            logger.info("Shutting down workers...")
            for p in processes:
                p.terminate()
                p.join()
    else:
        # Single worker
        worker = VisionWorker(args.redis_url)
        await worker.run_worker()

# Docker Compose integration
def create_docker_compose_vision_service():
    """
    Returns docker-compose service definition for the vision worker
    """
    return """
  vision-worker:
    build:
      context: .
      dockerfile: Dockerfile-vision-worker
    depends_on:
      - redis
    volumes:
      - uploads_data:/app/uploads
    environment:
      - REDIS_URL=redis://redis:6379
      - PYTHONPATH=/app
    restart: unless-stopped
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped
"""

# Health check endpoint for the worker
class HealthCheckServer:
    """Simple HTTP server for health checks"""
    
    def __init__(self, worker: VisionWorker, port: int = 8001):
        self.worker = worker
        self.port = port
    
    async def start_server(self):
        from aiohttp import web, web_runner
        
        app = web.Application()
        app.router.add_get('/health', self.health_handler)
        app.router.add_get('/metrics', self.metrics_handler)
        
        runner = web_runner.AppRunner(app)
        await runner.setup()
        
        site = web_runner.TCPSite(runner, '0.0.0.0', self.port)
        await site.start()
        
        logger.info(f"Health check server started on port {self.port}")
    
    async def health_handler(self, request):
        health = self.worker.health_check()
        status = 200 if health["status"] == "healthy" else 503
        return web.json_response(health, status=status)
    
    async def metrics_handler(self, request):
        health = self.worker.health_check()
        metrics = {
            "queue_length": health.get("queue_length", 0),
            "completed_count": health.get("completed_count", 0),
            "error_count": health.get("error_count", 0)
        }
        return web.json_response(metrics)

if __name__ == "__main__":
    asyncio.run(main())