# schedule_dashboard.py

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go # Make sure go is imported
import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from datetime import datetime, time, timedelta
import io # For capturing df.info() output

# --- 1. Data Loading and Preprocessing ---
def load_and_preprocess_data(excel_path=r"C:\Users\Dave\Documents\CH EN Schedule\Fall2025_Schedule.xlsx"):
    # ... (try-except for file reading, required columns check - remains the same) ...
    try:
        df = pd.read_excel(excel_path)
    except FileNotFoundError:
        print(f"Error: The file '{excel_path}' was not found. Please check the file path.")
        return pd.DataFrame()

    required_columns = ["Course", "Start", "Duration", "Days", "Instructor"]
    if not all(col in df.columns for col in required_columns):
        missing = [col for col in required_columns if col not in df.columns]
        print(f"Error: Missing required columns in Excel: {', '.join(missing)}")
        return pd.DataFrame()

    processed_events = []
    today = datetime.now().date()
    monday_of_week = today - timedelta(days=today.weekday()) 
    day_map = {
        'M': (0, 'Monday'), 'T': (1, 'Tuesday'), 'W': (2, 'Wednesday'),
        'R': (3, 'Thursday'), 'F': (4, 'Friday')
    }

    for index, row in df.iterrows():
        course_name = str(row["Course"])
        start_time_input = row["Start"]
        
        try:
            duration_minutes = int(row["Duration"])
            if duration_minutes <= 0:
                print(f"Warning (Row {index+2}): Non-positive duration '{duration_minutes}' for course '{course_name}'. Skipping this event.")
                continue
        except ValueError:
            print(f"Warning (Row {index+2}): Invalid duration format '{row['Duration']}' for course '{course_name}'. Skipping this event.")
            continue
            
        days_str = str(row["Days"]).upper()
        instructor = str(row["Instructor"])
        start_t = None

        if isinstance(start_time_input, time): start_t = start_time_input
        elif isinstance(start_time_input, datetime): start_t = start_time_input.time()
        elif isinstance(start_time_input, str):
            start_time_str = start_time_input.strip()
            parse_formats = ["%H:%M:%S", "%I:%M %p", "%H:%M", "%I:%M%p"]
            for fmt in parse_formats:
                try:
                    start_t = datetime.strptime(start_time_str, fmt).time()
                    break
                except ValueError: continue
        
        if start_t is None:
            # print(f"Warning (Row {index+2}): Could not parse start time '{start_time_input}' ...") # Keep if needed for debugging
            continue

        for day_char in days_str:
            if day_char in day_map:
                day_offset, day_name_full = day_map[day_char]
                event_date = monday_of_week + timedelta(days=day_offset)
                
                start_datetime_actual = datetime.combine(event_date, start_t)
                end_datetime_actual = start_datetime_actual + timedelta(minutes=duration_minutes)

                start_hour_float = start_t.hour + start_t.minute / 60.0 + start_t.second / 3600.0
                duration_hours_float = duration_minutes / 60.0 # Calculate DurationHours
                
                processed_events.append({
                    "Task": course_name,
                    "StartDateTime": start_datetime_actual, 
                    "FinishDateTime": end_datetime_actual, 
                    "StartHour": start_hour_float,
                    "DurationHours": duration_hours_float, # Added this field
                    "Resource": instructor,
                    "Day": day_name_full,
                    "HoverInfo": f"{course_name}<br>Instructor: {instructor}<br>Time: {start_t.strftime('%I:%M %p')} - {end_datetime_actual.strftime('%I:%M %p')}"
                })
            # ... (else for unknown day_char) ...
    
    if not processed_events: return pd.DataFrame()
    return pd.DataFrame(processed_events)

# --- Load data globally ---
all_events_df = load_and_preprocess_data()
if not all_events_df.empty:
    unique_courses = sorted(all_events_df["Task"].unique())
else:
    unique_courses = []

# --- Dash App Initialization and Layout (remains mostly the same) ---
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.COSMO])
app.layout = dbc.Container([
    # ... (layout definition as before) ...
    dbc.Row(dbc.Col(html.H1("College Department Course Schedule"), width=12, className="mb-4 mt-4 text-center")),
    dbc.Row([
        dbc.Col([
            html.Label("Select Courses to Display:", className="font-weight-bold"),
            dcc.Dropdown(
                id='course-dropdown-selector',
                options=[{'label': course, 'value': course} for course in unique_courses],
                value=unique_courses,
                multi=True,
                placeholder="Select courses..."
            ),
        ], width=12, className="mb-4")
    ]),
    dbc.Row([
        dbc.Col(dcc.Graph(id='schedule-gantt-chart'), width=12)
    ]),
    dbc.Row(dbc.Col(html.P("Hover over a course bar for more details.", className="text-muted small mt-3 text-center"), width=12))
], fluid=True)


# --- 3. Callback for Interactivity ---
@app.callback(
    Output('schedule-gantt-chart', 'figure'),
    [Input('course-dropdown-selector', 'value')]
)
def update_schedule_chart(selected_courses):
    # --- Y-axis (Time of Day) tick configuration ---
    hour_tick_start = 7 
    hour_tick_end = 19  
    # For Y-axis range: To have 7 AM at the top (like paper schedules), use a reversed range.
    y_axis_plot_range = [hour_tick_end + 0.5, hour_tick_start - 0.5] # Earlier times at top
    # y_axis_plot_range = [hour_tick_start - 0.5, hour_tick_end + 0.5] # Standard: Earlier times at bottom (This line is now commented out or removed)

    ytickvals = list(range(hour_tick_start, hour_tick_end + 1)) 
    yticktext = []
    for h_val in ytickvals:
        label_hour_val = h_val % 12 if h_val % 12 != 0 else 12
        am_pm_val = "AM" if h_val < 12 or h_val == 24 else "PM"
        if h_val == 0: label_hour_val, am_pm_val = 12, "AM"
        if h_val == 12: label_hour_val, am_pm_val = 12, "PM"
        yticktext.append(f"{label_hour_val} {am_pm_val}")
    # --- End Y-axis tick configuration ---

    days_of_week_ordered = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']

    # Base layout for empty or error states
    base_layout = dict(
        xaxis_title='Day of the Week', 
        yaxis_title='Time of Day',
        yaxis=dict(range=y_axis_plot_range, tickvals=ytickvals, ticktext=yticktext),
        xaxis=dict(categoryorder='array', categoryarray=days_of_week_ordered, type='category')
    )

    if not selected_courses or all_events_df.empty:
        fig = go.Figure()
        fig.update_layout(**base_layout)
        fig.update_layout(title_text="No courses selected or no data available.")
        return fig

    # Ensure 'DurationHours' is in all_events_df if it was just added
    if 'DurationHours' not in all_events_df.columns:
        print("Error: 'DurationHours' column is missing from all_events_df. Please check data preprocessing.")
        fig = go.Figure()
        fig.update_layout(**base_layout)
        fig.update_layout(title_text="Error: Data processing issue (DurationHours missing).")
        return fig
        
    filtered_df = all_events_df[all_events_df['Task'].isin(selected_courses)]

    if filtered_df.empty or 'StartHour' not in filtered_df.columns or 'DurationHours' not in filtered_df.columns \
       or filtered_df['StartHour'].isnull().all() or filtered_df['DurationHours'].isnull().all():
        fig = go.Figure()
        fig.update_layout(**base_layout)
        fig.update_layout(title_text="No valid schedule data to plot for selected courses.")
        return fig

    fig = go.Figure()

    # Create a color map for courses
    unique_tasks_in_filter = filtered_df['Task'].unique()
    plotly_colors = px.colors.qualitative.Plotly 
    course_color_map = {task: plotly_colors[i % len(plotly_colors)] for i, task in enumerate(unique_tasks_in_filter)}

    # print(f"\n--- Debug: Callback - plotting with go.Bar. Filtered df shape: {filtered_df.shape}")
    # Optional: print filtered_df.head() again if needed

    for index, event in filtered_df.iterrows():
        # Ensure data for bar is valid
        if pd.isna(event['StartHour']) or pd.isna(event['DurationHours']) or event['DurationHours'] <= 0:
            print(f"Skipping event due to invalid StartHour/DurationHours: {event['Task']} on {event['Day']}")
            continue

        fig.add_trace(go.Bar(
            x=[event['Day']],             # Day of the week on X-axis (categorical)
            y=[event['DurationHours']],   # Duration as height on Y-axis
            base=[event['StartHour']],    # Start time as base on Y-axis
            name=event['Task'],           # Course name for legend
            marker_color=course_color_map.get(event['Task']),
            customdata=[event['HoverInfo']],
            hovertemplate='%{customdata}<extra></extra>', # Show only custom hover text
            text=f"{event['Task']}",      # Text on bar (course name)
            textposition='inside',
            insidetextanchor='middle',    # Center text if possible
            width=0.5                     # Adjust bar width (0.0 to 1.0 relative to category width)
        ))
    
    # print(f"Added {len(fig.data)} traces to the figure.")

    # ... (inside update_schedule_chart function) ...

    fig.update_layout(
        title_text='Weekly Course Schedule',
        xaxis_title='Day of the Week',
        yaxis_title='Time of Day',
        xaxis=dict(
            categoryorder='array',
            categoryarray=days_of_week_ordered,
            side='top'  # <<< --- ADD THIS LINE TO MOVE X-AXIS TO THE TOP
        ),
        yaxis=dict(
            range=y_axis_plot_range, 
            tickvals=ytickvals,
            ticktext=yticktext,
        ),
        barmode='group', # CHANGED FROM 'overlay' to 'group'
        legend_title_text='Courses',
        showlegend=True, # CHANGED to True (temporarily or if desired)
        margin=dict(t=50, b=50, l=50, r=30)
    )
    fig.update_traces(textfont_size=9)

    if not fig.data:
        print("Warning: No traces were added to the figure, chart will be empty.")
        fig.update_layout(title_text="No courses to display based on current filter and data.")

    return fig

# --- Run the App ---
if __name__ == '__main__':
    if all_events_df.empty and not unique_courses:
         print("\nCould not start the dashboard because no data was loaded or processed.")
    else:
        app.run(debug=True)