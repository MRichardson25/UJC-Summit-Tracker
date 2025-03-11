import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

# test
st.set_page_config(page_title="UJC Summit Registration Tracker Dashboard", layout="wide")

tabs = ["Event Tracker","Registration Leaderboard"]
tab1, tab2 = st.tabs(tabs)

with tab1:
        

    st.image("Data/UJC_Summit_Logo_2023_horizontal-logo-wordmark-3-white.png")

    survey_data = ("Data/report-2025-03-11T1646.csv")
    df_survey = pd.read_csv(survey_data)

    # Set Page Config

    # Generate Fake Data
    np.random.seed(42)
    days = pd.date_range(start="2024-06-01", periods=60, freq="D")
    # Just the summary (orders, attendees, Name aka location)
    ticket_data = pd.read_csv("Data/Eventbrite Attendees Table - 2025-3-11 (1).csv")
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
    event_date = datetime(2025, 5, 30)  # Change to your event date

    # Get today's date
    today = datetime.today()

    # Calculate days remaining
    days_until_event = (event_date - today).days

    # Display the countdown
    st.markdown(f"""
    ### <span style='color: orange; font-weight: bold;'>{days_until_event}</span> days until UJC Summit 2025! 🎉
    """, unsafe_allow_html=True)


    st.title("🎟️ Event Tracker Dashboard")

    # Top Metrics (Like Total Balance and Monthly Budget)
    col1, col2 = st.columns([0.8, 0.2])
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
        # df.fillna("Unknown", inplace=True)
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


    # Define survey inclusion criteria
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
    eventbrite_views = 4230


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

    #analyze_survey_data(survey_data)




    ###

    # import folium
    # from collections import Counter
    # from streamlit_folium import st_folium
    # import streamlit as st

    # # Load pre-downloaded city coordinates dataset
    # city_data = pd.read_csv("Data/worldcities.csv")  # Ensure this CSV file is in your working directory

    # # Load ticket data and extract city names
    # city_list = ticket_data['Name'].tolist()  # Use ticket_data column

    # # Count how many attendees are from each city
    # city_counts = Counter(city_list)

    # # Convert to DataFrame
    # df_counts = pd.DataFrame(city_counts.items(), columns=["City", "Count"])

    # # Merge with city coordinates dataset
    # df_map = df_counts.merge(city_data, left_on="City", right_on="city", how="left")

    # # Identify and store skipped cities (cities without a lat/lon match)
    # skipped_cities = df_map[df_map["lat"].isna()]["City"].tolist()

    # # Remove unmatched cities
    # df_map = df_map.dropna(subset=["lat", "lng"])

    # # Rename columns for clarity
    # df_map = df_map[["City", "lat", "lng", "Count"]].rename(columns={"lat": "Lat", "lng": "Lon"})

    # # ✅ Standardize cities by grouping them and summing up their registrants
    # df_map = (
    #     df_map.groupby("City")
    #     .agg(
    #         Lat=("Lat", "first"),  # Keep the first Lat found
    #         Lon=("Lon", "first"),  # Keep the first Lon found
    #         Count=("Count", "sum")  # Sum up all the attendees per city
    #     )
    #     .reset_index()
    # )

    # # Display standardized table
    # st.table(df_map)

    # # Create Streamlit UI
    # st.title("Event Registrations by City")

    # # Create a Folium map
    # world_map = folium.Map(location=[20, 0], zoom_start=2)

    # # Add circle markers for each city
    # for _, row in df_map.iterrows():
    #     folium.CircleMarker(
    #         location=[row["Lat"], row["Lon"]],
    #         radius=row["Count"] * 2,  # Adjust multiplier for circle size
    #         color="blue",
    #         fill=True,
    #         fill_color="blue",
    #         fill_opacity=0.5,
    #         popup=f"{row['City']}: {row['Count']} attendees",
    #     ).add_to(world_map)

    # # Display map in Streamlit
    # st_folium(world_map, width=800, height=500)

    # # Display skipped cities in Streamlit
    # if skipped_cities:
    #     st.subheader("Cities Not Found in Dataset")
    #     st.write(", ".join(skipped_cities))  # Display the list as a comma-separated string

    import folium
    from streamlit_folium import st_folium
    import streamlit as st
    import os
    import matplotlib.pyplot as plt

    # Load attendee data
    df_state = pd.read_csv("Data/States/Eventbrite Attendees Table - 2025-3-11.csv")

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

    # Add non-US locations
    non_us_latlon = {
        "KR-41": (37.5665, 126.9780), "NI-MS": (12.1364, -86.2514), "TT-TUP": (10.6918, -61.2225),
        "BB-08": (13.1939, -59.5432), "AU-NSW": (-33.8688, 151.2093), "CA-ON": (43.651070, -79.347015),
        "CA-QC": (45.5017, -73.5673), "CH-ZH": (47.3769, 8.5417), "MX-ROO": (20.6296, -87.0739),
        "NL-ZH": (52.0705, 4.3007), "TT-CHA": (10.5162, -61.4119), "TT-POS": (10.6600, -61.5085),
        "ZW-HA": (-17.8292, 31.0522), "ZA-WC": (-33.9249, 18.4241), "ZA-EC": (-32.2968, 26.4194),
        "GB-LBH": (51.4746, -0.3620), "GB-MAN": (53.483959, -2.244644), "VI-T": (18.3358, -64.8963)
    }

    # Merge both datasets
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
        st.title("Event Registrations by Location")

        # Create a Folium world map
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

        # Format chart aesthetics
        fig.update_layout(
            xaxis_title="Attendees",
            yaxis_title="State",
            template="plotly_white",
            showlegend=False,  # ✅ Completely remove legend
            margin=dict(l=50, r=50, t=50, b=50),
        )

        # Ensure text inside bars is displayed correctly

        # Show chart in Streamlit
        st.plotly_chart(fig, use_container_width=True)

with tab2:
        
    ambassador_counts, advisor_counts, hearing_source_counts = analyze_survey_data(survey_data)

    # Hide "No" and NaN responses before displaying
    filtered_advisor_counts = advisor_counts[(advisor_counts["Response"] != "No") & (advisor_counts["Response"] != "nan")]
    filtered_ambassador_counts = ambassador_counts[(ambassador_counts["Response"] != "No") & (ambassador_counts["Response"] != "nan")]
    filtered_hearing_source_counts = hearing_source_counts[(hearing_source_counts["Response"] != "No") & (hearing_source_counts["Response"] != "nan") & (hearing_source_counts["Response"] != "Other (Please describe in next question)")]

    st.markdown("<h1 style='text-align: left;'>Top 5 Advisors by Registrations</h1>", unsafe_allow_html=True)

    # Get top 5 ambassador sources
    top_adv = filtered_advisor_counts.nlargest(5, "Count")  # ✅ Keep only top 5

    # Create a Plotly bar chart
    fig2 = px.bar(
        top_adv,  # ✅ Use the correct DataFrame
        x="Response",
        y="Count",
        orientation="v",
        text="Count",
    )

    # Manually set all bars to blue
    fig2.update_traces(marker=dict(color="blue"))

    # Format chart aesthetics
    fig2.update_layout(
        xaxis_title="Advisor",
        yaxis_title="Attendees Registered",
        template="plotly_white",
        showlegend=False,  # ✅ Completely remove legend
        margin=dict(l=50, r=50, t=50, b=50),
    )

    # Show chart in Streamlit
    st.plotly_chart(fig2, use_container_width=True)

    st.markdown("<h1 style='text-align: left;'>Top 5 Ambassadors by Registrations</h1>", unsafe_allow_html=True)

    ## Get top 5 ambassador sources
    top_amb = filtered_ambassador_counts.nlargest(5, "Count")  # ✅ Keep only top 5

    # Create a Plotly bar chart
    fig3 = px.bar(
        top_amb,  # ✅ Use the correct DataFrame
        x="Response",
        y="Count",
        orientation="v",
        text="Count",
    )

    # Manually set all bars to blue
    fig3.update_traces(marker=dict(color="blue"))

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
    


    from st_aggrid import AgGrid, GridOptionsBuilder
    from st_aggrid.shared import GridUpdateMode



    # Get top 5 ambassador sources

    # Create AgGrid options
    gb = GridOptionsBuilder.from_dataframe(filtered_ambassador_counts)
    gb.configure_pagination(enabled=True)  # ✅ Add pagination
    gb.configure_side_bar()  # ✅ Enable side panel for filtering
    gb.configure_selection(selection_mode="single")  # ✅ Allow row selection
    gb.configure_grid_options(domLayout='autoHeight')  # ✅ Adjust height automatically

    # Convert options to GridOptions
    grid_options = gb.build()

    # 🎯 Replace Plotly chart with AgGrid table
    st.subheader("Ambassadors by Registrations")

    AgGrid(
        filtered_ambassador_counts,
        gridOptions=grid_options,
        enable_enterprise_modules=True,  # ✅ Enables advanced features
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,  # ✅ Auto-adjust columns
        theme="balham",  # ✅ Set grid theme
        )
    
    gb2 = GridOptionsBuilder.from_dataframe(filtered_advisor_counts)
    gb2.configure_pagination(enabled=True)  # ✅ Add pagination
    gb2.configure_side_bar()  # ✅ Enable side panel for filtering
    gb2.configure_selection(selection_mode="single")  # ✅ Allow row selection
    gb2.configure_grid_options(domLayout='autoHeight')  # ✅ Adjust height automatically

    # Convert options to GridOptions
    grid_options = gb2.build()

    # 🎯 Replace Plotly chart with AgGrid table
    st.subheader("Advisors by Registrations")

    AgGrid(
        filtered_advisor_counts,
        gridOptions=grid_options,
        enable_enterprise_modules=True,  # ✅ Enables advanced features
        update_mode=GridUpdateMode.SELECTION_CHANGED,
        fit_columns_on_grid_load=True,  # ✅ Auto-adjust columns
        theme="balham",  # ✅ Set grid theme
        )
