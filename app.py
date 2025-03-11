import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
# test
survey_data = ("Data/report-2025-03-10T1407.csv")
df_survey = pd.read_csv(survey_data)

# Set Page Config
st.set_page_config(page_title="UJC Summit Registration Tracker Dashboard", layout="wide")

# Generate Fake Data
np.random.seed(42)
days = pd.date_range(start="2024-06-01", periods=60, freq="D")
# Just the summary (orders, attendees, Name aka location)
ticket_data = pd.read_csv("Data/Eventbrite Attendees Table - 2025-3-10.csv")
ticket_sales = ticket_data['Attendees']
web_traffic = np.random.randint(500, 2000, size=len(days))

# Event Statistics
total_sales = sum(ticket_sales)
total_budget = 7000
progress = (total_sales / total_budget) * 100

# Registrations Breakdown
returning_attendees = np.random.randint(400, 700)
new_students = np.random.randint(900, 1200)
ambassadors = np.random.randint(1300, 1600)
page_views = np.random.randint(23000, 30000)

# Ad Performance Data
platforms = ["Google Ads", "Facebook Ads", "Instagram Ads", "Twitter Ads"]
impressions = np.random.randint(200000, 500000, size=len(platforms))
clicks = np.random.randint(5000, 15000, size=len(platforms))
registrations = np.random.randint(500, 2000, size=len(platforms))
cost_per_reg = np.round(np.random.uniform(10, 20, size=len(platforms)), 2)

ad_data = pd.DataFrame({
    "Platform": platforms,
    "Impressions": impressions,
    "Clicks": clicks,
    "Registrations": registrations,
    "Cost Per Registration ($)": cost_per_reg
})

# Layout Design
st.title("🎟️ Event Tracker Dashboard")

# Top Metrics (Like Total Balance and Monthly Budget)
col1, col2 = st.columns(2)
with col1:
    st.metric("Total Ticket Sales", f"{total_sales:,.0f}")
    st.progress(progress / 100)
with col2:
    st.metric("Registration Goal", f"{total_budget:,.0f}")
    st.text(f"Progress: {progress:.2f}% achieved")


def analyze_survey_data(csv_file):
    # Load CSV file
    df = pd.read_csv(csv_file)
    
    # Define column names based on the given survey questions
    student_col = "Are you a student?"
    ambassador_col = "Did a UJC Ambassador Invite you to the Summit?"
    hearing_source_col = "How did you hear about that hear about the Summit?"
    advisor_col = "Did a UJC Advisor Invite you to the Summit?"

    # Ensure the expected columns exist in the dataset
    required_columns = [student_col, ambassador_col, hearing_source_col, advisor_col]
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        st.error(f"Missing expected columns: {missing_columns}")
        return

    # Fill NaN values with "Unknown" for better readability
    df.fillna("Unknown", inplace=True)

    # Count student responses (Yes/No)
    student_counts = df[student_col].value_counts().reset_index()
    student_counts.columns = ["Response", "Count"]

    # Count ambassador invitations (No / Custom Names)
    ambassador_counts = df[ambassador_col].value_counts().reset_index()
    ambassador_counts.columns = ["Response", "Count"]

    # Count hearing sources (Prebuilt List Options)
    hearing_source_counts = df[hearing_source_col].value_counts().reset_index()
    hearing_source_counts.columns = ["Response", "Count"]

    # Count advisor invitations (Custom Names)
    advisor_counts = df[advisor_col].value_counts().reset_index()
    advisor_counts.columns = ["Response", "Count"]

    # Display results in Streamlit
    #st.title("📊 Survey Data Analysis")


import matplotlib.pyplot as plt
import plotly.express as px


# Ensure "Order Date" is in datetime format
df_survey["Order Date"] = pd.to_datetime(df_survey["Order Date"], utc=True)
df_survey["Order Date"] = df_survey["Order Date"].dt.tz_localize(None)  # Remove timezone info

# Extract only the date part (drop time)
df_survey["Order Date"] = df_survey["Order Date"].dt.date

# Count occurrences of each unique date
date_counts = df_survey["Order Date"].value_counts().reset_index()
date_counts.columns = ["Order Date", "Count"]
date_counts = date_counts.sort_values("Order Date")  # Ensure proper chronological order

# Display the corrected table in Streamlit
#st.dataframe(date_counts)  # ✅ Now groups only by Date

# Create interactive line chart with customized hover text
fig = px.line(date_counts, x="Order Date", y="Count", markers=True, 
              title="Registrations Over Time (Daily)",
              labels={"Order Date": "Date", "Count": "Total Orders"},
              template="plotly_white")

# Customize the hover text
fig.update_traces(
    hovertemplate="Registrants: %{y}<extra></extra>",
    mode="lines+markers"
)


fig.update_layout(
    xaxis_tickangle=-45,
    hovermode="x unified"
)

# Display the chart in Streamlit
st.plotly_chart(fig, use_container_width=True)





### 


# Define survey exclusion criteria
invalid_entries = ["unknown", "no", "none", "n/a", "na"]

num_rows = df_survey.shape[0]

# Filter the dataset by excluding invalid entries
# Compute metrics
#summit_attendees = df_filtered[df_filtered['event'] == "Summit"]["registrations"].count()
summit_attendees = 0
students_registered = df_survey[
    (df_survey['Are you a student?'] == "Yes") &
    (~df_survey['Are you a student?'].astype(str).str.lower().isin(invalid_entries))
].shape[0]
#ambassadors_registered = df_filtered[df_filtered['Did a UJC Ambassador Invite you to the Summit?'] == "Ambassador"]["registrations"].count()
ambassadors_registered = df_survey[~df_survey['Did a UJC Ambassador Invite you to the Summit?'].astype(str).str.lower().isin(invalid_entries)].shape[0]
#eventbrite_views = df_filtered["page_views"].sum()  # Assuming page_views column exists
eventbrite_views = 0


# Custom CSS for styling
custom_css = """
<style>
    .metric-box {
        text-align: center;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
        font-family: Arial, sans-serif;
    }
    .title {
        font-size: 18px;
        color: white;
    }
    .number {
        font-size: 36px;
        font-weight: bold;
    }
    .blue { color: #25F4EE; }
    .pink { color: #FF2674; }
    .orange { color: #FF9800; }
</style>
"""
st.markdown(custom_css, unsafe_allow_html=True)

# Create columns for metrics
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f'<div class="metric-box"><div class="title">Returning Summit Attendees</div><div class="number blue">{summit_attendees:,}</div></div>', unsafe_allow_html=True)

with col2:
    st.markdown(f'<div class="metric-box"><div class="title">Students Registered</div><div class="number pink">{students_registered:,}</div></div>', unsafe_allow_html=True)

with col3:
    st.markdown(f'<div class="metric-box"><div class="title">Total Ambassador Registrations</div><div class="number orange">{ambassadors_registered:,}</div></div>', unsafe_allow_html=True)

with col4:
    st.markdown(f'<div class="metric-box"><div class="title">Eventbrite Page Views</div><div class="number orange">{eventbrite_views:,}</div></div>', unsafe_allow_html=True)


st.sidebar.header("UJC Summit Tracker")
# From custom survey questions report (default)

analyze_survey_data(survey_data)


# # Key Insights (Like Savings Goal)
# st.subheader("📊 Key Event Metrics")
# col1, col2, col3, col4 = st.columns(4)
# col1.metric("Returning Attendees", returning_attendees)
# col2.metric("New Students", new_students)
# col3.metric("Ambassador Registrations", ambassadors)
# col4.metric("Page Views", f"{page_views:,}")

# # Sales Trend Chart (Like Savings Statistic)
# st.subheader("📈 Ticket Sales & Web Traffic Over Time")
# sales_df = pd.DataFrame({"Date": days, "Ticket Sales": ticket_sales, "Web Traffic": web_traffic})
# fig = px.line(sales_df, x="Date", y=["Ticket Sales", "Web Traffic"], title="Event Performance Trends")
# st.plotly_chart(fig, use_container_width=True)

# # Ad Performance Table
# st.subheader("📢 Paid Promotion Performance")
# st.dataframe(ad_data)

# # Recent Transactions (Like Recent Transactions)
# st.subheader("💳 Recent Ticket Purchases")
# recent_transactions = pd.DataFrame({
#     "Name": ["John Doe", "Jane Smith", "Alex Johnson", "Emily Davis"],
#     "Date": pd.to_datetime(["2025-03-01", "2025-02-28", "2025-02-27", "2025-02-26"]),
#     "Transaction": ["Credit Card", "Bank Transfer", "PayPal", "Crypto"],
#     "Amount": ["$120.00", "$85.50", "$150.00", "$99.99"],
#     "Status": ["Completed", "Pending", "Completed", "Failed"]
# })
# st.dataframe(recent_transactions)

# st.write("📌 *This dashboard is a prototype and uses simulated data.*")
# --------------------------------------------------------------------------------------------------
#State 


# # Set Streamlit Page Config
# st.set_page_config(page_title="US Event Registrations Map", layout="wide")

# # Sample Data: Event Registrations by U.S. State
# state_data = {
#     "State": ["California", "Texas", "Florida", "New York", "Illinois", "Pennsylvania", "Ohio", "Georgia", "North Carolina", "Michigan"],
#     "Abbreviation": ["CA", "TX", "FL", "NY", "IL", "PA", "OH", "GA", "NC", "MI"],
#     "Registrations": [1500, 1300, 1100, 950, 870, 820, 780, 750, 720, 700]
# }

# # Convert to DataFrame
# df = pd.DataFrame(state_data)

# # Get Latitude & Longitude for Each State
# state_coords = {
#     "CA": [36.7783, -119.4179], "TX": [31.9686, -99.9018], "FL": [27.9944, -81.7603],
#     "NY": [40.7128, -74.0060], "IL": [40.6331, -89.3985], "PA": [41.2033, -77.1945],
#     "OH": [40.4173, -82.9071], "GA": [32.1656, -82.9001], "NC": [35.7596, -79.0193],
#     "MI": [44.3148, -85.6024]
# }

# # Add Latitude & Longitude to DataFrame
# df["Latitude"] = df["Abbreviation"].map(lambda x: state_coords[x][0])
# df["Longitude"] = df["Abbreviation"].map(lambda x: state_coords[x][1])

# # Create US Map with Plotly
# fig = px.scatter_geo(
#     df,
#     lat="Latitude",
#     lon="Longitude",
#     text="State",
#     size="Registrations",
#     size_max=30,  # Control max circle size
#     projection="albers usa",
#     title="Event Registrations by State",
#     color_discrete_sequence=["blue"]
# )

# # Display in Streamlit
# st.title("🗺️ Event Registrations Across the U.S.")
# st.plotly_chart(fig, use_container_width=True)

# st.write("📌 *Bubble sizes represent total event registrations per state.*")
