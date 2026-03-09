import streamlit as st
import pandas as pd
from supabase import create_client
from datetime import datetime, timedelta
import json

# Supabase connection (use secrets)
@st.cache_resource
def init_supabase():
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase = init_supabase()

st.set_page_config(
    page_title="🏥 Medical Store Admin", 
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏥 Medical Store Admin Dashboard")
st.markdown("---")

# Professional sidebar
page = st.sidebar.selectbox(
    "Navigation", 
    ["📊 Dashboard", "📅 Upcoming Orders", "👥 Customers", "💊 Medicines", "📦 Orders"]
)

if page == "📊 Dashboard":
    col1, col2, col3, col4 = st.columns(4)
    
    # Key metrics
    c1 = supabase.table("customers").select("count").execute()
    c2 = supabase.table("subscriptions").select("count").eq("status", "active").execute()
    c3 = supabase.table("orders").select("count").eq("status", "pending").execute()
    c4 = supabase.table("subscriptions").select("sum(price)").execute()
    
    with col1: st.metric("👥 Total Customers", c1.data[0]["count"])
    with col2: st.metric("📦 Active Subscriptions", c2.data[0]["count"])
    with col3: st.metric("⏳ Pending Orders", c3.data[0]["count"])
    with col4: st.metric("💰 Revenue", "₹0")  # Add later

elif page == "📅 Upcoming Orders":
    st.header("📅 Upcoming Orders (Next 30 Days)")
    
    upcoming = supabase.table("subscriptions").select("*").lte(
        "next_delivery_date", (datetime.now() + timedelta(days=30)).isoformat()
    ).eq("status", "active").execute()
    
    for sub in upcoming.data:
        with st.expander(f"📦 {sub['customer_name']} - {sub['next_delivery_date'][:10]}", expanded=False):
            medicines = json.loads(sub['medicines'])
            for med in medicines:
                st.write(f"• **{med['name']}** x{med['quantity']} - ₹{med.get('price', 0)*med['quantity']}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("✅ Create Order", key=f"order{sub['id'][:8]}"):
                    order = supabase.table("orders").insert({
                        "subscription_id": sub["id"],
                        "customer_name": sub["customer_name"],
                        "status": "pending"
                    }).execute()
                    st.success("✅ Order created!")
                    st.rerun()
            with col2:
                if st.button("⏸️ Pause", key=f"pause{sub['id'][:8]}"):
                    supabase.table("subscriptions").update({"status": "paused"}).eq("id", sub["id"]).execute()
                    st.rerun()
            with col3:
                if st.button("📱 SMS", key=f"sms{sub['id'][:8]}"):
                    st.info("📱 SMS reminder sent!")

# Add other pages similarly...
