import logging
import time
from threading import Thread, Lock
from collections import deque

# Configure logging for the task manager
# Using a distinct logger name can be helpful if you want to configure its output separately
task_logger = logging.getLogger('TaskManager')
task_logger.setLevel(logging.INFO)
# Ensure logs from this module also go to the main app.log file
# If not already configured by basicConfig in agent.py or main.py, you might need to add a handler.
# For simplicity, assuming basicConfig in agent.py or main.py covers this.

class Task:
    def __init__(self, id, description, target_func, *args, **kwargs):
        self.id = id
        self.description = description
        self.target_func = target_func
        self.args = args
        self.kwargs = kwargs
        self.status = "pending" # pending, running, completed, failed
        self.result = None
        self.error = None

    def run(self):
        self.status = "running"
        task_logger.info(f"Task {self.id} ('{self.description}') started.")
        try:
            self.result = self.target_func(*self.args, **self.kwargs)
            self.status = "completed"
            task_logger.info(f"Task {self.id} ('{self.description}') completed successfully. Result: {self.result}")
        except Exception as e:
            self.status = "failed"
            self.error = str(e)
            task_logger.error(f"Task {self.id} ('{self.description}') failed: {e}")
        return self.status

class TaskManager:
    def __init__(self, max_concurrent_tasks=3):
        self.task_queue = deque()
        self.task_history = {} # Store completed/failed tasks by ID
        self.current_tasks = {} # Tasks currently running
        self.next_task_id = 0
        self.lock = Lock()
        self.max_concurrent_tasks = max_concurrent_tasks
        self.worker_threads = []

        # Start a few worker threads to process the queue
        # For a GUI app, these threads should be managed carefully (e.g., daemon threads)
        # or integrated with Qt's threading if they need to update GUI directly (which they shouldn't here)
        for i in range(self.max_concurrent_tasks):
            thread = Thread(target=self._worker, daemon=True, name=f"TaskWorker-{i}")
            thread.start()
            self.worker_threads.append(thread)
        task_logger.info(f"TaskManager initialized with {max_concurrent_tasks} worker threads.")

    def _get_next_task_id(self):
        with self.lock:
            self.next_task_id += 1
            return self.next_task_id

    def add_task(self, description: str, target_func, *args, **kwargs) -> int:
        """
        Adds a new task to the queue.
        Returns the task ID.
        """
        task_id = self._get_next_task_id()
        task = Task(task_id, description, target_func, *args, **kwargs)
        with self.lock:
            self.task_queue.append(task)
            self.task_history[task_id] = task # Keep track immediately
        task_logger.info(f"Task {task_id} ('{description}') added to queue.")
        return task_id

    def _worker(self):
        """Worker thread method to process tasks from the queue."""
        while True: # Keep running to pick up new tasks
            task_to_process = None
            with self.lock:
                if self.task_queue:
                    task_to_process = self.task_queue.popleft()
                    self.current_tasks[task_to_process.id] = task_to_process

            if task_to_process:
                task_to_process.run() # This executes the task's target_func
                with self.lock:
                    del self.current_tasks[task_to_process.id]
                    # Task status is updated within task.run(), history already has the task object
            else:
                # No tasks, wait a bit before checking again to avoid busy-waiting
                time.sleep(0.1)

    def get_task_status(self, task_id: int) -> dict:
        """
        Gets the status and result/error of a task.
        """
        with self.lock:
            task = self.task_history.get(task_id)
            if task:
                return {
                    "id": task.id,
                    "description": task.description,
                    "status": task.status,
                    "result": task.result,
                    "error": task.error,
                }
            return None # Task not found

    def get_all_tasks_status(self) -> list[dict]:
        """Returns status for all known tasks (queued, running, historical)."""
        statuses = []
        with self.lock:
            # Combine queued, current, and historical tasks for a full overview
            # This is a simplified view; more complex logic might be needed for specific needs

            # Queued tasks
            for task in self.task_queue:
                 statuses.append({
                    "id": task.id, "description": task.description, "status": "queued",
                    "result": None, "error": None
                })
            # Running tasks
            for task_id, task in self.current_tasks.items():
                 statuses.append({
                    "id": task.id, "description": task.description, "status": task.status,
                    "result": task.result, "error": task.error # Result/error might be None while running
                })
            # Completed/Failed tasks (ensure no duplicates if also in current_tasks briefly)
            # A more robust way is to ensure task_history is the single source of truth for final states.
            # For simplicity, this might list a task as running and then its final state if queried at the exact moment of completion.
            # A better approach: iterate task_history and update with current_tasks' status if running.

            # Let's refine this to show the most current status from task_history
            # and supplement with any tasks still only in the queue.

            # This part becomes a bit more complex if we want a perfect snapshot.
            # For now, let's rely on task_history and what's currently in self.task_queue.
            # The self.current_tasks are mainly for internal tracking by workers.

            # Simplification: just iterate task_history for now, as it gets updated.
            # This won't show tasks that are only in task_queue and not yet in task_history with a status.
            # Correct approach:
            all_tasks_snapshot = list(self.task_history.values())

        return [
            {"id": t.id, "description": t.description, "status": t.status, "result": t.result, "error": t.error}
            for t in all_tasks_snapshot
        ]


# Example usage (conceptual, typically TaskManager would be part of a larger system like WillowAgent)
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    task_logger.info("Starting TaskManager example.")

    task_manager = TaskManager(max_concurrent_tasks=2)

    # Define some dummy functions for tasks
    def sample_task_long(duration, task_name):
        task_logger.info(f"'{task_name}' starting, will run for {duration}s.")
        time.sleep(duration)
        return f"'{task_name}' completed after {duration}s."

    def sample_task_short(task_name):
        task_logger.info(f"'{task_name}' starting.")
        time.sleep(0.5)
        return f"'{task_name}' completed quickly."

    def sample_task_fail(task_name):
        task_logger.info(f"'{task_name}' starting, will fail.")
        time.sleep(0.2)
        raise ValueError(f"'{task_name}' failed intentionally.")

    # Add tasks
    task_id1 = task_manager.add_task("Long Task A", sample_task_long, 3, "Task A (Long)")
    task_id2 = task_manager.add_task("Short Task B", sample_task_short, "Task B (Short)")
    task_id3 = task_manager.add_task("Failing Task C", sample_task_fail, "Task C (Fail)")
    task_id4 = task_manager.add_task("Long Task D", sample_task_long, 2, "Task D (Long)")

    task_logger.info(f"Tasks added: {task_id1}, {task_id2}, {task_id3}, {task_id4}")

    # Let tasks run for a bit
    time.sleep(1)
    task_logger.info("\nChecking status after 1s:")
    for tid in [task_id1, task_id2, task_id3, task_id4]:
        status = task_manager.get_task_status(tid)
        task_logger.info(f"Status of Task {tid}: {status}")

    task_logger.info(f"\nAll tasks snapshot: {task_manager.get_all_tasks_status()}")


    time.sleep(3) # Allow more tasks to complete
    task_logger.info("\nChecking status after 4s total:")
    for tid in [task_id1, task_id2, task_id3, task_id4]:
        status = task_manager.get_task_status(tid)
        task_logger.info(f"Status of Task {tid}: {status}")

    task_logger.info(f"\nAll tasks snapshot: {task_manager.get_all_tasks_status()}")

    # Note: Worker threads are daemons, so they'll exit when the main thread exits.
    # In a real app, you might want a more graceful shutdown.
    task_logger.info("Example finished.")
