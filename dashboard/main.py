import os
import psycopg2
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

app = FastAPI(title="MarTech DataOps Portal")
templates = Jinja2Templates(directory="dashboard/templates")

def get_metrics():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "db"),
            user=os.getenv("DB_USER", "data_engineer"),
            password=os.getenv("DB_PASS", "devpassword"),
            dbname=os.getenv("DB_NAME", "analytics_dw"),
            port=5432
        )
        cur = conn.cursor()
        cur.execute("""
            SELECT 
                pipeline_name, 
                records_processed, 
                duration_ms, 
                status, 
                TO_CHAR(executed_at, 'YYYY-MM-DD HH24:MI:SS') as executed_at 
            FROM public.pipeline_metrics 
            ORDER BY executed_at DESC 
            LIMIT 10;
        """)
        metrics = cur.fetchall()
        cur.close()
        conn.close()
        return metrics
    except Exception as e:
        print(f"[!] Database connection error: {e}")
        return []

@app.get("/", response_class=HTMLResponse)
def index(request: Request):
    runs = get_metrics()
    return templates.TemplateResponse(
        request=request, 
        name="dashboard.html", 
        context={"runs": runs}
    )

@app.get("/api/health")
def health():
    return {"status": "healthy", "service": "data-platform-orchestrator"}