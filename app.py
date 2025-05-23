import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime, timedelta
import folium
from streamlit_folium import st_folium
import os
import matplotlib.pyplot as plt
# from st_aggrid import AgGrid, GridOptionsBuilder
# from st_aggrid.shared import GridUpdateMode
from dotenv import load_dotenv
from pydomo import Domo
import plotly.graph_objects as go

# Set page config
st.set_page_config(page_title="UJC Summit Registration Tracker Dashboard", layout="wide")

# Utility: Generate a "refresh token" that only changes on Fridays
def get_friday_token():
    today = datetime.now()
    if today.weekday() == 4:  # Friday is weekday 4
        return today.strftime("%Y-%m-%d")
    else:
        return "no-refresh"
    
load_dotenv() 
url_1 = os.getenv("DROPBOX_URL")
def get_cached_data(url):
    return pd.read_csv(url)
df_domo = get_cached_data(url_1)
df_domo2 = df_domo.copy()
# Define a helper to clean numeric columns
def clean_numeric(series, force_int=False):
# Step 1: Clean the string
    cleaned = (
    series.astype(str)
            .str.strip()
            .replace(['-', '–', '—', ' - ', ' - ', '', 'nan', 'None'], '0', regex=False)
            .replace('[\$,]', '', regex=True)
)

# Step 2: Convert to float
    cleaned = cleaned.astype(float)

    # Step 3: Convert to int if needed
    if force_int:
        cleaned = cleaned.round().astype(int)

    return cleaned

# Apply cleaning to relevant columns
df_domo["Amount Spent"] = clean_numeric(df_domo["Amount Spent"])
df_domo["Impressions"] = clean_numeric(df_domo["Impressions"], force_int=True)
df_domo["CPC (Cost Per Click)"] = clean_numeric(df_domo["CPC (Cost Per Click)"])
df_domo["Leads"] = clean_numeric(df_domo["Leads"], force_int=True)
df_domo["Clicks"] = clean_numeric(df_domo["Click"], force_int=True)

# Filter the Total row
total_row = df_domo[df_domo["Platform"] == "Total"]

# Pull each metric safely
amount_spent = total_row["Amount Spent"].values[0] if not total_row.empty else 0
impressions = total_row["Impressions"].values[0] if not total_row.empty else 0
cpc = total_row["CPC (Cost Per Click)"].values[0] if not total_row.empty else 0
leads = total_row["Leads"].values[0] if not total_row.empty else 0
clicks = total_row["Clicks"].values[0] if not total_row.empty else 0
cpl = total_row["Cost Per Lead"].values[0] if not total_row.empty else 0

# # Cache the Domo pull, but only refresh on Fridays
# @st.cache_data
# def get_domo_data(refresh_token):  # passing token makes Streamlit recache
#     load_dotenv()
#     client_id = os.getenv("DOMO_CLIENT_ID")
#     client_secret = os.getenv("DOMO_CLIENT_SECRET")
#     api_host = os.getenv("DOMO_API_HOST", "api.domo.com")  # fallback to default if not set
#     dataset_id = os.getenv("DOMO_DATASET_ID")

#     domo = Domo(client_id, client_secret, api_host=api_host)
#     data = domo.ds_get(dataset_id)
#     df = pd.DataFrame(data)
#     return df

# # Use the token to control refresh
# refresh_token = get_friday_token()
# data_domo = get_domo_data(refresh_token)

# PASSWORD = os.getenv("STREAMLIT_PASSWORD")

# Initialize session state
# if "authenticated" not in st.session_state:
#     st.session_state.authenticated = False

# Authentication
# if not st.session_state.authenticated:
#     user_input = st.text_input("Enter Password:", type="password")

#     if st.button("Submit"):
#         if user_input == PASSWORD:
#             st.session_state.authenticated = True
#             st.rerun()  # Refresh the app
#         else:
#             st.error("Incorrect password. Try again.")

# Shows the dashboard if authenticated
# if st.session_state.authenticated:
#     st.success("Access Granted!")
st.write("Welcome to the UJC Summit 2025 Dashboard!")

tabs = ["Event Tracker", "Registration Leaderboard", "Repeat Registrants", "Paid Promotions"]
tab1, tab2, tab3, tab4 = st.tabs(tabs)

# Sidebar instructions
instructions = {
    "Event Tracker": "Track event registrations by date, location, and by type (student, ambassador referral, advisor referral).",
    "Registration Leaderboard": "View the top contributors and sources driving the most registrations.",
    "Repeat Registrants": "View the number of individuals who registered for previous summits.",
    "Paid Promotions": "View the performance of paid advertisement campaigns across Meta, Google, and LinkedIn."
}
st.sidebar.header("UJC Summit 2025 Tracker")
st.sidebar.markdown("### Updated 12pm daily.")

st.sidebar.markdown("### Overview:")
for tab, instruction in instructions.items():
    st.sidebar.markdown(f"**<u>{tab}</u>:** {instruction}", unsafe_allow_html=True)

st.sidebar.markdown("#### Collapse sidebar for a full-screen view.")

def process_attendance_data(csv_file):
    """
    Processes the CSV file to:
      1. Calculate the total sum of attendees (students + non-students).
      2. Return a count table of Ambassador Point of Contact responses.
      3. Aggregate student registrations per date (group_dates).
      4. Sum the non-student registrations based on empty age-range responses.
      5. Aggregate student registrations by state.

    Args:
        csv_file (str): Path to the CSV file.

    Returns:
        tuple: (total_attendees, ambassador_counts, ambassador_totals, group_dates, 
                non_student_registrations, state_totals)
    """
    
    # Load CSV into a DataFrame
    df = pd.read_csv(csv_file)

    # Define target columns
    attendee_col = "How many students will be attending with your group?"
    ambassador_col = "Ambassador Point of Contact"
    timestamp_col = "Timestamp"
    state_col = "School State (Please abbreviate, example: NJ for New Jersey)"

    # Ensure required columns exist
    required_columns = [attendee_col, ambassador_col, timestamp_col, state_col]
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        raise ValueError(f"Missing required columns in the CSV file: {missing_columns}")

    # Convert attendee column to numeric and compute total registrations
    df[attendee_col] = pd.to_numeric(df[attendee_col], errors="coerce")
    total_attendees = df[attendee_col].sum(skipna=True)

    # Clean and process Ambassador column
    df[ambassador_col] = df[ambassador_col].astype(str).str.strip().str.lower()
    df = df[df[ambassador_col] != "nan"]

    # Build the ambassador counts table
    ambassador_counts = df[ambassador_col].value_counts().reset_index()
    ambassador_counts.columns = ["Ambassador Name", "Count"]

    # Group ambassador totals by state
    ambassador_totals = (
        df.groupby([ambassador_col, state_col], as_index=False)
        .agg(
            Count=(ambassador_col, "size"),
            Total_Attendees=(attendee_col, "sum")
        )
    )

    # Clean state column
    df[state_col] = df[state_col].astype(str).fillna("").str.strip().str.upper()

    # Identify non-student registrations
    non_student_mask = df[state_col].isin(["", "N/A", "NULL"])
    non_student_registrations = df.loc[non_student_mask, attendee_col].sum(skipna=True)

    # Filter only student registrations
    student_df = df[~non_student_mask].copy()

    # Convert Timestamp column to datetime and extract date
    student_df[timestamp_col] = pd.to_datetime(student_df[timestamp_col], utc=True, errors="coerce")
    student_df["Order Date"] = student_df[timestamp_col].dt.date  # extract date only

    # Aggregate total student attendees per date
    group_dates = student_df.groupby("Order Date")[attendee_col].sum().reset_index()
    group_dates.columns = ["Order Date", "Total Attendees"]
    group_dates = group_dates.sort_values("Order Date")

    # Aggregate student registrations by state
    state_totals = student_df.groupby(state_col)[attendee_col].sum().reset_index()
    state_totals.columns = ["StateCode", "Total_Attendees"]

    return total_attendees, ambassador_counts, ambassador_totals, group_dates, non_student_registrations, state_totals


def format_name(full_name):
    parts = full_name.split()
    if len(parts) >= 2:
        return f"{parts[0].capitalize()} {parts[1][0].upper()}."
    return f"{parts[0].capitalize()}." if parts else ""


# Custom responses to survey questions + open ended
load_dotenv() 
if "REPORT_URL" in os.environ:
    survey_data = os.getenv("REPORT_URL")
else:
    survey_data = st.secrets["REPORT_URL"]
#survey_data = os.getenv("REPORT_URL")#("Data/Eventbrite Survey - 324 report.csv")
# Just the summary (orders, attendees, Name aka location)
if "TABLE_URL" in os.environ:
    order_data = os.getenv("TABLE_URL")
else:
    order_data = st.secrets["TABLE_URL"]
#order_data = os.getenv("TABLE_URL") #("Data/Eventbrite Attendees Table - 2025-3-24.csv")
# Group survey form
group_data = ("Data/Perm/Eventbrite Survey - Copy of group surv (3).csv")

#Change here order may not be right for function!!!!!!
group_signups, group_ambassador_registrations, ambassador_totals, group_dates, non_student_registrations, state_totals = process_attendance_data(group_data)
# Apply name formatting
group_ambassador_registrations["Ambassador Name"] = group_ambassador_registrations["Ambassador Name"].apply(format_name)
# Aggregate counts to combine duplicate initials
temp_ambassador_counts = group_ambassador_registrations.groupby("Ambassador Name", as_index=False)["Count"].sum()

df_survey = pd.read_csv(survey_data)

def analyze_survey_data(csv_file):
        df = pd.read_csv(csv_file)
        # Survey questions
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
        
        df = df.astype(str).fillna("Unknown")

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
        return ambassador_counts,advisor_counts,hearing_source_counts

ambassador_counts, advisor_counts, hearing_source_counts = analyze_survey_data(survey_data)
filtered_advisor_counts = advisor_counts[(advisor_counts["Response"] != "No") & (advisor_counts["Response"] != "nan")]
filtered_ambassador_counts = ambassador_counts[(ambassador_counts["Response"] != "No") & (ambassador_counts["Response"] != "nan")]
filtered_hearing_source_counts = hearing_source_counts[(hearing_source_counts["Response"] != "No") & (hearing_source_counts["Response"] != "nan") & (hearing_source_counts["Response"] != "Other (Please describe in next question)")]

def process_and_calc_returners(file1, file2, file3):
    # Load the CSV files
    df1 = pd.read_csv(file1)
    df2 = pd.read_csv(file2)
    df3 = pd.read_csv(file3)

    df1 = df1[['Name']]  
    df2 = df2[['Name']] 
    df3 = df3[['First Name', 'Last Name']]

    df3["Name"] = (df3["First Name"].astype(str).str.strip() + " " + df3["Last Name"].astype(str).str.strip()).str.lower()

    df3 = df3[["Name"]]

    for df in [df1, df2, df3]:
        df["Name"] = df["Name"].astype(str).str.replace(r'\s+', ' ', regex=True).str.strip().str.lower()

    df1 = df1.drop_duplicates(subset=["Name"])
    df2 = df2.drop_duplicates(subset=["Name"])
    df3 = df3.drop_duplicates(subset=["Name"])

    # Finding Returning Users 

        # 2022 and 2023
    t22to23 = pd.concat([df1, df2], ignore_index=True)
    name_counts_22_23 = t22to23["Name"].value_counts()
    duplicates_22_23 = name_counts_22_23[name_counts_22_23 > 1].reset_index()
    duplicates_22_23.columns = ["Name", "Count"]
        # 2023 and 2025
    t23to25 = pd.concat([df2, df3], ignore_index=True)
    name_counts_23_25 = t23to25["Name"].value_counts()
    duplicates_23_25 = name_counts_23_25[name_counts_23_25 > 1].reset_index()
    duplicates_23_25.columns = ["Name", "Count"]

        # All 3 summits
    t22to25 = pd.concat([df1, df2, df3], ignore_index=True)
    name_counts_22_23_25 = t22to25["Name"].value_counts()
    duplicates_22_23_25 = name_counts_22_23_25[name_counts_22_23_25 > 2].reset_index()
    duplicates_22_23_25.columns = ["Name", "Count"]

        # Finding returning users between 2022 and 2025
    t22and25 = pd.concat([df1, df3], ignore_index=True)
    name_counts_22_25 = t22and25["Name"].value_counts()
    duplicates_22_25 = name_counts_22_25[name_counts_22_25 > 1].reset_index()
    duplicates_22_25.columns = ["Name", "Count"]

    return duplicates_22_23, duplicates_23_25, duplicates_22_23_25, duplicates_22_25

with tab1:
    st.image("Data/Perm/UJC_Summit_Logo_2023_horizontal-logo-wordmark-3-white.png")
    # Just the summary (orders, attendees, Name aka location)
    ticket_data = pd.read_csv(order_data)
    ticket_sales = ticket_data['Attendees']

    # Event Statistics
    total_sales = sum(ticket_sales) + group_signups + non_student_registrations + leads #2647
    total_budget = 7000
    progress = (total_sales / total_budget) * 100
    print(total_sales)

    event_date = datetime(2025, 5, 30)  # Change to your event date
    # Get today's date
    today = datetime.today()
    # Calculate days remaining
    days_until_event = (event_date - today).days

    st.markdown(f"""
    ### <span style='color: orange; font-weight: bold;'>{days_until_event}</span> days until UJC Summit 2025! 🎉
    """, unsafe_allow_html=True)

    st.title("🎟️ Event Tracker Dashboard")

    col1, col2 = st.columns([0.8, 0.2])
    with col1:
        st.metric("Total Ticket Sales", f"{total_sales:,.0f}")
        st.progress(min(progress / 100, 1.0))  # caps at 100% for visual bar
    with col2:
        st.metric("Registration Goal", f"{total_budget:,.0f}")
        st.text(f"Progress: {progress:.2f}% achieved")

        df_survey["Order Date"] = pd.to_datetime(df_survey["Order Date"], utc=True)
    df_survey["Order Date"] = df_survey["Order Date"].dt.tz_localize(None)  # Remove timezone info

    # Extract only the date part (drop time)
    df_survey["Order Date"] = df_survey["Order Date"].dt.date

    # Count occurrences of each unique date
    date_counts = df_survey["Order Date"].value_counts().reset_index()
    date_counts.columns = ["Order Date", "Count"]
    date_counts = date_counts.sort_values("Order Date")  # Ensure proper chronological order

    merged_dates = pd.merge(date_counts, group_dates, on="Order Date", how="outer").fillna(0)

    # Sum up values from both sources
    merged_dates["Total Registrations"] = merged_dates["Count"] + merged_dates["Total Attendees"]
    
    # --- Load ad_time from Google Sheet CSV (registrations only) ---
    load_dotenv()
    ad_time_path = os.getenv("ADOT")  # This must be a public .csv export URL
    ad_time = pd.read_csv(ad_time_path)

    # Clean ad_time columns and types
    ad_time.columns = ad_time.columns.str.strip()
    ad_time["Order Date"] = pd.to_datetime(ad_time["Order Date"]).dt.date
    ad_time["Registrations"] = ad_time["Registrations"].fillna(0)

    # --- Final merge: combine everything ---
    final_df = pd.merge(merged_dates, ad_time, on="Order Date", how="outer").fillna(0)

    # Update final total
    final_df["Total Registrations"] += final_df["Registrations"]

    # Only keep necessary columns
    final_df = final_df[["Order Date", "Total Registrations"]].sort_values("Order Date")
    average_daily_regis = int((final_df['Total Registrations'].mean()))
    
    st.write(f"Group Signup Form Registrations: {group_signups:,}")
    st.write(f"Advertisement Registrations: {leads:,}")
    st.write(f"Eventbrite Registrations: {sum(ticket_sales):,}")#Eventbrite Registrations: 2,647
    st.write(f"Average Daily Registrations: <u>{average_daily_regis:,}</u>. Projected to gain {average_daily_regis*days_until_event:,} registrations by 5/30.",unsafe_allow_html=True)
   
    # Plot
    fig = px.line(final_df, x="Order Date", y="Total Registrations", markers=True,
                title="Registrations Over Time (Daily)",
                labels={"Order Date": "Date", "Total Registrations": "Total Registrations"},
                template="plotly_white")
    
    fig.update_traces(
    hovertemplate='Registration: %{y}<extra></extra>'
)
    fig.update_layout(
        xaxis_tickangle=-45,
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

    # # Assume final_df is already defined and sorted by "Order Date"
    # final_df["DoD Change"] = final_df["Total Registrations"].diff()
    # fig_dod = px.line(final_df, x="Order Date", y="DoD Change", markers=True,
    #                   title="Day-over-Day Change in Registrations",
    #                   labels={"Order Date": "Date", "DoD Change": "Change"},
    #                   template="plotly_white")
    # fig_dod.update_traces(hovertemplate='Change: %{y}<extra></extra>')
    # fig_dod.update_layout(xaxis_tickangle=-45, hovermode="x unified")
    # st.plotly_chart(fig_dod, use_container_width=True)


    # Compute DoD Change
    final_df["DoD Change"] = final_df["Total Registrations"].diff()
    final_df["Order Date"] = pd.to_datetime(final_df["Order Date"])
    final_df = final_df[final_df["Order Date"] >= pd.to_datetime("2025-04-10")].reset_index(drop=True)
    final_df = final_df.dropna().reset_index(drop=True)

    # Determine label colors
    label_colors = ['green' if val >= 0 else 'red' for val in final_df["DoD Change"]]

    # Create base line chart
    fig_dod = go.Figure()

    fig_dod.add_trace(go.Scatter(
        x=final_df["Order Date"],
        y=final_df["DoD Change"],
        mode="lines+markers+text",
        line=dict(color="royalblue", width=2),
        marker=dict(size=6, color="royalblue"),
        text=[f"{val:.0f}" for val in final_df["DoD Change"]],
        textposition="top center",
        textfont=dict(color=label_colors),
        name="DoD Change",
        hovertemplate='Change: %{y}<extra></extra>'
    ))

    # Add horizontal reference line at y=0
    fig_dod.add_shape(
        type="line",
        x0=final_df["Order Date"].min(),
        x1=final_df["Order Date"].max(),
        y0=0, y1=0,
        line=dict(color="gray", width=1, dash="dash")
    )

    # Layout
    fig_dod.update_layout(
        title="Day-over-Day Change in Registrations",
        xaxis_title="Date",
        yaxis_title="Change",
        template="plotly_white",
        hovermode="x unified",
        xaxis_tickangle=-45
    )

    # Display
    st.plotly_chart(fig_dod, use_container_width=True)

    # Define survey exclusion criteria
    invalid_entries = ["unknown", "no", "none", "n/a", "na", "NA", "nan"]

    num_rows = df_survey.shape[0]

    # STUDENTS REGISTERED COUNT
    students_registered = df_survey[
        (df_survey['Are you a student?'] == "Yes") &
        (~df_survey['Are you a student?'].astype(str).str.lower().isin(invalid_entries))
    ].shape[0]    
    
    # AMBASSADOR INVITE COUNT
    #ambassadors_registered = df_survey[~df_survey['Did a UJC Ambassador Invite you to the Summit?'].astype(str).str.lower().isin(invalid_entries)].shape[0]
    #related to number ambassadors registered 
    num_amb_registered = filtered_ambassador_counts["Count"].sum() + group_signups #+ group_ambassador_registrations["Count"].sum()

    # ADVISOR INVITE COUNT 
    num_adv_registered = filtered_advisor_counts["Count"].sum()
    # EVENTBRITE VIEW COUNT (MANUAL)
    eventbrite_views = 18616
    previous_eventbrite_views = 17094
    #test change
    #df1_res, df2_res, df3_res, df4_res = process_and_calc_returners(data_2022,data_2023,survey_data)
    load_dotenv() 
    data_2022 = os.getenv("DATA_2022")
    data_2023 = os.getenv("DATA_2023")
    #df1_res, df4_res, df2_res, df3_res = process_and_calc_returners(data_2022,data_2023,survey_data)
    df1_res, df4_res, df2_res, df3_res = 690,281,998,200
    df1_old, df4_old, df2_old, df3_old = 690,276,969,197

    # PREVIOUS ATTENDEE COUNT
    include_words = [
    "email","Via email","email list","email list","mailing list","direct email","email blast","emailed"] #"Roc","Roc Nation","RocNation","rocnation","Rocnation", "ROC Nation","ROC nation","ujc",
    
    exclude_words = ["colleague", "friend", "aware"]

# Function to check if a response should be included
    def should_include(response):
        response_lower = response.lower() if isinstance(response, str) else ""
        
        # Check if any include word is present
        if any(word in response_lower for word in include_words):
            # Ensure no exclude words are present
            if not any(word in response_lower for word in exclude_words):
                return True
        return False
    # filtered_prev_attendees = advisor_counts[(advisor_counts["Response"] != "No") & (advisor_counts["Response"] != "nan")]
    test_3 = df_survey[df_survey["If you answered \"Other\" to the. previous question -"].apply(should_include) & df_survey["Did a UJC Ambassador Invite you to the Summit?"]]
    filtered_prev_attendees = df_survey[df_survey["If you answered \"Other\" to the. previous question -"].apply(should_include)]
    prev_attendee_response = len(filtered_prev_attendees)
    test_4 = len(test_3)
    print(test_4)
    #st.table(filtered_prev_attendees)

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
            font-size: 40px;
            font-weight: bold;
        }
        .blue { color: #25F4EE; }
        .pink { color: #FF2674; }
        .orange { color: #FF9800; }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)

    # Create columns for metrics
    col2, col3, col4, col5 = st.columns(4)
    
    with col2:
        st.markdown(f'<div class="metric-box"><div class="title">Students Registered</div><div class="number pink">{students_registered+group_signups:,}</div></div>', unsafe_allow_html=True)

    with col3:
        st.markdown(f'<div class="metric-box"><div class="title">Ambassador Driven Registrations</div><div class="number orange">{num_amb_registered+test_4:,}</div></div>', unsafe_allow_html=True)

    with col4:
        st.markdown(f'<div class="metric-box"><div class="title">Advisor Driven Registrations</div><div class="number" style="color: #FEC110;">{num_adv_registered:,}</div></div>', unsafe_allow_html=True)

    views_diff = eventbrite_views-previous_eventbrite_views
    # Calculate percentage change
    if previous_eventbrite_views > 0:
        percentage_change = ((eventbrite_views - previous_eventbrite_views) / previous_eventbrite_views) * 100
    else:
        percentage_change = 0  # Avoid division by zero

    # Determine color and symbol for percentage change
    if percentage_change > 0:
        change_html = f'<p style="font-size: 14px; color: green; margin-top: -10px;">▲ {views_diff}, ({percentage_change:.1f}%) from last week</p>'
    elif percentage_change < 0:
        change_html = f'<p style="font-size: 14px; color: red; margin-top: -10px;">▼ {views_diff} ({abs(percentage_change):.2f}%) from last week</p>'
    else:
        change_html = '<p style="font-size: 14px; color: gray; margin-top: -10px;">No change from yesterday</p>'

    with col5:
        st.markdown(f'''
            <div class="metric-box">
                <div class="title">Eventbrite Page Views</div>
                <div class="number" style="color: #20D6D3;">{eventbrite_views:,}</div>
                {change_html}  <!-- Inject percentage change here -->
            </div>
        ''', unsafe_allow_html=True)
    st.divider()

    # Load attendee data
    df_state = pd.read_csv(order_data)

    # Manually create a state/province latitude & longitude dataset for US states
    state_latlon = {
        "AL": (32.806671, -86.791130), "AK": (61.370716, -152.404419), "AZ": (33.729759, -111.431221),
        "AR": (34.746613, -92.288986), "CA": (36.778259, -119.417931), "CO": (39.550051, -105.782067),
        "CT": (41.603221, -73.087749), "DE": (38.910832, -75.527670), "FL": (27.994402, -81.760254),
        "GA": (32.157435, -82.907123), "HI": (20.796179, -156.331925), "ID": (44.068202, -114.742043),
        "IL": (40.633125, -89.398529), "IN": (40.551217, -85.602364), "IA": (41.878003, -93.097702),
        "KS": (39.011902, -98.484246), "KY": (37.839333, -84.270018), "LA": (30.984298, -91.962333),
        "ME": (45.253783, -69.445469), "MD": (39.045753, -76.641273), "MA": (42.407211, -71.382439),
        "MI": (44.314844, -85.602364), "MN": (46.729553, -94.685900), "MS": (32.354668, -89.398528),
        "MO": (37.964253, -91.831833), "MT": (46.879682, -110.362566), "NE": (41.492537, -99.901813),
        "NV": (38.802610, -116.419389), "NH": (43.193852, -71.572395), "NJ": (40.058324, -74.405661),
        "NM": (34.972730, -105.032363), "NY": (40.712776, -74.005974), "NC": (35.759573, -79.019300),
        "ND": (47.551493, -101.002012), "OH": (40.417287, -82.907123), "OK": (35.007752, -97.092877),
        "OR": (43.804133, -120.554201), "PA": (41.203323, -77.194525), "RI": (41.580095, -71.477429),
        "SC": (33.836081, -81.163725), "SD": (43.969515, -99.901813), "TN": (35.517491, -86.580447),
        "TX": (31.968599, -99.901813), "UT": (39.320980, -111.093731), "VT": (44.558803, -72.577841),
        "VA": (37.431573, -78.656894), "WA": (47.751076, -120.740135), "WV": (38.597626, -80.454903),
        "WI": (44.784439, -88.787868), "WY": (43.075968, -107.290283)
    }

    # non-US locations (Not needed)
    non_us_latlon = {
        "KR-41": (37.5665, 126.9780), "NI-MS": (12.1364, -86.2514), "TT-TUP": (10.6918, -61.2225),
        "BB-08": (13.1939, -59.5432), "AU-NSW": (-33.8688, 151.2093), "CA-ON": (43.651070, -79.347015),
        "CA-QC": (45.5017, -73.5673), "CH-ZH": (47.3769, 8.5417), "MX-ROO": (20.6296, -87.0739),
        "NL-ZH": (52.0705, 4.3007), "TT-CHA": (10.5162, -61.4119), "TT-POS": (10.6600, -61.5085),
        "ZW-HA": (-17.8292, 31.0522), "ZA-WC": (-33.9249, 18.4241), "ZA-EC": (-32.2968, 26.4194),
        "GB-LBH": (51.4746, -0.3620), "GB-MAN": (53.483959, -2.244644), "VI-T": (18.3358, -64.8963)
    }

    # if i want to Merge both datasets
    #all_latlon = {**state_latlon, **non_us_latlon}

    # Convert dictionary to DataFrame
    latlon_df = pd.DataFrame(state_latlon.items(), columns=["StateCode", "Coordinates"])
    latlon_df[["Lat", "Lon"]] = pd.DataFrame(latlon_df["Coordinates"].tolist(), index=latlon_df.index)
    latlon_df = latlon_df.drop(columns=["Coordinates"])

    # Extract country & state code from dataset (assuming "US-NY" format in your file)
    df_state["Country"] = df_state["Name"].str.split("-").str[0]
    df_state["StateCode"] = df_state["Name"].str.split("-").str[1]

    # Remove rows where Attendees is NaN
    df_state = df_state.dropna(subset=["Attendees"])

    # Convert Attendees to integer (if needed)
    df_state["Attendees"] = df_state["Attendees"].astype(int)

    # Merge with lat/lon dataset
    latlon_df = pd.DataFrame(state_latlon.items(), columns=["StateCode", "Coordinates"])
    latlon_df[["Lat", "Lon"]] = pd.DataFrame(latlon_df["Coordinates"].tolist(), index=latlon_df.index)
    latlon_df = latlon_df.drop(columns=["Coordinates"])

    df_map = df_state.merge(latlon_df, on="StateCode", how="left")

    # Remove rows with missing Lat/Lon
    df_map = df_map.dropna(subset=["Lat", "Lon"])

    # ✅ Roll up duplicate states by summing their counts
    df_map = (
        df_map.groupby(["StateCode", "Lat", "Lon"])
        .agg(Count=("Attendees", "sum"))
        .reset_index()
    )

    df_map.set_index("StateCode", inplace=True)  # Set index for faster lookup

    # Integrate state-level student registrations
    for index, row in state_totals.iterrows():
        state = row["StateCode"]
        attendees = row["Total_Attendees"]
        if state in df_map.index:
            df_map.at[state, "Count"] += attendees  # Directly update the count
        else:
            df_map.loc[state] = [None, None, attendees]  # Add new state if missing

    df_map.reset_index(inplace=True)  # Reset index back to normal


    # Create Streamlit UI
    col1, col2 = st.columns(2)  # Left column (map) is twice as wide as right column (chart)
    with col1:
        st.title("Event Registrations by State")

        # Create a Folium *world map
        # world_map = folium.Map(location=[20, 0], zoom_start=2) For Global view

        # Filter to only show US states
        #df_map = df_map[df_map["Country"] == "US"]

        # Create a US-centered Folium map
        world_map = folium.Map(location=[37.8, -90], zoom_start=4)  # ✅ Center on the US

        # Add circle markers for each location
        for _, row in df_map.iterrows():
            folium.CircleMarker(
                location=[row["Lat"], row["Lon"]],
                radius = max(2, row["Count"] ** 0.5),  # ✅ Further reduced size
                color="blue",
                fill=True,
                fill_color="blue",
                fill_opacity=0.5,
                popup=f"{row['StateCode']}: {row['Count']} attendees",
            ).add_to(world_map)

        # Display map in Streamlit

        st_folium(world_map, width=800, height=500)

    with col2:
        st.markdown("<h1 style='text-align: left;'>Top 10 States by Registrations</h1>", unsafe_allow_html=True)
        # Get top 10 states
        top_10_states = df_map.nlargest(10, "Count")
        top_10_states = top_10_states.sort_values(by="Count", ascending=True)
        fig = px.bar(
        top_10_states,
        x="Count",
        y="StateCode",
        orientation="h",
        text="Count",
    )

        # Manually set all bars to blue
        fig.update_traces(marker=dict(color="blue"))

        fig.update_traces(
        hovertemplate="%{y} Registrations: %{x}<extra></extra>"
        
    )

        # Format chart aesthetics
        fig.update_layout(
            xaxis_title="Attendees",
            yaxis_title="State",
            template="plotly_white",
            showlegend=False,  # ✅ Completely remove legend
            margin=dict(l=50, r=50, t=50, b=50),
        )

        # Show chart in Streamlit
        st.plotly_chart(fig, use_container_width=True)
    
    st.divider()
    load_dotenv()
    ujc_social_act = os.getenv("SOCIAL_ACTIVITY")  # This must be a public .csv export URL
    ujcactivity = pd.read_csv(ujc_social_act)

    def split_totals(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Splits the DataFrame into two:
        - One without any 'Total' in the 'Group' column
        - One with only rows that have 'Total' in the 'Group' column
        
        Parameters:
        - df (pd.DataFrame): The original DataFrame
        
        Returns:
        - (non_totals_df, totals_df): Tuple of filtered DataFrames
        """
        totals_df = df[df['Group'].str.contains("Total", case=False, na=False)]
        non_totals_df = df[~df['Group'].str.contains("Total", case=False, na=False)]
        return non_totals_df, totals_df
    
    
    # st.title("Overview of Group Social Activity - Totals")
    
    # st.dataframe(totals_act, use_container_width=True)
    #UNCOMMENT FOR GROUP SOCIAL ACTIVITY
    # non_totals, totals_act = split_totals(ujcactivity)
    # st.markdown("<h1 style='color: #4169E1;'>Overview of Group Social Activity - Totals</h1>", unsafe_allow_html=True)
    # clean_act = totals_act.drop(columns=["Link"]).reset_index(drop=True)
    # clean_act.index = [""] * len(clean_act)  # Set blank index
    # st.dataframe(clean_act, use_container_width=True)
    # st.markdown("<h1 style='color: #DC143C;'>All Group Social Activity - Individual Posts</h1>", unsafe_allow_html=True)
    # st.dataframe(non_totals, use_container_width=True)

with tab2:

    col_r_3, col_r_4 = st.columns([2, 1])
    with col_r_3:
        # temp_ambassador_counts = temp_ambassador_counts.rename(columns={"Ambassador Name": "Response"})
        # merged_ambassadors = pd.concat([filtered_ambassador_counts, temp_ambassador_counts]).groupby("Response", as_index=False)["Count"].sum()
        # merged_ambassadors = merged_ambassadors.sort_values(by="Count",ascending=False) 
        ambassador_totals["Ambassador Point of Contact"] = ambassador_totals["Ambassador Point of Contact"].apply(format_name)

        temp_ambassador_counts = ambassador_totals.rename(columns={
    "Ambassador Point of Contact": "Response",
    "Count": "Agg Number of Registrations",
    "Total_Attendees": "Count"
})
        
        merged_ambassadors = pd.concat([filtered_ambassador_counts, temp_ambassador_counts]).groupby("Response", as_index=False)["Count"].sum()
        merged_ambassadors = merged_ambassadors.sort_values(by="Count",ascending=False) 
        st.markdown("<h1 style='text-align: left;'>Top 5 Ambassadors by Registrations</h1>", unsafe_allow_html=True)
        ## Get top 5 ambassador sources
        top_amb = merged_ambassadors.nlargest(5, "Count")  # ✅ Keep only top 5

        # Create a Plotly bar chart
        fig3 = px.bar(
            top_amb,  # ✅ Use the correct DataFrame
            x="Response",
            y="Count",
            orientation="v",
            text="Count")

        # Manually set all bars to blue
        fig3.update_traces(marker=dict(color="blue"))

        fig3.update_traces(
            hovertemplate="%{x}: %{y} registrations<extra></extra>"     
        )

        # Format chart aesthetics
        fig3.update_layout(
            xaxis_title="Ambassador",
            yaxis_title="Attendees Registered",
            template="plotly_white",
            showlegend=False,  # ✅ Completely remove legend
            margin=dict(l=50, r=50, t=50, b=50),
        )

        # Show chart in Streamlit
        st.plotly_chart(fig3, use_container_width=True)
    with col_r_4:
        merged_ambassadors = merged_ambassadors.reset_index(drop=True)
        merged_ambassadors.index = merged_ambassadors.index + 1
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)
        # filtered_ambassador_counts = filtered_ambassador_counts.replace(r'^\s*$', None, regex=True)
        # filtered_ambassador_counts = filtered_ambassador_counts.dropna(how='all')
        st.dataframe(merged_ambassadors, height=400)

    col_r_1, col_r_2 = st.columns([2, 1])
    with col_r_1:
        st.markdown("<h1 style='text-align: left;'>Top 5 Advisors by Registrations</h1>", unsafe_allow_html=True)

            # Get top 5 ambassador sources
        top_adv = filtered_advisor_counts.nlargest(5, "Count")  # ✅ Keep only top 5

        # Create a Plotly bar chart
        fig2 = px.bar(
            top_adv,  # ✅ Use the correct DataFrame
            x="Response",
            y="Count",
            orientation="v",
            text="Count")

        # Manually set all bars to blue
        fig2.update_traces(marker=dict(color="blue"))
        
        fig2.update_traces(
            hovertemplate="%{x}: %{y} registrations<extra></extra>")

        # Format chart aesthetics
        fig2.update_layout(
            xaxis_title="Advisor",
            yaxis_title="Attendees Registered",
            template="plotly_white",
            showlegend=False,  # ✅ Completely remove legend
            margin=dict(l=50, r=50, t=50, b=50))

        # Show chart in Streamlit
        st.plotly_chart(fig2, use_container_width=True)

    with col_r_2:
        filtered_advisor_counts = filtered_advisor_counts.reset_index(drop=True)
        filtered_advisor_counts.index = filtered_advisor_counts.index + 1
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)
        st.dataframe(filtered_advisor_counts, height=400) 
        

    col_r_5, col_r_6 = st.columns([2, 1])
    with col_r_5:
        st.markdown("<h1 style='text-align: left;'>Top 5 Sources for Registrations</h1>", unsafe_allow_html=True)

        ## Get top 5 ambassador sources
        top_hearing = filtered_hearing_source_counts.nlargest(5, "Count")  # ✅ Keep only top 5

        # Create a Plotly bar chart
        fig4 = px.bar(
            top_hearing,  # ✅ Use the correct DataFrame
            x="Response",
            y="Count",
            orientation="v",
            text="Count",
        )

        # Manually set all bars to blue
        fig4.update_traces(marker=dict(color="blue"),textangle=0)
        fig4.update_traces(
            hovertemplate="%{x}: %{y} registrations<extra></extra>"
            
        )
        
        # Format chart aesthetics
        fig4.update_layout(
            xaxis_title="Source",
            yaxis_title="Attendees Registered",
            template="plotly_white",
            showlegend=False,  # ✅ Completely remove legend
            margin=dict(l=50, r=50, t=50, b=50),
        )

        # Show chart in Streamlit
        st.plotly_chart(fig4, use_container_width=True)
        # Get top 5 ambassador sources

    with col_r_6:
        filtered_hearing_source_counts = filtered_hearing_source_counts.reset_index(drop=True)
        filtered_hearing_source_counts.index = filtered_hearing_source_counts.index + 1
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)
        filtered_hearing_source_counts = filtered_hearing_source_counts.dropna(how='all')
        st.dataframe(filtered_hearing_source_counts, height=400) 
    col7, col8 = st.columns(2)
    
with tab3:
    st.text("The numbers below highlight how many registrants have attended past summits, to better understand returning participant trends and engagement with the summit over time.")

    #Function output reference to variables
    #duplicates_22_23, duplicates_23_25, duplicates_22_23_25, duplicates_22_25
    # df1_res, df2_res, df3_res, df4_res = process_and_calc_returners(data_2022,data_2023,survey_data)
    #Table names 
    # st.write("Example: 2022 & 2023 Repeat Attendees - Represents number of individuals who registered for both 2022 and 2023 summits.")

    # def align_right_table(df):
    #     st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
    #     st.dataframe(df, height=150)
    #     st.markdown("</div>", unsafe_allow_html=True)
    
    #TOTAL REGISTRATIONS 
    # df_2022 = pd.read_csv(data_2022)
    # df_2023 = pd.read_csv(data_2023)
    # registraints_2022 = df_2022['Name'].count()
    # registraints_2023 = df_2023['Name'].count()
    # #total_sales
    # col101, col201, col301 = st.columns(3)

    # with col101:
    #     st.markdown(f'''
    #         <div class="metric-box" style="text-align: center;">
    #             <div class="title" style="font-weight: bold; color: white; font-size: 16px; margin-bottom: 6px;">
    #                 Total 2022 Registrants
    #             </div>
    #             <div class="number" style="color: #FF4B8B; font-size: 40px; font-weight: bold;">
    #                 {registraints_2022:,}
    #             </div>
    #         </div>
    #     ''', unsafe_allow_html=True)

    # with col201:
    #     st.markdown(f'''
    #         <div class="metric-box" style="text-align: center;">
    #             <div class="title" style="font-weight: bold; color: white; font-size: 16px; margin-bottom: 6px;">
    #                 Total 2023 Registrants
    #             </div>
    #             <div class="number" style="color: #F58F29; font-size: 40px; font-weight: bold;">
    #                 {registraints_2023:,}
    #             </div>
    #         </div>
    #     ''', unsafe_allow_html=True)

    # with col301:
    #     st.markdown(f'''
    #         <div class="metric-box" style="text-align: center;">
    #             <div class="title" style="font-weight: bold; color: white; font-size: 16px; margin-bottom: 6px;">
    #                 Total 2025 Registrants
    #             </div>
    #             <div class="number" style="color: #00C6C2; font-size: 40px; font-weight: bold;">
    #                 {total_sales:,}
    #             </div>
    #         </div>
    #     ''', unsafe_allow_html=True)



    col_6, col_7, col_8, col_9 = st.columns(4)

    # Define old and new values
    #int(df1_res,df4_res,df2_res,)
    # Create dictionaries for iteration
    old_values = {'df1': df1_old, 'df4': df4_old, 'df2': df2_old, 'df3': df3_old}
    new_values = {'df1': df1_res, 'df4': df4_res, 'df2': df2_res, 'df3': df3_res}

    # Dictionary to store percent changes
    percent_changes = {}
    differences = []

    # Calculate percent change iteratively
    for key in old_values:
        old = old_values[key]
        new = new_values[key]

        difference = new - old
        differences.append(difference)
        
        # Avoid division by zero
        if new == old:
            change = 0.0
        elif old != 0:
            change = ((new - old) / old) * 100
        else:
            change = None  # If old value is 0, percent change is undefined

        percent_changes[f"{key}_change"] = change
         

    # Assign values to individual variables
    df1_change, df4_change, df2_change, df3_change = (
        percent_changes["df1_change"],
        percent_changes["df4_change"],
        percent_changes["df2_change"],
        percent_changes["df3_change"]
    )
    with col_6:
        # Determine color and symbol for percentage change
        if df1_change > 0:
            change_html1 = f'<p style="font-size: 14px; color: green; margin-top: -10px;">▲ {differences[0]} ({df1_change:.2f}%) from yesterday</p>'
        elif df1_change < 0:
            change_html1 = f'<p style="font-size: 14px; color: red; margin-top: -10px;">▼ {differences[0]} ({abs(df1_change):.2f}%) from yesterday</p>'
        else:
            change_html1 = f'<p style="font-size: 14px; color: gray; margin-top: -10px;">{differences[0]}, No change from yesterday</p>'
        
        st.markdown(f'''
            <div class="metric-box">
                <div class="title">2022 & 2023 Repeat Registrants</div>
                <div class="number pink";">{df1_res:,}</div>
                {change_html1}  <!-- Inject percentage change here -->
            </div>
        ''', unsafe_allow_html=True)

            #st.markdown(f'<div class="metric-box"><div class="title">2022 & 2023 Repeat Attendees</div><div class="number pink">{(df1_change):,}</div></div>', unsafe_allow_html=True)
            # df1_res = df1_res.sort_values(by="Name") 
            # st.table(df1_res["Name"])
            #align_right_table(df1_res)  # Shift table position



    with col_7:
        if df4_change > 0:
            change_html2 = f'<p style="font-size: 14px; color: green; margin-top: -10px;">▲ {differences[1]} ({df4_change:.2f}%) from yesterday</p>'
        elif df4_change < 0:
            change_html2 = f'<p style="font-size: 14px; color: red; margin-top: -10px;">▼ {differences[1]} ({abs(df4_change):.2f}%) from yesterday</p>'
        else:
            change_html2 = f'<p style="font-size: 14px; color: gray; margin-top: -10px;">{differences[1]}, No change from yesterday</p>'
        
        st.markdown(f'''
            <div class="metric-box">
                <div class="title">2022 & 2025 Repeat Registrants</div>
                <div class="number" style="color: #FEC110;">{df4_res:,}</div>
                {change_html2}  <!-- Inject percentage change here -->
            </div>
        ''', unsafe_allow_html=True)

    with col_8:
        if df2_change > 0:
            change_html3 = f'<p style="font-size: 14px; color: green; margin-top: -10px;">▲ {differences[2]} ({df2_change:.2f}%) from yesterday</p>'
        elif df2_change < 0:
            change_html3 = f'<p style="font-size: 14px; color: red; margin-top: -10px;">▼ {differences[2]} ({abs(df2_change):.2f}%) from yesterday</p>'
        else:
            change_html3 = f'<p style="font-size: 14px; color: gray; margin-top: -10px;">{differences[2]}, No change from yesterday</p>'
        
        st.markdown(f'''
            <div class="metric-box">
                <div class="title">2023 & 2025 Repeat Registrants </div>
                <div class="number orange">{df2_res:,}</div>
                {change_html3}  <!-- Inject percentage change here -->
            </div>
        ''', unsafe_allow_html=True)

    with col_9:
        if df3_change > 0:
            change_html4 = f'<p style="font-size: 14px; color: green; margin-top: -10px;">▲ {differences[3]} ({df3_change:.2f}%) from yesterday</p>'
        elif df3_change < 0:
            change_html4 = f'<p style="font-size: 14px; color: red; margin-top: -10px;">▼ {differences[3]} ({abs(df3_change):.2f}%) from yesterday</p>'
        else:
            change_html4 = f'<p style="font-size: 14px; color: gray; margin-top: -10px;">{differences[3]}, No change from yesterday</p>'
        
        st.markdown(f'''
            <div class="metric-box">
                <div class="title">All 3 Summit Repeat Registrants</div>
                <div class="number" style="color: #20D6D3;">{df3_res:,}</div>
                {change_html4}  <!-- Inject percentage change here -->
            </div>
        ''', unsafe_allow_html=True)

# # Repeat registration matrix including 3-year repeats
#     repeat_data = {
#         "2022": [None, 690, None, None],
#         "2023": [None, None, None, None],
#         "2025": [265, 943, None, None],
#         "All 3 Years": [None, None, None, 194]
#     }
#     repeat_df = pd.DataFrame(repeat_data, index=["2022", "2023", "2025", "All 3 Years"])
#     repeat_df.index.name = "From Year"
#     formatted_df = repeat_df.applymap(lambda x: int(x) if pd.notnull(x) else "-")
#     st.dataframe(formatted_df, use_container_width=True)

    # TABLE VIEW FOR REPEAT REGISTRATIONS
    # repeat_data = {
    #     "2022": [None, 690.0, None, None],
    #     "2023": [None, None, None, None],
    #     "2025": [265.0, 943.0, None, None],
    #     "All 3 Years": [None, None, None, 194.0]
    # }

    # repeat_df = pd.DataFrame(repeat_data, index=["2022", "2023", "2025", "All 3 Years"])
    # repeat_df.index.name = "From Year"

    # # Format numbers and blanks
    # formatted_df = repeat_df.applymap(lambda x: int(x) if pd.notnull(x) else " ")

    # # Define styling function
    # def highlight_dash(val):
    #     if val == " ":
    #         return "background-color: #3a3a3a; color: white"
    #     return ""

    # # Apply styling
    # styled_df = formatted_df.style.applymap(highlight_dash)

    # # Display styled dataframe
    # st.dataframe(styled_df, use_container_width=True)
    st.divider()
    #VENN DIAGRAM
    # import streamlit as st
    # from matplotlib_venn import venn3
    # import matplotlib.pyplot as plt


    # # Define your values
    # # Format: (A only, B only, A&B only, C only, A&C only, B&C only, A&B&C)
    # #2022 total registrations, 2023 total registrants, 22+23 reg, 2025 registrations, 22+25 reg, 23+25 reg, all 3)
    # #row_count = df['Name'].count()
   
    # df_2022 = pd.read_csv(data_2022)
    # df_2023 = pd.read_csv(data_2023)
    # registraints_2022 = df_2022['Name'].count()
    # registraints_2023 = df_2023['Name'].count()
    # values = (registraints_2022, registraints_2023, 690, total_sales, df4_res, df2_res, df3_res)

    # labels = ('2022', '2023', '2025')
    # # Plotting
    # fig11, ax11 = plt.subplots(figsize=(4, 4))
    # # Set transparent background
    # fig11.patch.set_alpha(0)  # entire figure background
    # ax11.patch.set_alpha(0)   # axes background
    # venn = venn3(subsets=values, set_labels=labels, ax=ax11)
    # ax11.set_title("Total Registration and Repeat Registration Venn Diagram", color='white', fontsize=12)
    # for text in venn.set_labels:
    #     if text:  # sometimes None if a set has no label
    #         text.set_color("white")
    # for text in venn.subset_labels:
    #     if text:
    #         text.set_color("white")
    # st.pyplot(fig11)
    # col111, col222, col333 = st.columns([1, 2, 1])  # center the chart in column 2
    # with col2:
    #     st.pyplot(fig11)

with tab4:
    # st.write("[Work In Progress]")
    # df_domo = pd.DataFrame(data_domo)
    # st.dataframe(df_domo)
    
    st.header("Registration Campaign Overview")

    # Comparing to 9/25/2023 through 11/2/2023
    num_2023_registrations = 1557
    acpc_2023 = 14.27
    acpc_2022 = 25
    # acpc_2023_2025_diff = 
    impress_2023 = 982089
    spend_2023 = 22473.13
    clicks_2023 = 16734

    #target_ad_registrations = 
    # Calculate percentage change
    change_html_2023 = f'<p style="font-size: 14px; color: red; margin-top: -10px;">2023 Avg. Cost Per Lead: ${acpc_2023}</p>'
    change_html_impresss = f'<p style="font-size: 14px; color: red; margin-top: -10px;">2023 Impressions: {impress_2023:,}</p>'
    change_html_spend = f'<p style="font-size: 14px; color: red; margin-top: -10px;">2023 Spend: ${spend_2023:,}</p>'
    change_html_clicks = f'<p style="font-size: 14px; color: red; margin-top: -10px;">2023 Clicks: {clicks_2023:,}</p>'
    change_html_regist = f'<p style="font-size: 14px; color: red; margin-top: -10px;">2023 Ad Registrations: {num_2023_registrations:,}</p>'


    # Display the metrics
    col11, col12, col13, col14, col15 = st.columns(5)
    # col14, col15, col16 = st.columns(3)
    with col11:
        # st.markdown(f'<div class="metric-box"><div class="title">Total Amount Spent</div><div class="number white">${amount_spent:,.2f}</div></div>', unsafe_allow_html=True)
        st.markdown(f'''
            <div class="metric-box">
                <div class="title">Amount Spent</div>
                <div class="number white" style="font-size: 34px;">${amount_spent:,.0f}</div>
                {change_html_spend}  <!-- Inject percentage change here -->
            </div>
        ''', unsafe_allow_html=True)
    # with col3:
    #     st.markdown(f'<div class="metric-box"><div class="title">Total Ambassador Registrations</div><div class="number orange">{num_amb_registered:,}</div></div>', unsafe_allow_html=True)

    # with col11:
    #     st.metric("Total Amount Spent", f"${amount_spent:,.2f}")

    with col12:
        # st.metric("Total Impressions", f"{impressions:,}")
        # st.markdown(f'<div class="metric-box"><div class="title">Total Impressions</div><div class="number green">{impressions:,}</div></div>', unsafe_allow_html=True)
        st.markdown(f'''
            <div class="metric-box">
                <div class="title">Impressions</div>
                <div class="number white" style="font-size: 34px;">{impressions:,}</div>
                {change_html_impresss}  <!-- Inject percentage change here -->
            </div>
        ''', unsafe_allow_html=True)
    with col13:
        # st.metric("Total Impressions", f"{impressions:,}")
        # st.markdown(f'<div class="metric-box"><div class="title">Total Clicks</div><div class="number green">{clicks:,}</div></div>', unsafe_allow_html=True)
        st.markdown(f'''
            <div class="metric-box">
                <div class="title">Clicks</div>
                <div class="number white" style="font-size: 34px;">{clicks:,}</div>
                {change_html_clicks}  <!-- Inject percentage change here -->
            </div>
        ''', unsafe_allow_html=True)

    with col14:
        # st.metric("Total Leads", f"{leads:,}")
        # st.markdown(f'<div class="metric-box"><div class="title">Total Registrations</div><div class="number white">{leads:,}</div></div>', unsafe_allow_html=True)
        st.markdown(f'''
            <div class="metric-box">
                <div class="title">Registrations</div>
                <div class="number white" style="font-size: 34px;">{leads:,}</div>
                {change_html_regist}  <!-- Inject percentage change here -->
            </div>
        ''', unsafe_allow_html=True)

    with col15:
        filtered_df = df_domo2[~df_domo2['Platform'].isin(['Facebook', 'Instagram'])]
        filtered_df['Cost Per Lead'] = filtered_df['Cost Per Lead'].str.replace('$', '', regex=False)  # remove all dollar signs
        filtered_df['Cost Per Lead'] = filtered_df['Cost Per Lead'].str.replace(',', '')               # remove commas
        filtered_df['Cost Per Lead'] = filtered_df['Cost Per Lead'].str.extract('(\d+\.?\d*)')          # extract the first valid number from each string
        filtered_df['Cost Per Lead'] = pd.to_numeric(filtered_df['Cost Per Lead'], errors='coerce') 
        # Calculate the average cost
        average_cost = filtered_df['Cost Per Lead'].mean()



        # st.metric("Average Cost Per Click", f"${cpc:.2f}")
        # st.markdown(f'<div class="metric-box"><div class="title">Average Cost Per Click</div><div class="number red">${cpc:.2f}</div></div>', unsafe_allow_html=True)
        st.markdown(f'''
            <div class="metric-box">
                <div class="title">Avg. Cost Per Lead*</div>
                <div class="number white" style="font-size: 34px;">${average_cost:,.2f}</div> 
                {change_html_2023}  <!-- Inject percentage change here -->
            </div>
        ''', unsafe_allow_html=True) #cpl instead of 8.83

    df_domo['Platform'] = df_domo['Platform'].replace({
    'Facebook': 'Facebook (Awareness Focused)',
    'Instagram': 'Instagram (Awareness Focused)'
})
    df_domo.set_index("Platform", inplace=True)
    # copy_df = 
    # st.dataframe(df_domo)

    def render_html_table(df):
        # Convert all cells to strings so no inline styles are added
        df_str = df.astype(str).reset_index()

        html = """
        <style>
            table {
                color: white;
                background-color: #1e1e1e;
                border-collapse: collapse;
                width: 100%;
                font-size: 26px;
            }
            th {
                background-color: #333;
                text-align: center;
                padding: 10px;
            }
            td {
                padding: 10px;
                text-align: center;
            }
        </style>
        """
        #html += df_str.to_html(index=False, escape=False, border=0)
        html += f'<div style="display: flex; justify-content: center;">{df_str.to_html(index=False, escape=False, border=0)}</div>'
        return html


    subset_cols = [
    "Amount Spent",
    "Impressions",
    "Clicks",
    "CPC (Cost Per Click)",
    "Leads",
    "Cost Per Lead"]

    df_domo_subset = df_domo[subset_cols]
    df_domo_subset["Cost Per Lead"] = df_domo_subset["Cost Per Lead"].apply(
    lambda x: f"${float(x):,.2f}" if pd.notnull(x) and isinstance(x, (int, float)) else x)

    df_domo_subset["Amount Spent"] = df_domo_subset["Amount Spent"].apply(
        lambda x: f"${float(x):,.2f}" if pd.notnull(x) and isinstance(x, (int, float)) else x)

    #st.markdown(render_html_table(df_domo_subset), unsafe_allow_html=True)
    #st.dataframe(df_domo_subset, use_container_width=True)
    df_domo_subset = df_domo_subset[df_domo_subset.index != "Total"]
    df_sorted = df_domo_subset.sort_values(by="Leads", ascending=False)
    df_top8 = df_sorted.head(12)
    st.dataframe(df_top8, use_container_width=True, height=420)
    st.text("*Avg. Cost Per Lead measures campaigns/platforms solely focused on registrations, not awareness.")

