import streamlit as st
import pandas as pd
from datetime import datetime
import re
import os
import paramiko  # Import for SSH access

# Additional imports
import numpy as np
import geoip2.database
from user_agents import parse
import pydeck as pdk

# Path to the GeoLite2 database file
GEOIP_DATABASE = 'GeoLite2-City.mmdb'

# Path to save the downloaded log file
LOCAL_LOG_PATH = 'access_logs.txt'

# SSH login credentials for PythonAnywhere
HOST = 'ssh.pythonanywhere.com'
USERNAME = 'cnichols1734'  # Replace with your PythonAnywhere username
PASSWORD = 'Cassiechris177!'  # Replace with your PythonAnywhere password
LOG_PATH = '/var/log/cnichols1734.pythonanywhere.com.access.log'  # Remote log path

# Configure Streamlit page
st.set_page_config(
    page_title="cnichols1734.pythonanywhere.com Access Logs Viewer",
    layout="wide",
    initial_sidebar_state="expanded",
)

def get_access_logs():
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(HOST, username=USERNAME, password=PASSWORD)

    sftp = ssh.open_sftp()
    try:
        # Download the logs as a temporary bytes object
        with sftp.open(LOG_PATH, 'r') as remote_file:
            new_logs = remote_file.read().decode('utf-8')  # Decode bytes to string

        # Check if the local log file already exists
        if os.path.exists(LOCAL_LOG_PATH):
            # Read existing logs (in text mode)
            with open(LOCAL_LOG_PATH, 'r') as local_file:
                existing_logs = local_file.read()

            # Combine existing logs with new logs (filter duplicates if necessary)
            combined_logs = existing_logs + new_logs

            # Optionally: Filter out duplicate log lines if needed
            combined_logs = '\n'.join(sorted(set(combined_logs.splitlines())))

        else:
            # If no local log file exists, use the new logs as the base
            combined_logs = new_logs

        # Write the combined logs back to the local file
        with open(LOCAL_LOG_PATH, 'w') as local_file:
            local_file.write(combined_logs)

        st.success(f"Logs retrieved successfully and saved to {LOCAL_LOG_PATH}")

    except Exception as e:
        st.error(f"Failed to retrieve logs: {e}")
    finally:
        sftp.close()
        ssh.close()



def parse_log_line(line):
    """
    Parses a single log line and returns a dictionary of its components.
    """
    log_pattern = re.compile(
        r'(?P<ip>\S+) - - \[(?P<datetime>[^\]]+)\] '
        r'"(?P<method>\S+) (?P<path>\S+) (?P<protocol>[^"]+)" '
        r'(?P<status>\d{3}) (?P<size>\d+) "(?P<referrer>[^"]*)" "(?P<user_agent>[^"]*)" '
        r'"(?P<remote_ip>\S+)" response-time=(?P<response_time>\d+\.\d+)'
    )

    match = log_pattern.match(line)
    if match:
        data = match.groupdict()
        # Convert datetime string to a datetime object
        try:
            data['datetime'] = datetime.strptime(data['datetime'], '%d/%b/%Y:%H:%M:%S %z')
        except ValueError:
            data['datetime'] = None
        # Convert numeric fields
        try:
            data['status'] = int(data['status'])
        except:
            data['status'] = None
        try:
            data['size'] = int(data['size'])
        except:
            data['size'] = None
        try:
            data['response_time'] = float(data['response_time'])
        except:
            data['response_time'] = None
        return data
    else:
        return None


@st.cache_resource
def load_geoip_reader():
    return geoip2.database.Reader(GEOIP_DATABASE)


def get_geo_info(ip):
    try:
        reader = load_geoip_reader()
        response = reader.city(ip)
        return {
            'country': response.country.name,
            'city': response.city.name,
            'latitude': response.location.latitude,
            'longitude': response.location.longitude
        }
    except:
        return {
            'country': None,
            'city': None,
            'latitude': None,
            'longitude': None
        }


def get_device_type(ua_string):
    try:
        user_agent = parse(ua_string)
        if user_agent.is_mobile:
            return 'Mobile'
        elif user_agent.is_tablet:
            return 'Tablet'
        elif user_agent.is_pc:
            return 'Desktop'
        else:
            return 'Other'
    except:
        return 'Unknown'


bot_keywords = ['bot', 'spider', 'crawler', 'crawl', 'slurp', 'archive', 'ahrefs',
                'bingpreview', 'bingbot', 'yandex', 'baiduspider', 'facebookexternalhit', 'google', 'gsa-crawler']


def is_bot(ua_string):
    if ua_string:
        ua_string_lower = ua_string.lower()
        for keyword in bot_keywords:
            if keyword in ua_string_lower:
                return True
    return False


def load_logs(content):
    """
    Loads and parses the access logs from raw text content.
    """
    lines = content.strip().split('\n')
    parsed_logs = []
    for line in lines:
        parsed = parse_log_line(line)
        if parsed and parsed['datetime']:
            parsed_logs.append(parsed)
    df = pd.DataFrame(parsed_logs)

    if not df.empty:
        # Process geolocation
        unique_ips = df['ip'].unique()
        ip_geo_info = {}
        for ip in unique_ips:
            ip_geo_info[ip] = get_geo_info(ip)
        geo_df = pd.DataFrame.from_dict(ip_geo_info, orient='index')
        geo_df.index.name = 'ip'
        geo_df.reset_index(inplace=True)
        # Merge with df
        df = pd.merge(df, geo_df, on='ip', how='left')

        # Process device types
        unique_user_agents = df['user_agent'].unique()
        ua_device_info = {}
        for ua in unique_user_agents:
            ua_device_info[ua] = get_device_type(ua)
        device_df = pd.DataFrame.from_dict(ua_device_info, orient='index', columns=['device_type'])
        device_df.index.name = 'user_agent'
        device_df.reset_index(inplace=True)
        # Merge with df
        df = pd.merge(df, device_df, on='user_agent', how='left')

        # Bot detection
        df['is_bot'] = df['user_agent'].apply(is_bot)

    return df


def analyze_logs(df):
    st.markdown("---")
    st.subheader("Log Analysis")

    # Convert datetime for easier manipulation
    df['datetime'] = pd.to_datetime(df['datetime'])

    # Sidebar Filters
    st.sidebar.header("Filters")
    include_bots = st.sidebar.checkbox("Include Bot Traffic", value=True)
    selected_ips = st.sidebar.multiselect("Select IP Addresses", options=sorted(df['ip'].unique()), default=[])
    selected_status = st.sidebar.multiselect("Select Status Codes", options=sorted(df['status'].unique()), default=[])
    date_range = st.sidebar.date_input(
        "Select Date Range",
        [df['datetime'].min().date(), df['datetime'].max().date()]
    )

    # Apply Filters
    filtered_df = df.copy()
    if not include_bots:
        filtered_df = filtered_df[~filtered_df['is_bot']]
    if selected_ips:
        filtered_df = filtered_df[filtered_df['ip'].isin(selected_ips)]
    if selected_status:
        filtered_df = filtered_df[filtered_df['status'].isin(selected_status)]
    if len(date_range) == 2:
        start_date, end_date = date_range
        filtered_df = filtered_df[
            (filtered_df['datetime'].dt.date >= start_date) &
            (filtered_df['datetime'].dt.date <= end_date)
            ]

    # Executive Summary
    st.markdown("## Executive Summary")
    total_visits = len(filtered_df)
    unique_visitors = filtered_df['ip'].nunique()
    top_path = filtered_df['path'].value_counts().idxmax()
    top_path_count = filtered_df['path'].value_counts().max()
    hourly_traffic = filtered_df.set_index('datetime').resample('h').size()
    peak_hour = hourly_traffic.idxmax().strftime('%Y-%m-%d %H:%M:%S')
    peak_hour_count = hourly_traffic.max()

    st.markdown(f"- **Total Visits:** {total_visits}")
    st.markdown(f"- **Unique Visitors:** {unique_visitors}")
    st.markdown(f"- **Top Path:** {top_path} with {top_path_count} visits")
    st.markdown(f"- **Peak Traffic Hour:** {peak_hour} with {peak_hour_count} visits")

    # Dashboard Layout with Tabs
    st.markdown("---")
    st.subheader("Log Analysis")

    tab1, tab2, tab3 = st.tabs(["Overview", "Detailed Analysis", "Advanced Features"])

    with tab1:
        # High-level metrics
        st.markdown("### High-Level Metrics")
        col1, col2 = st.columns(2)
        with col1:
            st.metric(label="Total Visits", value=total_visits)
        with col2:
            st.metric(label="Unique Visitors", value=unique_visitors)

        st.markdown("### Traffic Over Time")
        df_sorted = filtered_df.sort_values('datetime')
        traffic_over_time = df_sorted.set_index('datetime').resample('h').size()
        st.line_chart(traffic_over_time)

        st.markdown("### Top Paths")
        paths = filtered_df['path'].value_counts().head(10)
        st.bar_chart(paths)

    with tab2:
        st.markdown("### Filtered Access Logs")
        st.dataframe(filtered_df)

        st.markdown("### Requests by IP Address")
        ip_counts = filtered_df['ip'].value_counts().head(10)
        st.bar_chart(ip_counts)

        st.markdown("### Status Code Distribution")
        status_counts = filtered_df['status'].value_counts()
        st.bar_chart(status_counts)

        st.markdown("### Response Time Statistics")
        st.write(filtered_df['response_time'].describe())

        # Error Tracking
        st.markdown("#### Error Responses (4xx and 5xx)")
        error_df = filtered_df[filtered_df['status'] >= 400]
        if not error_df.empty:
            st.dataframe(error_df)
        else:
            st.write("No error responses found.")

    with tab3:
        st.markdown("### Geolocation Map")
        if 'latitude' in filtered_df.columns and 'longitude' in filtered_df.columns:
            map_data = filtered_df[['latitude', 'longitude']].dropna()
            if not map_data.empty:
                st.map(map_data)
            else:
                st.write("No geolocation data available.")
        else:
            st.write("Geolocation data not available.")

        # **Heatmap Visualization**
        st.markdown("### Request Density Heatmap")
        if not map_data.empty:
            midpoint = (np.average(map_data['latitude']), np.average(map_data['longitude']))
            heatmap_layer = pdk.Layer(
                "HeatmapLayer",
                data=map_data,
                get_position='[longitude, latitude]',
                radius=100,
                opacity=0.6,
            )

            view_state = pdk.ViewState(
                latitude=midpoint[0],
                longitude=midpoint[1],
                zoom=1,
                pitch=0,
            )

            heatmap = pdk.Deck(
                map_style='mapbox://styles/mapbox/light-v9',
                layers=[heatmap_layer],
                initial_view_state=view_state,
            )

            st.pydeck_chart(heatmap)
        else:
            st.write("No data available for heatmap.")

        st.markdown("### Device Type Distribution")
        device_counts = filtered_df['device_type'].value_counts()
        st.bar_chart(device_counts)

        st.markdown("### User Agent Analysis")
        user_agents = filtered_df['user_agent'].value_counts().head(10)
        st.bar_chart(user_agents)

        # **Bot Analysis**
        st.markdown("### Bot Traffic Analysis")
        total_requests = len(df)
        total_bots = df['is_bot'].sum()
        total_humans = total_requests - total_bots

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Bot Requests", total_bots)
        with col2:
            st.metric("Total Human Requests", total_humans)

        st.markdown("#### Bot vs. Human Traffic")
        bot_human_counts = pd.Series({'Bots': total_bots, 'Humans': total_humans})
        st.bar_chart(bot_human_counts)

        st.markdown("#### Top Bots by User-Agent")
        bot_user_agents = df[df['is_bot']]['user_agent'].value_counts().head(10)
        st.bar_chart(bot_user_agents)

        st.markdown("#### Bot Traffic Over Time")
        bot_traffic = df[df['is_bot']].set_index('datetime').resample('h').size()
        st.line_chart(bot_traffic)

    # Download Filtered Logs
    st.markdown("### Download Filtered Logs")
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download CSV",
        data=csv,
        file_name='filtered_logs.csv',
        mime='text/csv',
    )


def main():
    st.title("📈 PythonAnywhere Access Logs Viewer")

    # Button to fetch the latest logs
    if st.button('Fetch Latest Logs'):
        get_access_logs()

    # Check if the log file exists after fetching
    if os.path.exists(LOCAL_LOG_PATH):
        with open(LOCAL_LOG_PATH, 'r') as log_file:
            content = log_file.read()

        df = load_logs(content)

        if not df.empty:
            st.success("✅ Logs successfully parsed!")
            # Proceed to analysis
            analyze_logs(df)
        else:
            st.error("❌ No valid log entries found.")
    else:
        st.info("📂 Click the button above to fetch logs from your PythonAnywhere account.")


if __name__ == "__main__":
    main()
