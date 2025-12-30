import streamlit as st #type:ignore
import requests #type:ignore
import pandas as pd #type:ignore
import plotly.express as px #type:ignore
from pymongo import MongoClient #type:ignore
import traceback
import os
import io
import sys
from minio import Minio  #type:ignore
from dotenv import load_dotenv #type: ignore

with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/2593/2593491.png", width=50)
    st.title("Menu")
    st.success("✅ Đã xác thực tự động")
    st.divider()
    st.info(f"API: `{API_URL}`")
    st.caption("v1.3 - Auto Auth")