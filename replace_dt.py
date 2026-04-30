import os

files = [
    "backend/app/workers/metrics_collector.py",
    "backend/app/telemetry/collector.py",
    "backend/app/services/metrics_service.py",
    "backend/app/rl/trainer.py",
    "backend/app/optimizer/explainer.py",
    "backend/app/models/user.py",
    "backend/app/models/metrics_model.py",
    "backend/app/models/aws_connection.py",
    "backend/app/ml/forecasting_model.py",
    "backend/app/aws/mock_aws.py",
    "backend/app/aws/ec2_controller.py",
    "backend/app/aws/cost_explorer.py",
    "backend/app/audit/logger.py",
]

for f in files:
    full = os.path.join(r"c:\E\mini project sem 4\CostPilot-AI", f)
    if not os.path.exists(full):
        continue
    
    with open(full, 'r', encoding='utf-8') as file:
        content = file.read()
        
    if "datetime.utcnow" in content:
        if "timezone" not in content:
            # Handle cases where timedelta might be present
            content = content.replace("from datetime import datetime\n", "from datetime import datetime, timezone\n")
            content = content.replace("from datetime import datetime, timedelta\n", "from datetime import datetime, timedelta, timezone\n")
            
        content = content.replace("datetime.utcnow()", "datetime.now(timezone.utc)")
        content = content.replace("datetime.utcnow", "lambda: datetime.now(timezone.utc)")
        
        with open(full, 'w', encoding='utf-8') as file:
            file.write(content)
            print(f"Updated {f}")
