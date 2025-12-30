import streamlit as st #type:ignore
import requests #type:ignore
import pandas as pd #type:ignore
import plotly.express as px #type:ignore
from pymongo import MongoClient #type:ignore
import traceback
import os
import io
import sys
from PIL import Image #type:ignore
from minio import Minio  #type:ignore
from dotenv import load_dotenv #type: ignore
load_dotenv(".env")
MONGO_URI = os.getenv('MONGO_URI')
DB_NAME = "api_request_log"
COLLECTION_NAME = "test_yolo_12_confi_0.3"
BUCKET_NAME = "test-yolo12-confi-0.3"
MINIO_CONF = {
    "endpoint": "localhost:9000",
    "access_key": os.getenv("MINIO_ACCESS_KEY"),
    "secret_key": os.getenv("MINIO_SECRET_KEY"),
    "secure": False
}

@st.cache_resource
def get_minio_client():
    return Minio(
        endpoint=MINIO_CONF["endpoint"],
        access_key=MINIO_CONF["access_key"],
        secret_key = MINIO_CONF["secret_key"],
        secure = MINIO_CONF["secure"]
    )
@st.cache_resource
def get_mongo_client():
    client = MongoClient(MONGO_URI)
    return client[DB_NAME][COLLECTION_NAME]

def get_image_from_minio(client, bucket, object_name):
    response = client.get_object(bucket, object_name)
    img_data = response.read()
    response.close()
    response.release_conn()
    return Image.open(io.BytesIO(img_data))

st.set_page_config(layout="wide", page_title="Image Processing Dashboard")
st.title("📸 Hệ thống visualize ảnh ở các step")
collection = get_mongo_client()
minio_client = get_minio_client()

all_records = list(collection.find({}, {"_id": 0}))
total_items = len(all_records)

tab1, tab2 = st.tabs(["🖼️ So sánh Ảnh (Visual)", "📊 Metadata (Data)"])

with tab1:
    st.header("So sánh quy trình xử lý ảnh")
    
    # Cấu hình phân trang
    col_ctrl1, col_ctrl2 = st.columns([1, 4])
    with col_ctrl1:
        items_per_page = st.selectbox("Số ảnh mỗi trang:", [5, 10, 20], index=0)
    
    # Tính toán số trang
    total_pages = (total_items // items_per_page) + (1 if total_items % items_per_page > 0 else 0)
    
    with col_ctrl2:
        current_page = st.number_input(f"Chọn trang (Tổng: {total_pages})", min_value=1, max_value=total_pages, step=1)

    # Logic lấy data của trang hiện tại (Slice data)
    start_idx = (current_page - 1) * items_per_page
    end_idx = start_idx + items_per_page
    current_batch = all_records[start_idx:end_idx]

    st.divider()

    # Header của bảng ảnh
    cols = st.columns([1, 2, 2, 2])
    cols[0].markdown("**Tên file**")
    cols[1].markdown("**Gốc (MinIO)**")
    cols[2].markdown("**Tiền xử lý (MinIO)**")
    cols[3].markdown("**Đã xử lý (MinIO)**")

    # Loop qua từng dòng dữ liệu của trang hiện tại
    for item in current_batch:
        file_name = item.get("filename", "Unknown")
        path = item.get("minio_image_path", {})
        # Tạo row mới
        row = st.columns([1, 2, 2, 2])
        
        # Cột 1: Tên
        row[0].code(file_name)
        
        # Cột 2: Ảnh Gốc
        img_raw = get_image_from_minio(minio_client, BUCKET_NAME, path)
        if img_raw:
            row[1].image(img_raw, use_container_width=True)
        else:
            row[1].error("Not found")

        # Cột 3: Ảnh Preprocessing
        # Giả sử tên file ở bucket này có thêm prefix hoặc giữ nguyên
        img_pre = get_image_from_minio(minio_client, BUCKET_NAME, path)
        if img_pre:
            row[2].image(img_pre, use_container_width=True)
        else:
            row[2].info("Pending...")

        # Cột 4: Ảnh Processing
        img_proc = get_image_from_minio(minio_client, BUCKET_NAME, path)
        if img_proc:
            row[3].image(img_proc, use_container_width=True)
        else:
            row[3].info("Pending...")
            
        st.divider()
with tab2:
    st.header("Bảng dữ liệu Metadata chi tiết")
    
    # Chuyển đổi list dict thành DataFrame
    df = pd.DataFrame(all_records)
    
    # Làm phẳng (Flatten) dữ liệu nếu nó lồng nhau
    # Nếu metadata đơn giản thì không cần bước này
    if "preprocessing_meta" in df.columns:
        df_pre = pd.json_normalize(df["preprocessing_meta"]).add_prefix("Pre_")
        df = pd.concat([df.drop(columns=["preprocessing_meta"], errors='ignore'), df_pre], axis=1)
        
    if "processing_meta" in df.columns:
        df_proc = pd.json_normalize(df["processing_meta"]).add_prefix("Proc_")
        df = pd.concat([df.drop(columns=["processing_meta"], errors='ignore'), df_proc], axis=1)

    # Hiển thị bảng tương tác
    st.dataframe(
        df, 
        use_container_width=True, 
        height=600,
        column_config={
            "filename": st.column_config.TextColumn("Tên File", pinned=True),
            # Bạn có thể định dạng thêm các cột khác tại đây
        }
    )