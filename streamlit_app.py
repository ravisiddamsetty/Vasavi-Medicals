import streamlit as st
import pandas as pd
from supabase import create_client, Client
from datetime import datetime, timedelta
import json

# Production: Use Streamlit secrets
@st.cache_resource
def init_supabase() -> Client:
    return create_client(st.secrets["SUPABASE_URL"], st.secrets["SUPABASE_KEY"])

supabase: Client = init_supabase()

# Config
st.set_page_config(
    page_title="🏥 Vasavi Medicals Admin", 
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏥 Vasavi Medicals - Admin Dashboard")
st.markdown("---")

# Sidebar navigation
page = st.sidebar.selectbox("📋 Navigation", [
    "📊 Dashboard", 
    "📅 Upcoming Orders", 
    "👥 Customers", 
    "💊 Medicines", 
    "📦 All Orders"
])

if page == "📊 Dashboard":
    col1, col2, col3, col4 = st.columns(4)
    
    try:
        # Safe metrics
        c1 = supabase.table("customers").select("count").execute()
        c2 = supabase.table("subscriptions").select("count").eq("status", "active").execute()
        c3 = supabase.table("orders").select("count").eq("status", "pending").execute()
        
        with col1: st.metric("👥 Customers", c1.data[0]["count"])
        with col2: st.metric("📦 Active Subs", c2.data[0]["count"])
        with col3: st.metric("⏳ Pending Orders", c3.data[0]["count"])
        with col4: st.metric("📱 Next Delivery", "Mar 15")
        
    except Exception as e:
        st.error(f"❌ Database connection failed. Add secrets: {e}")
        st.info("👆 Go to Streamlit Cloud → Settings → Secrets → Add SUPABASE_URL & SUPABASE_KEY")

elif page == "📅 Upcoming Orders":
    st.header("📅 Upcoming Orders (Next 30 Days)")
    
    try:
        upcoming = supabase.table("subscriptions").select("*").lte(
            "next_delivery_date", (datetime.now() + timedelta(days=30)).isoformat()
        ).eq("status", "active").execute()
        
        if not upcoming.data:
            st.success("🎉 No upcoming orders! All caught up!")
        else:
            for sub in upcoming.data:
                with st.expander(f"📦 {sub['customer_name']} - {sub['next_delivery_date'][:10]}"):
                    medicines = json.loads(sub['medicines'])
                    total = 0
                    for med in medicines:
                        price = med.get('price', 0)
                        qty_price = price * med['quantity']
                        total += qty_price
                        st.write(f"• **{med['name']}** x{med['quantity']} - ₹{qty_price}")
                    
                    st.caption(f"**Total: ₹{total}**")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        if st.button("✅ Create Order", key=f"create_{sub['id'][:8]}"):
                            supabase.table("orders").insert({
                                "subscription_id": sub["id"],
                                "customer_name": sub["customer_name"],
                                "status": "pending",
                                "order_date": datetime.now().isoformat()
                            }).execute()
                            st.success("✅ Order created in database!")
                            st.rerun()
                    with col2:
                        if st.button("⏸️ Pause Sub", key=f"pause_{sub['id'][:8]}"):
                            supabase.table("subscriptions").update({"status": "paused"}).eq("id", sub["id"]).execute()
                            st.success("⏸️ Subscription paused!")
                            st.rerun()
                    with col3:
                        if st.button("📱 Send SMS", key=f"sms_{sub['id'][:8]}"):
                            st.info("📱 SMS integration coming soon!")
        
    except Exception as e:
        st.error(f"Error loading orders: {e}")

# Add other pages...
elif page == "👥 Customers":
    try:
        customers = supabase.table("customers").select("*").execute()
        st.dataframe(pd.DataFrame(customers.data), use_container_width=True)
    except:
        st.error("👥 Customers table not found")

elif page == "💊 Medicines":
    try:
        medicines = supabase.table("medicines").select("*").execute()
        st.dataframe(pd.DataFrame(medicines.data), use_container_width=True)
    except:
        st.error("💊 Medicines table not found")
