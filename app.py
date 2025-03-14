import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime
import folium
from streamlit_folium import st_folium
import os
import matplotlib.pyplot as plt
# from st_aggrid import AgGrid, GridOptionsBuilder
# from st_aggrid.shared import GridUpdateMode
from dotenv import load_dotenv

# Set page config
st.set_page_config(page_title="UJC Summit Registration Tracker Dashboard", layout="wide")

load_dotenv()
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

tabs = ["Event Tracker", "Registration Leaderboard", "Repeat Attendees"] #Paid Promotion Performance
tab1, tab2, tab3 = st.tabs(tabs)

# Sidebar instructions
instructions = {
    "Event Tracker": "Track event registrations by date, location, and repeat attendees across previous summits.",
    "Registration Leaderboard": "View the top contributors and sources driving the most registrations.",
    "Repeat Attendees": "View the count and names of individuals who registered for previous summits."
    #"Paid Promotion Performance": "Analyze the impact of paid advertisements."
}
st.sidebar.header("UJC Summit 2025 Tracker")
st.sidebar.markdown("### Updated 12pm daily.")

st.sidebar.markdown("### Overview:")
for tab, instruction in instructions.items():
    st.sidebar.markdown(f"**<u>{tab}</u>:** {instruction}", unsafe_allow_html=True)

st.sidebar.markdown("#### Collapse sidebar for a full-screen view.")

#Data File References - Manually change this everyday by ~~

# Custom responses to survey questions + open ended
survey_data = ("Data/report-2025-03-14T1514.csv")
# Just the summary (orders, attendees, Name aka location)
order_data = ("Data/Eventbrite Attendees Table - 2025-3-14.csv")

# DO NOT CHANGE THESE REFERENCES
data_2022 = ("Data/Perm/Summit Data Stuff - 2022 Raw.csv")
data_2023 = ("Data/Perm/Summit Data Stuff - 2023Raw.csv")

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
    total_sales = sum(ticket_sales)
    total_budget = 7000
    progress = (total_sales / total_budget) * 100

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
        st.progress(progress / 100)
    with col2:
        st.metric("Registration Goal", f"{total_budget:,.0f}")
        st.text(f"Progress: {progress:.2f}% achieved")

    # Ensure "Order Date" is in datetime format
    df_survey["Order Date"] = pd.to_datetime(df_survey["Order Date"], utc=True)
    df_survey["Order Date"] = df_survey["Order Date"].dt.tz_localize(None)  # Remove timezone info

    # Extract only the date part (drop time)
    df_survey["Order Date"] = df_survey["Order Date"].dt.date

    # Count occurrences of each unique date
    date_counts = df_survey["Order Date"].value_counts().reset_index()
    date_counts.columns = ["Order Date", "Count"]
    date_counts = date_counts.sort_values("Order Date")  # Ensure proper chronological order

    # Create interactive line chart with customized hover text
    fig = px.line(date_counts, x="Order Date", y="Count", markers=True, 
                title="Registrations Over Time (Daily)",
                labels={"Order Date": "Date", "Count": "Total Registrations"},
                template="plotly_white")

    # Customize the hover text
    fig.update_traces(
        hovertemplate="Registrations: %{y}<extra></extra>",
        mode="lines+markers"
    )

    fig.update_layout(
        xaxis_tickangle=-45,
        hovermode="x unified"
    )
    st.plotly_chart(fig, use_container_width=True)

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
    num_amb_registered = filtered_ambassador_counts["Count"].sum()

    # ADVISOR INVITE COUNT 
    num_adv_registered = filtered_advisor_counts["Count"].sum()
    # EVENTBRITE VIEW COUNT (MANUAL)
    eventbrite_views = 4230

    # PREVIOUS ATTENDEE COUNT
    include_words = [
    "attended", "previous", "past", "last year", "2024", "inauguration", "inaugural", 
    "1st", "first", "2023", "2022", "December 2023", "Dec 2023", "participated", "participate"]
    
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
    filtered_prev_attendees = df_survey[df_survey["If you answered \"Other\" to the. previous question -"].apply(should_include)]
    prev_attendee_response = len(filtered_prev_attendees)
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
        st.markdown(f'<div class="metric-box"><div class="title">Students Registered</div><div class="number pink">{students_registered:,}</div></div>', unsafe_allow_html=True)

    with col3:
        st.markdown(f'<div class="metric-box"><div class="title">Total Ambassador Registrations</div><div class="number orange">{num_amb_registered:,}</div></div>', unsafe_allow_html=True)

    with col4:
        st.markdown(f'<div class="metric-box"><div class="title">Total Advisor Registrations</div><div class="number" style="color: #FEC110;">{num_adv_registered:,}</div></div>', unsafe_allow_html=True)

    with col5:
        st.markdown(f'<div class="metric-box"><div class="title">Eventbrite Page Views</div><div class="number" style="color: #20D6D3;">{eventbrite_views:,}</div></div>', unsafe_allow_html=True)
        
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

with tab2:
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
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)
        st.dataframe(filtered_advisor_counts, height=400) 

    col_r_3, col_r_4 = st.columns([2, 1])
    with col_r_3:

        st.markdown("<h1 style='text-align: left;'>Top 5 Ambassadors by Registrations</h1>", unsafe_allow_html=True)
        ## Get top 5 ambassador sources
        top_amb = filtered_ambassador_counts.nlargest(5, "Count")  # ✅ Keep only top 5

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
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)
        filtered_ambassador_counts = filtered_ambassador_counts.replace(r'^\s*$', None, regex=True)
        filtered_ambassador_counts = filtered_ambassador_counts.dropna(how='all')
        st.dataframe(filtered_ambassador_counts, height=400)

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
        st.markdown("<br><br><br><br>", unsafe_allow_html=True)
        filtered_hearing_source_counts = filtered_hearing_source_counts.dropna(how='all')
        st.dataframe(filtered_hearing_source_counts, height=400) 
    col7, col8 = st.columns(2)


    # with col7:
    #     # Create AgGrid options
    #     gb = GridOptionsBuilder.from_dataframe(filtered_ambassador_counts)
    #     gb.configure_pagination(enabled=True)  # ✅ Add pagination
    #     gb.configure_side_bar()  # ✅ Enable side panel for filtering
    #     gb.configure_selection(selection_mode="single")  # ✅ Allow row selection
    #     gb.configure_grid_options(domLayout='autoHeight')  # ✅ Adjust height automatically

    #     # Convert options to GridOptions
    #     grid_options = gb.build()

    #     # 🎯 Replace Plotly chart with AgGrid table
    #     st.subheader("Ambassadors by Registrations")

    #     AgGrid(
    #         filtered_ambassador_counts,
    #         gridOptions=grid_options,
    #         enable_enterprise_modules=True,  # ✅ Enables advanced features
    #         update_mode=GridUpdateMode.SELECTION_CHANGED,
    #         fit_columns_on_grid_load=True,  # ✅ Auto-adjust columns
    #         theme="balham",  # ✅ Set grid theme
    #         )
    # with col8:
    #     gb2 = GridOptionsBuilder.from_dataframe(filtered_advisor_counts)
    #     gb2.configure_pagination(enabled=True)  # ✅ Add pagination
    #     gb2.configure_side_bar()  # ✅ Enable side panel for filtering
    #     gb2.configure_selection(selection_mode="single")  # ✅ Allow row selection
    #     gb2.configure_grid_options(domLayout='autoHeight')  # ✅ Adjust height automatically

    #     # Convert options to GridOptions
    #     grid_options = gb2.build()

    #     # 🎯 Replace Plotly chart with AgGrid table
    #     st.subheader("Advisors by Registrations")

    #     AgGrid(
    #         filtered_advisor_counts,
    #         gridOptions=grid_options,
    #         enable_enterprise_modules=True,  # ✅ Enables advanced features
    #         update_mode=GridUpdateMode.SELECTION_CHANGED,
    #         fit_columns_on_grid_load=True,  # ✅ Auto-adjust columns
    #         theme="balham",  # ✅ Set grid theme
    #         )
    
with tab3:
    #Function output reference to variables
    #duplicates_22_23, duplicates_23_25, duplicates_22_23_25, duplicates_22_25
    df1_res, df2_res, df3_res, df4_res = process_and_calc_returners(data_2022,data_2023,survey_data)
    st.write("Example: 2022 & 2023 Repeat Attendees - Represents number of individuals who registered both 2022 and 2023 summits")

    def align_right_table(df):
        st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
        st.dataframe(df, height=150)
        st.markdown("</div>", unsafe_allow_html=True)

    col_6, col_7, col_8, col_9 = st.columns(4)

    with col_6:
        st.markdown(f'<div class="metric-box"><div class="title">2022 & 2023 Repeat Attendees</div><div class="number pink">{len(df1_res):,}</div></div>', unsafe_allow_html=True)
        df1_res = df1_res.sort_values(by="Name") 
        st.table(df1_res["Name"])
        #align_right_table(df1_res)  # Shift table position


    with col_7:
        st.markdown(f'<div class="metric-box"><div class="title"/?>2022 & 2025 Repeat Attendees</div><div class="number" style="color: #FEC110;">{len(df4_res):,}</div></div>', unsafe_allow_html=True)
        #st.text("*Number of individuals who registered in 2022 and 2025(still in progress)")
        df4_res = df4_res.sort_values(by="Name") 
        st.table(df4_res["Name"]) 
        #align_right_table(df4_res)  # Shift table position

    with col_8:
        st.markdown(f'<div class="metric-box"><div class="title">2023 & 2025 Repeat Attendees</div><div class="number orange">{len(df2_res):,}</div></div>', unsafe_allow_html=True)
        #st.write("*Number of individuals who registered in 2023 and 2025(still in progress)")

        df2_res = df2_res.sort_values(by="Name") 
        st.table(df2_res["Name"]) 
        #align_right_table(df2_res)  # Shift table position

    with col_9:
        st.markdown(f'<div class="metric-box"><div class="title">All 3 Summit Repeat Attendees</div><div class="number" style="color: #20D6D3;">{len(df3_res):,}</div></div>', unsafe_allow_html=True)
        #st.write("*Number of individuals who registered for all 3 summits(still in progress)")

        df3_res = df3_res.sort_values(by="Name") 
        st.table(df3_res["Name"]) 
        #align_right_table(df3_res["Name"])  # Shift table position


    # col_10, col_11, col_12, col_13 = st.columns(4)
    # with col_10:
    #         st.dataframe(df1_res["Name"], height=400) 
    # with col_11:
    #     st.dataframe(df4_res["Name"], height=400) 
    # with col_12:
    #     st.dataframe(df2_res["Name"], height=400) 
    # with col_13:
    #     st.dataframe(df3_res["Name"], height=400) 
    # Custom Static Data (Manually Updated)
#     ad_list = [
#     ["UJC Website", "$0.00", "3,009", "326", "10.4%", "$0.00"],
#     ["Google (Performance Max)", "$842.65", "85,289", "8,500", "17", "$49.57"],
#     ["Google (Search Standard)", "$460.22", "313", "14", "2", "$230.11"],
#     ["Facebook", "$12,080.02", "509,997", "5,635", "815", "$14.82"],
#     ["Instagram", "$8,730.96", "364,022", "2,468", "723", "$12.08"],
#     ["LinkedIn", "$282.72", "10,261", "73", "0", "$0.00"],
#     ["TikTok", "$79.79", "11,795", "38", "0", "$0.00"],
#     ["Total", "$22,473.13", "982,089", "16,734", "1,557", "$14.27"]]
    
#     columns = ["Platform", "Spend", "Impressions", "Link Clicks", "Conversion Rate(%)", "Cost Per Action (CPA)"]
#     df_ad = pd.DataFrame(ad_list, columns= columns)

#     # Title and Header Styling
#     st.markdown("<h1 style='text-align: center; color: white;'>Total Registrations from Ads</h1>", unsafe_allow_html=True)

#     col_1, col_2 = st.columns(2)

#     with col_1:
#         st.markdown("<h2 style='color: orange; font-size: 60px; text-align: center;'>1,557</h2>", unsafe_allow_html=True)
#         st.markdown("<h4 style='text-align: center; color: white;'>Total Registrations</h4>", unsafe_allow_html=True)

#     with col_2:
#         st.markdown("<h2 style='color: pink; font-size: 60px; text-align: center;'>$14.27</h2>", unsafe_allow_html=True)
#         st.markdown("<h4 style='text-align: center; color: white;'>Average Cost-Per-Action (Registration)</h4>", unsafe_allow_html=True)

#     # Table Display
#     st.markdown("<h3 style='color: white;'>Advertising Performance Overview</h3>", unsafe_allow_html=True)
#     st.dataframe(df_ad.style.set_properties(**{'background-color': 'black', 'color': 'white', 'border-color': 'white'}))

#     # CPA Comparison
#     st.markdown("<h4 style='color: lightgreen; text-align: center;'>$10.73 LESS than 2022’s average CPA of $25.</h4>", unsafe_allow_html=True)


#     # MANUALLY UPDATE FROM HERE
#     linkfire_data = {
#     "Date": [
#         "2025-03-12T00:00:00.000Z", "2025-03-11T00:00:00.000Z", "2025-03-10T00:00:00.000Z",
#         "2025-03-09T00:00:00.000Z", "2025-03-08T00:00:00.000Z", "2025-03-07T00:00:00.000Z",
#         "2025-03-06T00:00:00.000Z", "2025-03-05T00:00:00.000Z", "2025-03-04T00:00:00.000Z",
#         "2025-03-03T00:00:00.000Z", "2025-03-02T00:00:00.000Z", "2025-03-01T00:00:00.000Z",
#         "2025-02-28T00:00:00.000Z", "2025-02-27T00:00:00.000Z", "2025-02-26T00:00:00.000Z",
#         "2025-02-25T00:00:00.000Z"
#     ],
#     "Visits": [11, 5, 17, 11, 24, 61, 8, 19, 80, 52, 13, 13, 68, 48, 124, 263]
# }
#     df_lf = pd.DataFrame(linkfire_data)

#     # Ensure "Order Date" is in datetime format
#     df_lf["Date"] = pd.to_datetime(df_lf["Date"], utc=True)
#     df_lf["Date"] = df_lf["Date"].dt.tz_localize(None)  # Remove timezone info

#     # Extract only the date part (drop time)
#     df_lf["Date"] = df_lf["Date"].dt.date

#     fig5 = px.line(df_lf, x="Date", y="Visits", markers=True, 
#                 title="Linkfire Clicks (Daily)",
#                 labels={"Date": "Date", "Visits": "Total Clicks"},
#                 template="plotly_white")

#     # Customize the hover text
#     fig5.update_traces(
#         hovertemplate="Clicks: %{y}<extra></extra>",
#         mode="lines+markers"
#     )


#     fig5.update_layout(
#         xaxis_tickangle=-45,
#         hovermode="x unified"
#     )

#     # Display the chart in Streamlit
#     st.plotly_chart(fig5, use_container_width=True)