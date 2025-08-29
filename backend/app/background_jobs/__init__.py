"""
Background Job System Initialization
Following YAGNI principles - Simple ThreadPoolExecutor implementation
"""

from app.background_jobs.core import job_manager
from app.background_jobs.handlers.csv_orders import CSVOrderProcessingJobHandler

def initialize_job_system():
    """
    Initialize job system and register all handlers
    Following SOLID: Single Responsibility for initialization
    """
    
    # Register job handlers
    job_manager.register_handler("csv_order_processing", CSVOrderProcessingJobHandler)
    
    # Register other handlers as needed (YAGNI - only when required)
    # job_manager.register_handler("report_generation", ReportGenerationJobHandler)
    # job_manager.register_handler("email_sending", EmailSendingJobHandler)
    
    return job_manager

# Initialize on import
initialize_job_system()