from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

import shutil
import os
from processing.logic import run_full_pipeline

app = FastAPI()

# Allow frontend connection (adjust origin if needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve output files (for direct download)
app.mount("/download", StaticFiles(directory="outputs"), name="outputs")

UPLOAD_DIR = "uploads"
OUTPUT_DIR = "outputs"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@app.post("/process/")
async def process_files(
    sales_file: UploadFile = File(...),
    inventory_file: UploadFile = File(...),
    #location_file: UploadFile = File(...)
):
    # Save uploaded files to disk
    sales_path = os.path.join(UPLOAD_DIR, sales_file.filename)
    inventory_path = os.path.join(UPLOAD_DIR, inventory_file.filename)
    #location_path = os.path.join(UPLOAD_DIR, location_file.filename)

    with open(sales_path, "wb") as f:
        shutil.copyfileobj(sales_file.file, f)
    with open(inventory_path, "wb") as f:
        shutil.copyfileobj(inventory_file.file, f)
    #with open(location_path, "wb") as f:
        #shutil.copyfileobj(location_file.file, f)

    # Run your main pipeline
    try:
        location_path = "D:/Walmart Sparkathon/predictsmart-ui/predictsmart-backend/uploads/mock_store_locations.csv"
        run_full_pipeline(
            sales_path=sales_path,
            inventory_path=inventory_path,
            location_path=location_path,
            output_dir=OUTPUT_DIR
        )
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

    # Return downloadable file URLs
    return {
        "forecast_csv": "/download/forecast_df.csv",
        "recommendation_csv": "/download/enhanced_sourcing_recommendations.csv",
        "pdf_report": "/download/sourcing_recommendation_report.pdf",
        "map_html": "/download/sourcing_map_with_legend.html"
    }

@app.get("/download/{filename}")
async def download_file(filename: str):
    filepath = os.path.join(OUTPUT_DIR, filename)
    if not os.path.exists(filepath):
        return JSONResponse(status_code=404, content={"error": "File not found"})
    return FileResponse(filepath, filename=filename)

@app.get("/store-locations")
def get_store_locations():
    path = os.path.join(UPLOAD_DIR, "mock_store_locations.csv")
    if not os.path.exists(path):
        return JSONResponse(status_code=404, content={"error": "Locations file not found"})
    return FileResponse(path, filename="mock_store_locations.csv")

@app.post("/store-locations/upload")
async def upload_store_locations(file: UploadFile = File(...)):
    path = os.path.join(UPLOAD_DIR, "mock_store_locations.csv")
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"message": "Store locations updated successfully."}
@app.get("/map-to-png")
def map_to_png():
    from html2image import Html2Image
    hti = Html2Image()
    map_path = "outputs/sourcing_map_with_legend.html"
    output_path = "outputs/sourcing_map_image.png"
    hti.screenshot(html_file=map_path, save_as=os.path.basename(output_path), size=(1200, 800))
    return FileResponse(output_path, filename="sourcing_map_image.png")
from fastapi import UploadFile

@app.post("/upload-location-csv")
async def upload_location_csv(file: UploadFile = File(...)):
    save_path = os.path.join("uploads", "mock_store_locations.csv")
    with open(save_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"message": "Store location CSV updated successfully"}
