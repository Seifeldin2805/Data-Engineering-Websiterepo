"""
NYC Motor Vehicle Collisions - Interactive Data Visualization Dashboard
=======================================================================
A professional, interactive web application for exploring NYC crash data
with comprehensive filtering, search capabilities, and dynamic visualizations.
"""

import dash
from dash import dcc, html, Input, Output, State, callback
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import os
import re
import sys
from datetime import datetime

# Fix Windows console encoding issues
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except:
        pass

# ============================================================================
# DATA LOADING AND PREPROCESSING
# ============================================================================

def load_data():
    """
    Load and preprocess the crash data from Parquet file.
    Handles missing files gracefully with empty dataframe structure.
    """
    DATA_PATH = os.path.join('data', 'df_merged_clean.parquet')
    try:
        # Read parquet file
        df = pd.read_parquet(DATA_PATH)
        print(f"Data loaded successfully: {len(df):,} records")
        
        # Data cleaning and type conversions
        # Convert CRASH_YEAR to numeric (handle various formats)
        if 'CRASH_YEAR' in df.columns:
            df['CRASH_YEAR'] = pd.to_numeric(df['CRASH_YEAR'], errors='coerce')
            # Remove invalid years
            df = df[(df['CRASH_YEAR'].isna()) | ((df['CRASH_YEAR'] >= 1900) & (df['CRASH_YEAR'] <= 2100))]
        
        # Ensure numeric columns are properly typed
        numeric_cols = [
            'LATITUDE', 'LONGITUDE', 'NUMBER_OF_PERSONS_INJURED',
            'NUMBER_OF_PERSONS_KILLED', 'CRASH_HOUR', 'CRASH_DAY',
            'TOTAL_INJURED', 'TOTAL_KILLED'
        ]
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Clean string columns to handle encoding issues
        string_cols = ['VEHICLE_TYPE_CODE_1', 'VEHICLE_TYPE_CODE_2', 
                      'CONTRIBUTING_FACTOR_VEHICLE_1', 'CONTRIBUTING_FACTOR_VEHICLE_2',
                      'BOROUGH']
        for col in string_cols:
            if col in df.columns:
                df[col] = df[col].astype(str).apply(
                    lambda x: x.encode('utf-8', errors='ignore').decode('utf-8') 
                    if pd.notna(x) and x != 'nan' else ''
                )
                # Replace 'nan' strings with empty
                df[col] = df[col].replace('nan', '')
        
        return df
    except FileNotFoundError:
        print("WARNING: Data file not found. Application will run with empty dataset.")
        # Return empty dataframe with expected structure
        return pd.DataFrame({
            'CRASH_DATE': [], 'CRASH_TIME': [], 'BOROUGH': [], 'ZIP_CODE': [],
            'LATITUDE': [], 'LONGITUDE': [], 'ON_STREET_NAME': [], 
            'CROSS_STREET_NAME': [], 'OFF_STREET_NAME': [],
            'NUMBER_OF_PERSONS_INJURED': [], 'NUMBER_OF_PERSONS_KILLED': [],
            'NUMBER_OF_PEDESTRIANS_INJURED': [], 'NUMBER_OF_PEDESTRIANS_KILLED': [],
            'NUMBER_OF_CYCLIST_INJURED': [], 'NUMBER_OF_CYCLIST_KILLED': [],
            'NUMBER_OF_MOTORIST_INJURED': [], 'NUMBER_OF_MOTORIST_KILLED': [],
            'CONTRIBUTING_FACTOR_VEHICLE_1': [], 'CONTRIBUTING_FACTOR_VEHICLE_2': [],
            'COLLISION_ID': [], 'VEHICLE_TYPE_CODE_1': [], 'VEHICLE_TYPE_CODE_2': [],
            'CRASH_DATETIME': [], 'CRASH_HOUR': [], 'CRASH_DAY': [],
            'CRASH_WEEKDAY': [], 'CRASH_MONTH': [], 'CRASH_YEAR': [],
            'IS_WEEKEND': [], 'TOTAL_PERSONS': [], 'TOTAL_INJURED': [],
            'TOTAL_KILLED': [], 'AVG_PERSON_AGE': [], 'FEMALE_PERSONS': [],
            'MALE_PERSONS': [], 'UNKNOWN_SEX': []
        })
    except Exception as e:
        print(f"ERROR: Error loading data: {str(e)}")
        return pd.DataFrame()

# Load initial dataset
df = load_data()

# ============================================================================
# HELPER FUNCTIONS
# ============================================================================

def parse_search_query(query):
    """
    Parse natural language search query and extract filter parameters.
    
    Examples:
        "Brooklyn 2022 pedestrian crashes" -> borough=Brooklyn, year=2022, injury_type=Pedestrian
        "Queens speeding accidents" -> borough=Queens, contributing_factor=Unsafe Speed
    
    Returns:
        dict: Filter parameters with keys: borough, year, vehicle_type, 
              contributing_factor, injury_type
    """
    if not query:
        return {
            'borough': None, 'year': None, 'vehicle_type': None,
            'contributing_factor': None, 'injury_type': None
        }
    
    filters = {
        'borough': None, 'year': None, 'vehicle_type': None,
        'contributing_factor': None, 'injury_type': None
    }
    
    query_lower = query.lower()
    
    # Extract borough
    boroughs = {
        'brooklyn': 'BROOKLYN', 'manhattan': 'MANHATTAN', 
        'queens': 'QUEENS', 'bronx': 'BRONX', 
        'staten island': 'STATEN ISLAND'
    }
    for key, value in boroughs.items():
        if key in query_lower:
            filters['borough'] = value
            break
    
    # Extract year (4-digit years)
    year_match = re.search(r'\b(19|20)\d{2}\b', query)
    if year_match:
        full_year_match = re.search(r'\b(19\d{2}|20\d{2})\b', query)
        if full_year_match:
            try:
                filters['year'] = int(full_year_match.group())
            except ValueError:
                pass
    
    # Extract vehicle type keywords - match actual data values
    # Note: Vehicle types in data are full names like "Sedan", "Station Wagon/Sport Utility Vehicle"
    vehicle_keywords = {
        'sedan': 'Sedan', 
        'suv': 'Station Wagon/Sport Utility Vehicle', 'sport utility': 'Station Wagon/Sport Utility Vehicle',
        'truck': 'Truck', 'pickup': 'Pick-up Truck',
        'motorcycle': 'Motorcycle', 'moped': 'Moped',
        'bicycle': 'Bicycle', 'bike': 'Bicycle',
        'bus': 'Bus',
        'van': 'Van',
        'taxi': 'Taxi',
        'ambulance': 'Ambulance'
    }
    for key, value in vehicle_keywords.items():
        if key in query_lower:
            filters['vehicle_type'] = value
            break
    
    # Extract injury type
    if 'pedestrian' in query_lower:
        filters['injury_type'] = 'Pedestrian'
    elif 'cyclist' in query_lower or 'bicycle' in query_lower:
        filters['injury_type'] = 'Cyclist'
    elif 'motorist' in query_lower or 'driver' in query_lower:
        filters['injury_type'] = 'Motorist'
    
    # Extract contributing factors
    factor_keywords = {
        'speeding': 'Unsafe Speed', 'speed': 'Unsafe Speed',
        'alcohol': 'Alcohol Involvement', 'drunk': 'Alcohol Involvement',
        'distraction': 'Driver Inattention/Distraction',
        'inattention': 'Driver Inattention/Distraction',
        'red light': 'Traffic Control Disregarded',
        'stop sign': 'Traffic Control Disregarded'
    }
    for key, value in factor_keywords.items():
        if key in query_lower:
            filters['contributing_factor'] = value
            break
    
    return filters

def get_dropdown_options(df):
    """
    Extract unique values from dataframe for dropdown filter options.
    Handles missing columns gracefully.
    
    Returns:
        dict: Options for each filter type
    """
    options = {
        'boroughs': [], 'years': [], 'vehicle_types': [],
        'contributing_factors': [], 'injury_types': ['All', 'Pedestrian', 'Cyclist', 'Motorist']
    }
    
    if df.empty:
        return options
    
    # Boroughs
    if 'BOROUGH' in df.columns:
        boroughs = [b for b in df['BOROUGH'].dropna().unique() if b and str(b).strip()]
        options['boroughs'] = sorted(boroughs)
    
    # Years - handle various data types
    if 'CRASH_YEAR' in df.columns:
        years_list = []
        for y in df['CRASH_YEAR'].dropna().unique():
            try:
                # Convert to numeric first
                year_val = pd.to_numeric(y, errors='coerce')
                if pd.notna(year_val) and year_val >= 1900 and year_val <= 2100:
                    years_list.append(int(year_val))
            except:
                continue
        options['years'] = sorted(list(set(years_list)))  # Remove duplicates and sort
    
    # Vehicle types - filter to show only valid, common vehicle types
    if 'VEHICLE_TYPE_CODE_1' in df.columns:
        # Get value counts to prioritize common vehicle types
        all_vehicles = pd.concat([df['VEHICLE_TYPE_CODE_1'], df['VEHICLE_TYPE_CODE_2']]).dropna()
        vehicle_counts = all_vehicles.value_counts()
        
        # Filter for valid vehicle types: at least 3 chars, contains letters, not mostly numbers/symbols
        valid_vehicle_types = []
        invalid_patterns = ['', 'nan', 'None', 'Unknown', '-', '.', '0', '1', '2', '3', '4', '5', '6', '7', '8', '9']
        
        for v_type, count in vehicle_counts.items():
            if pd.notna(v_type):
                v_str = str(v_type).strip()
                # Must be: non-empty, at least 4 chars, contains letters, not mostly symbols/numbers
                if (v_str and 
                    v_str not in invalid_patterns and
                    len(v_str) >= 4 and  # At least 4 characters
                    not v_str.isdigit() and  # Not just numbers
                    not v_str.startswith("'") and  # Not weird quoted strings
                    not v_str.startswith("(") and  # Not starting with parenthesis (likely corrupted)
                    not v_str[0].isdigit() and  # Doesn't start with digit
                    sum(c.isalpha() for c in v_str) >= 2):  # At least 2 letters
                    valid_vehicle_types.append(v_str)
        
        # Remove case-insensitive duplicates (keep the most common version)
        seen_lower = {}
        deduplicated = []
        for v_type in valid_vehicle_types:
            v_lower = v_type.lower()
            if v_lower not in seen_lower:
                seen_lower[v_lower] = v_type
                deduplicated.append(v_type)
            else:
                # Keep the one with higher count
                existing = seen_lower[v_lower]
                if vehicle_counts.get(v_type, 0) > vehicle_counts.get(existing, 0):
                    deduplicated.remove(existing)
                    deduplicated.append(v_type)
                    seen_lower[v_lower] = v_type
        
        # Sort by frequency (most common first), then alphabetically
        # Limit to top 50 most common valid types
        sorted_types = sorted(deduplicated, 
                            key=lambda x: (vehicle_counts.get(x, 0), x), 
                            reverse=True)[:50]
        options['vehicle_types'] = sorted(sorted_types)  # Final alphabetical sort
    
    # Contributing factors - filter out invalid entries and ensure proper encoding
    if 'CONTRIBUTING_FACTOR_VEHICLE_1' in df.columns:
        f1 = df['CONTRIBUTING_FACTOR_VEHICLE_1'].dropna().unique()
        f2 = df['CONTRIBUTING_FACTOR_VEHICLE_2'].dropna().unique() if 'CONTRIBUTING_FACTOR_VEHICLE_2' in df.columns else []
        factors = []
        invalid_patterns = ['', 'nan', 'None', 'Unspecified', 'Unknown', '-', '.', '0', '1', '2']
        for f in pd.concat([pd.Series(f1), pd.Series(f2)]).unique():
            if pd.notna(f):
                f_str = str(f).strip()
                # Filter out: empty, numbers only, single characters, and invalid patterns
                if (f_str and 
                    f_str not in invalid_patterns and
                    len(f_str) > 3 and  # Must be at least 4 characters (reasonable text)
                    not f_str.isdigit() and  # Not just numbers
                    any(c.isalpha() for c in f_str)):  # Must contain at least one letter
                    # Ensure proper encoding
                    try:
                        f_encoded = f_str.encode('utf-8', errors='ignore').decode('utf-8')
                        if f_encoded:
                            factors.append(f_encoded)
                    except:
                        pass
        # Remove duplicates and sort
        options['contributing_factors'] = sorted(list(set(factors)))
    
    return options

def apply_filters(df, filters):
    """
    Apply all filters to the dataframe.
    
    Args:
        df: Input dataframe
        filters: Dict with filter values (borough, year, vehicle_type, etc.)
    
    Returns:
        Filtered dataframe
    """
    filtered_df = df.copy()
    
    # Borough filter
    if filters.get('borough') and filters['borough'] != 'All':
        filtered_df = filtered_df[filtered_df['BOROUGH'] == filters['borough']]
    
    # Year filter
    if filters.get('year') and filters['year'] != 'All':
        if isinstance(filters['year'], (int, float)):
            filtered_df = filtered_df[filtered_df['CRASH_YEAR'] == filters['year']]
    
    # Vehicle type filter
    if filters.get('vehicle_type') and filters['vehicle_type'] != 'All':
        filtered_df = filtered_df[
            (filtered_df['VEHICLE_TYPE_CODE_1'] == filters['vehicle_type']) |
            (filtered_df['VEHICLE_TYPE_CODE_2'] == filters['vehicle_type'])
        ]
    
    # Contributing factor filter
    if filters.get('contributing_factor') and filters['contributing_factor'] != 'All':
        filtered_df = filtered_df[
            (filtered_df['CONTRIBUTING_FACTOR_VEHICLE_1'] == filters['contributing_factor']) |
            (filtered_df['CONTRIBUTING_FACTOR_VEHICLE_2'] == filters['contributing_factor'])
        ]
    
    # Injury type filter
    if filters.get('injury_type') and filters['injury_type'] != 'All':
        if filters['injury_type'] == 'Pedestrian':
            filtered_df = filtered_df[
                (filtered_df['NUMBER_OF_PEDESTRIANS_INJURED'] > 0) |
                (filtered_df['NUMBER_OF_PEDESTRIANS_KILLED'] > 0)
            ]
        elif filters['injury_type'] == 'Cyclist':
            filtered_df = filtered_df[
                (filtered_df['NUMBER_OF_CYCLIST_INJURED'] > 0) |
                (filtered_df['NUMBER_OF_CYCLIST_KILLED'] > 0)
            ]
        elif filters['injury_type'] == 'Motorist':
            filtered_df = filtered_df[
                (filtered_df['NUMBER_OF_MOTORIST_INJURED'] > 0) |
                (filtered_df['NUMBER_OF_MOTORIST_KILLED'] > 0)
            ]
    
    return filtered_df

# Initialize dropdown options
dropdown_options = get_dropdown_options(df)

# ============================================================================
# DASH APP INITIALIZATION
# ============================================================================

app = dash.Dash(__name__)
app.title = "NYC Motor Vehicle Collisions Dashboard"
server = app.server

# ============================================================================
# CUSTOM CSS STYLES
# ============================================================================

app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f5f7fa;
            }
            .main-container {
                max-width: 1400px;
                margin: 0 auto;
            }
            .stat-card {
                background: white;
                border-radius: 8px;
                padding: 20px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                margin-bottom: 20px;
            }
            .stat-number {
                font-size: 2em;
                font-weight: bold;
                color: #2c3e50;
            }
            .stat-label {
                color: #7f8c8d;
                font-size: 0.9em;
                margin-top: 5px;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

# ============================================================================
# APP LAYOUT
# ============================================================================

app.layout = html.Div([
    # Header Section
    html.Div([
        html.H1(
            "NYC Motor Vehicle Collisions Dashboard",
            style={
                'textAlign': 'center',
                'color': '#2c3e50',
                'marginBottom': '10px',
                'fontSize': '2.5em'
            }
        ),
        html.P(
            "Explore crash data with interactive visualizations and comprehensive filtering",
            style={
                'textAlign': 'center',
                'color': '#7f8c8d',
                'fontSize': '1.1em',
                'marginBottom': '30px'
            }
        )
    ], style={'marginBottom': '30px'}),
    
    # Main Content Container
    html.Div([
        # Left Sidebar - Filters
        html.Div([
            html.Div([
                html.H3("🔍 Search & Filters", style={
                    'color': '#2c3e50',
                    'marginBottom': '20px',
                    'borderBottom': '2px solid #3498db',
                    'paddingBottom': '10px'
                }),
                
                # Search Mode Section
                html.Div([
                    html.Label("Search Mode", style={
                        'fontWeight': 'bold',
                        'marginBottom': '8px',
                        'color': '#34495e'
                    }),
                    html.P("Try: 'Brooklyn 2022 pedestrian crashes'", style={
                        'fontSize': '0.85em',
                        'color': '#95a5a6',
                        'marginBottom': '8px',
                        'fontStyle': 'italic'
                    }),
                    dcc.Input(
                        id='search-input',
                        type='text',
                        placeholder='Enter natural language query...',
                        style={
                            'width': '100%',
                            'padding': '12px',
                            'borderRadius': '5px',
                            'border': '1px solid #ddd',
                            'marginBottom': '10px',
                            'fontSize': '14px'
                        }
                    ),
                    html.Button(
                        'Apply Search',
                        id='apply-search-btn',
                        n_clicks=0,
                        style={
                            'width': '100%',
                            'padding': '10px',
                            'backgroundColor': '#3498db',
                            'color': 'white',
                            'border': 'none',
                            'borderRadius': '5px',
                            'cursor': 'pointer',
                            'fontSize': '14px',
                            'fontWeight': 'bold',
                            'marginBottom': '20px'
                        }
                    ),
                ], style={'marginBottom': '25px', 'paddingBottom': '20px', 'borderBottom': '1px solid #ecf0f1'}),
                
                # Filter Dropdowns
                html.Div([
                    html.Label("Borough", style={'fontWeight': 'bold', 'marginBottom': '5px', 'color': '#34495e'}),
                    dcc.Dropdown(
                        id='borough-filter',
                        options=[{'label': 'All Boroughs', 'value': 'All'}] + 
                                [{'label': b, 'value': b} for b in dropdown_options['boroughs']],
                        value='All',
                        clearable=False,
                        style={'marginBottom': '15px'}
                    ),
                    
                    html.Label("Year", style={'fontWeight': 'bold', 'marginBottom': '5px', 'color': '#34495e'}),
                    dcc.Dropdown(
                        id='year-filter',
                        options=[{'label': 'All Years', 'value': 'All'}] + 
                                [{'label': str(int(y)) if pd.notna(y) else 'All', 
                                  'value': int(y) if pd.notna(y) else 'All'} 
                                 for y in dropdown_options['years'] if pd.notna(y)],
                        value='All',
                        clearable=False,
                        style={'marginBottom': '15px'}
                    ),
                    
                    html.Label("Vehicle Type", style={'fontWeight': 'bold', 'marginBottom': '5px', 'color': '#34495e'}),
                    dcc.Dropdown(
                        id='vehicle-type-filter',
                        options=[{'label': 'All Types', 'value': 'All'}] + 
                                [{'label': str(v), 'value': str(v)} 
                                 for v in dropdown_options['vehicle_types'] if v],
                        value='All',
                        clearable=False,
                        style={'marginBottom': '15px'}
                    ),
                    
                    html.Label("Contributing Factor", style={'fontWeight': 'bold', 'marginBottom': '5px', 'color': '#34495e'}),
                    dcc.Dropdown(
                        id='contributing-factor-filter',
                        options=[{'label': 'All Factors', 'value': 'All'}] + 
                                [{'label': str(c), 'value': str(c)} 
                                 for c in dropdown_options['contributing_factors'] if c],
                        value='All',
                        clearable=False,
                        style={'marginBottom': '15px'}
                    ),
                    
                    html.Label("Injury Type", style={'fontWeight': 'bold', 'marginBottom': '5px', 'color': '#34495e'}),
                    dcc.Dropdown(
                        id='injury-type-filter',
                        options=[{'label': it, 'value': it} for it in dropdown_options['injury_types']],
                        value='All',
                        clearable=False,
                        style={'marginBottom': '20px'}
                    ),
                ]),
                
                # Generate Report Button
                html.Button(
                    '📊 Generate Report',
                    id='generate-report-btn',
                    n_clicks=0,
                    style={
                        'width': '100%',
                        'padding': '15px',
                        'backgroundColor': '#27ae60',
                        'color': 'white',
                        'border': 'none',
                        'borderRadius': '5px',
                        'fontSize': '16px',
                        'fontWeight': 'bold',
                        'cursor': 'pointer',
                        'boxShadow': '0 4px 6px rgba(0,0,0,0.1)',
                        'transition': 'all 0.3s ease'
                    }
                ),
            ], style={
                'padding': '25px',
                'backgroundColor': 'white',
                'borderRadius': '10px',
                'boxShadow': '0 2px 10px rgba(0,0,0,0.1)',
                'height': 'fit-content',
                'position': 'sticky',
                'top': '20px'
            })
        ], style={
            'width': '23%',
            'display': 'inline-block',
            'verticalAlign': 'top',
            'marginRight': '2%'
        }),
        
        # Right Side - Visualizations
        html.Div([
            # Summary Statistics Cards
            html.Div(id='summary-stats', children=[]),
            
            # Visualizations Container
            html.Div(id='visualizations-container', children=[
                html.Div([
                    html.H3("👈 Select filters and click 'Generate Report' to view visualizations",
                           style={
                               'textAlign': 'center',
                               'color': '#95a5a6',
                               'padding': '100px 20px',
                               'fontSize': '1.2em'
                           })
                ])
            ])
        ], style={
            'width': '75%',
            'display': 'inline-block',
            'verticalAlign': 'top'
        })
    ], style={'maxWidth': '1400px', 'margin': '0 auto'})
], style={
    'padding': '20px',
    'fontFamily': '"Segoe UI", Tahoma, Geneva, Verdana, sans-serif',
    'backgroundColor': '#f5f7fa',
    'minHeight': '100vh'
})

# ============================================================================
# CALLBACKS
# ============================================================================

@callback(
    [Output('borough-filter', 'value'),
     Output('year-filter', 'value'),
     Output('vehicle-type-filter', 'value'),
     Output('contributing-factor-filter', 'value'),
     Output('injury-type-filter', 'value')],
    Input('apply-search-btn', 'n_clicks'),
    State('search-input', 'value'),
    prevent_initial_call=True
)
def apply_search(n_clicks, search_query):
    """
    Parse search query and update filter dropdowns automatically.
    """
    if not search_query:
        return 'All', 'All', 'All', 'All', 'All'
    
    filters = parse_search_query(search_query)
    
    return (
        filters['borough'] if filters['borough'] else 'All',
        filters['year'] if filters['year'] else 'All',
        filters['vehicle_type'] if filters['vehicle_type'] else 'All',
        filters['contributing_factor'] if filters['contributing_factor'] else 'All',
        filters['injury_type'] if filters['injury_type'] else 'All'
    )

@callback(
    [Output('visualizations-container', 'children'),
     Output('summary-stats', 'children')],
    Input('generate-report-btn', 'n_clicks'),
    State('borough-filter', 'value'),
    State('year-filter', 'value'),
    State('vehicle-type-filter', 'value'),
    State('contributing-factor-filter', 'value'),
    State('injury-type-filter', 'value'),
    prevent_initial_call=True
)
def update_visualizations(n_clicks, borough, year, vehicle_type, contributing_factor, injury_type):
    """
    Main callback to generate all visualizations and summary statistics
    based on selected filters. This function handles data filtering,
    validation, and chart creation.
    """
    # Error handling for empty dataset
    if df.empty or len(df) == 0:
        return (
            html.Div([
                html.Div([
                    html.H3("⚠️ No Data Available", style={'color': '#e74c3c'}),
                    html.P("Please ensure the data file is located at: data/df_merged_clean.parquet",
                          style={'color': '#7f8c8d'})
                ], style={
                    'textAlign': 'center',
                    'padding': '50px',
                    'backgroundColor': 'white',
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 10px rgba(0,0,0,0.1)'
                })
            ]),
            []
        )
    
    # Collect filter values
    filters = {
        'borough': borough,
        'year': year,
        'vehicle_type': vehicle_type,
        'contributing_factor': contributing_factor,
        'injury_type': injury_type
    }
    
    # Apply filters
    try:
        filtered_df = apply_filters(df, filters)
    except Exception as e:
        return (
            html.Div([
                html.Div([
                    html.H3("❌ Error Applying Filters", style={'color': '#e74c3c'}),
                    html.P(f"An error occurred: {str(e)}", style={'color': '#7f8c8d'})
                ], style={
                    'textAlign': 'center',
                    'padding': '50px',
                    'backgroundColor': 'white',
                    'borderRadius': '10px'
                })
            ]),
            []
        )
    
    # Handle empty filtered results
    if len(filtered_df) == 0:
        return (
            html.Div([
                html.Div([
                    html.H3("📭 No Data Matches Filters", style={'color': '#f39c12'}),
                    html.P("Try adjusting your filters or search criteria.", 
                          style={'color': '#7f8c8d'})
                ], style={
                    'textAlign': 'center',
                    'padding': '50px',
                    'backgroundColor': 'white',
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 10px rgba(0,0,0,0.1)'
                })
            ]),
            []
        )
    
    # Calculate summary statistics
    summary_stats = calculate_summary_stats(filtered_df)
    
    # Generate all visualizations
    visualizations = create_all_visualizations(filtered_df)
    
    return visualizations, summary_stats

def calculate_summary_stats(filtered_df):
    """
    Calculate key summary statistics for the filtered dataset.
    
    Returns:
        List of HTML Div elements containing stat cards
    """
    stats = []
    
    try:
        total_crashes = len(filtered_df)
        total_injured = filtered_df['TOTAL_INJURED'].sum() if 'TOTAL_INJURED' in filtered_df.columns else \
                       filtered_df['NUMBER_OF_PERSONS_INJURED'].sum() if 'NUMBER_OF_PERSONS_INJURED' in filtered_df.columns else 0
        total_killed = filtered_df['TOTAL_KILLED'].sum() if 'TOTAL_KILLED' in filtered_df.columns else \
                      filtered_df['NUMBER_OF_PERSONS_KILLED'].sum() if 'NUMBER_OF_PERSONS_KILLED' in filtered_df.columns else 0
        
        # Calculate average per crash
        avg_injured = total_injured / total_crashes if total_crashes > 0 else 0
        avg_killed = total_killed / total_crashes if total_crashes > 0 else 0
        
        stats = [
            html.Div([
                html.Div([
                    html.Div([
                        html.Div([
                            html.H2(f"{total_crashes:,}", className='stat-number',
                                   style={'color': '#3498db', 'margin': '0'}),
                            html.P("Total Crashes", className='stat-label')
                        ], style={
                            'textAlign': 'center',
                            'padding': '20px',
                            'backgroundColor': 'white',
                            'borderRadius': '8px',
                            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                        })
                    ], style={'width': '24%', 'display': 'inline-block', 'marginRight': '1%'}),
                    
                    html.Div([
                        html.Div([
                            html.H2(f"{int(total_injured):,}", className='stat-number',
                                   style={'color': '#f39c12', 'margin': '0'}),
                            html.P("Total Injured", className='stat-label')
                        ], style={
                            'textAlign': 'center',
                            'padding': '20px',
                            'backgroundColor': 'white',
                            'borderRadius': '8px',
                            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                        })
                    ], style={'width': '24%', 'display': 'inline-block', 'marginRight': '1%'}),
                    
                    html.Div([
                        html.Div([
                            html.H2(f"{int(total_killed):,}", className='stat-number',
                                   style={'color': '#e74c3c', 'margin': '0'}),
                            html.P("Total Killed", className='stat-label')
                        ], style={
                            'textAlign': 'center',
                            'padding': '20px',
                            'backgroundColor': 'white',
                            'borderRadius': '8px',
                            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                        })
                    ], style={'width': '24%', 'display': 'inline-block', 'marginRight': '1%'}),
                    
                    html.Div([
                        html.Div([
                            html.H2(f"{avg_injured:.2f}", className='stat-number',
                                   style={'color': '#27ae60', 'margin': '0'}),
                            html.P("Avg Injured/Crash", className='stat-label')
                        ], style={
                            'textAlign': 'center',
                            'padding': '20px',
                            'backgroundColor': 'white',
                            'borderRadius': '8px',
                            'boxShadow': '0 2px 4px rgba(0,0,0,0.1)'
                        })
                    ], style={'width': '24%', 'display': 'inline-block'})
                ])
            ], style={'marginBottom': '30px'})
        ]
    except Exception as e:
        print(f"Error calculating summary stats: {e}")
    
    return stats

def create_all_visualizations(filtered_df):
    """
    Create all visualization charts based on filtered data.
    
    Returns:
        List of HTML Div elements containing dcc.Graph components
    """
    visualizations = []
    
    # 1. Bar Chart: Crashes by Borough
    if 'BOROUGH' in filtered_df.columns and len(filtered_df['BOROUGH'].dropna()) > 0:
        try:
            borough_counts = filtered_df['BOROUGH'].value_counts().reset_index()
            borough_counts.columns = ['BOROUGH', 'Count']
            fig_bar = px.bar(
                borough_counts, 
                x='BOROUGH', 
                y='Count',
                title='📊 Crashes by Borough',
                labels={'Count': 'Number of Crashes', 'BOROUGH': 'Borough'},
                color='Count',
                color_continuous_scale='Blues'
            )
            fig_bar.update_layout(
                showlegend=False,
                template='plotly_white',
                height=400,
                margin=dict(l=20, r=20, t=60, b=20)
            )
            visualizations.append(
                html.Div([
                    dcc.Graph(figure=fig_bar)
                ], style={
                    'marginBottom': '30px',
                    'backgroundColor': 'white',
                    'padding': '20px',
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 10px rgba(0,0,0,0.1)'
                })
            )
        except Exception as e:
            print(f"Error creating borough chart: {e}")
    
    # 2. Line Chart: Crashes Over Time by Year
    if 'CRASH_YEAR' in filtered_df.columns and len(filtered_df['CRASH_YEAR'].dropna()) > 0:
        try:
            year_counts = filtered_df.groupby('CRASH_YEAR').size().reset_index()
            year_counts.columns = ['Year', 'Count']
            fig_line = px.line(
                year_counts, 
                x='Year', 
                y='Count',
                title='📈 Crashes Over Time',
                labels={'Count': 'Number of Crashes', 'Year': 'Year'},
                markers=True
            )
            fig_line.update_traces(line_color='#3498db', line_width=3, marker_size=8)
            fig_line.update_layout(
                template='plotly_white',
                height=400,
                margin=dict(l=20, r=20, t=60, b=20)
            )
            visualizations.append(
                html.Div([
                    dcc.Graph(figure=fig_line)
                ], style={
                    'marginBottom': '30px',
                    'backgroundColor': 'white',
                    'padding': '20px',
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 10px rgba(0,0,0,0.1)'
                })
            )
        except Exception as e:
            print(f"Error creating time series chart: {e}")
    
    # 3. Injuries and Fatalities Trends
    if 'CRASH_YEAR' in filtered_df.columns:
        try:
            if 'TOTAL_INJURED' in filtered_df.columns and 'TOTAL_KILLED' in filtered_df.columns:
                year_trends = filtered_df.groupby('CRASH_YEAR').agg({
                    'TOTAL_INJURED': 'sum',
                    'TOTAL_KILLED': 'sum'
                }).reset_index()
                
                fig_trends = go.Figure()
                fig_trends.add_trace(go.Scatter(
                    x=year_trends['CRASH_YEAR'],
                    y=year_trends['TOTAL_INJURED'],
                    name='Injured',
                    line=dict(color='#f39c12', width=3),
                    mode='lines+markers'
                ))
                fig_trends.add_trace(go.Scatter(
                    x=year_trends['CRASH_YEAR'],
                    y=year_trends['TOTAL_KILLED'] * 100,  # Scale for visibility
                    name='Killed (×100)',
                    line=dict(color='#e74c3c', width=3),
                    mode='lines+markers'
                ))
                fig_trends.update_layout(
                    title='📉 Injuries and Fatalities Over Time',
                    xaxis_title='Year',
                    yaxis_title='Count',
                    template='plotly_white',
                    height=400,
                    margin=dict(l=20, r=20, t=60, b=20),
                    legend=dict(x=0.02, y=0.98)
                )
                visualizations.append(
                    html.Div([
                        dcc.Graph(figure=fig_trends)
                    ], style={
                        'marginBottom': '30px',
                        'backgroundColor': 'white',
                        'padding': '20px',
                        'borderRadius': '10px',
                        'boxShadow': '0 2px 10px rgba(0,0,0,0.1)'
                    })
                )
        except Exception as e:
            print(f"Error creating trends chart: {e}")
    
    # 4. Pie Chart: Injury Type Distribution
    try:
        injury_data = []
        if 'NUMBER_OF_PEDESTRIANS_INJURED' in filtered_df.columns:
            pedestrian_count = ((filtered_df['NUMBER_OF_PEDESTRIANS_INJURED'] > 0) | 
                               (filtered_df['NUMBER_OF_PEDESTRIANS_KILLED'] > 0)).sum()
            if pedestrian_count > 0:
                injury_data.append({'Type': 'Pedestrian', 'Count': pedestrian_count})
        
        if 'NUMBER_OF_CYCLIST_INJURED' in filtered_df.columns:
            cyclist_count = ((filtered_df['NUMBER_OF_CYCLIST_INJURED'] > 0) |
                            (filtered_df['NUMBER_OF_CYCLIST_KILLED'] > 0)).sum()
            if cyclist_count > 0:
                injury_data.append({'Type': 'Cyclist', 'Count': cyclist_count})
        
        if 'NUMBER_OF_MOTORIST_INJURED' in filtered_df.columns:
            motorist_count = ((filtered_df['NUMBER_OF_MOTORIST_INJURED'] > 0) |
                             (filtered_df['NUMBER_OF_MOTORIST_KILLED'] > 0)).sum()
            if motorist_count > 0:
                injury_data.append({'Type': 'Motorist', 'Count': motorist_count})
        
        if injury_data:
            injury_df = pd.DataFrame(injury_data)
            fig_pie = px.pie(
                injury_df, 
                values='Count', 
                names='Type',
                title='🥧 Injury Type Distribution',
                color_discrete_map={
                    'Pedestrian': '#3498db',
                    'Cyclist': '#27ae60',
                    'Motorist': '#e74c3c'
                }
            )
            fig_pie.update_layout(
                template='plotly_white',
                height=400,
                margin=dict(l=20, r=20, t=60, b=20)
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            visualizations.append(
                html.Div([
                    dcc.Graph(figure=fig_pie)
                ], style={
                    'marginBottom': '30px',
                    'backgroundColor': 'white',
                    'padding': '20px',
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 10px rgba(0,0,0,0.1)'
                })
            )
    except Exception as e:
        print(f"Error creating pie chart: {e}")
    
    # 5. Heatmap: Crashes by Hour and Weekday
    if 'CRASH_HOUR' in filtered_df.columns and 'CRASH_WEEKDAY' in filtered_df.columns:
        try:
            hour_weekday = filtered_df.groupby(['CRASH_HOUR', 'CRASH_WEEKDAY']).size().reset_index()
            hour_weekday.columns = ['Hour', 'Weekday', 'Count']
            if len(hour_weekday) > 0:
                pivot_table = hour_weekday.pivot(index='Weekday', columns='Hour', values='Count').fillna(0)
                fig_heatmap = px.imshow(
                    pivot_table,
                    labels=dict(x='Hour of Day', y='Weekday', color='Number of Crashes'),
                    title='🔥 Crashes by Hour and Weekday',
                    color_continuous_scale='Reds',
                    aspect='auto'
                )
                fig_heatmap.update_layout(
                    template='plotly_white',
                    height=500,
                    margin=dict(l=20, r=20, t=60, b=20)
                )
                visualizations.append(
                    html.Div([
                        dcc.Graph(figure=fig_heatmap)
                    ], style={
                        'marginBottom': '30px',
                        'backgroundColor': 'white',
                        'padding': '20px',
                        'borderRadius': '10px',
                        'boxShadow': '0 2px 10px rgba(0,0,0,0.1)'
                    })
                )
        except Exception as e:
            print(f"Error creating heatmap: {e}")
    
    # 6. Map: Crash Locations (NYC Map)
    if 'LATITUDE' in filtered_df.columns and 'LONGITUDE' in filtered_df.columns:
        try:
            map_df = filtered_df[
                filtered_df['LATITUDE'].notna() & 
                filtered_df['LONGITUDE'].notna() &
                (filtered_df['LATITUDE'] != 0) &
                (filtered_df['LONGITUDE'] != 0)
            ].copy()
            
            if len(map_df) > 0:
                # Sample for performance if too many points
                max_points = 2000
                if len(map_df) > max_points:
                    map_df = map_df.sample(n=max_points, random_state=42)
                
                # Add size based on severity
                if 'TOTAL_INJURED' in map_df.columns:
                    map_df['size'] = map_df['TOTAL_INJURED'] + map_df.get('TOTAL_KILLED', 0) * 10 + 1
                else:
                    map_df['size'] = 3
                
                fig_map = px.scatter_mapbox(
                    map_df,
                    lat='LATITUDE',
                    lon='LONGITUDE',
                    size='size',
                    hover_data=['BOROUGH', 'CRASH_YEAR', 'TOTAL_INJURED'] if 'TOTAL_INJURED' in map_df.columns else ['BOROUGH', 'CRASH_YEAR'],
                    color_discrete_sequence=['#e74c3c'],
                    zoom=10,
                    height=600,
                    title='🗺️ Crash Locations Map (NYC)'
                )
                fig_map.update_layout(
                    mapbox_style='open-street-map',
                    margin=dict(l=0, r=0, t=40, b=0),
                    mapbox=dict(
                        center=dict(lat=40.7128, lon=-74.0060)  # NYC coordinates
                    )
                )
                fig_map.update_traces(marker=dict(sizemode='diameter', sizeref=2))
                visualizations.append(
                    html.Div([
                        dcc.Graph(figure=fig_map)
                    ], style={
                        'marginBottom': '30px',
                        'backgroundColor': 'white',
                        'padding': '20px',
                        'borderRadius': '10px',
                        'boxShadow': '0 2px 10px rgba(0,0,0,0.1)'
                    })
                )
        except Exception as e:
            print(f"Error creating map: {e}")
    
    # 7. Bar Chart: Top Contributing Factors
    if 'CONTRIBUTING_FACTOR_VEHICLE_1' in filtered_df.columns:
        try:
            factors = pd.concat([
                filtered_df['CONTRIBUTING_FACTOR_VEHICLE_1'],
                filtered_df['CONTRIBUTING_FACTOR_VEHICLE_2']
            ]).dropna()
            factors = factors[factors != 'Unspecified']
            
            if len(factors) > 0:
                factor_counts = factors.value_counts().head(10).reset_index()
                factor_counts.columns = ['Factor', 'Count']
                fig_factors = px.bar(
                    factor_counts, 
                    x='Count', 
                    y='Factor',
                    orientation='h',
                    title='⚠️ Top 10 Contributing Factors',
                    labels={'Count': 'Number of Crashes', 'Factor': 'Contributing Factor'},
                    color='Count',
                    color_continuous_scale='Oranges'
                )
                fig_factors.update_layout(
                    template='plotly_white',
                    height=500,
                    margin=dict(l=150, r=20, t=60, b=20),
                    yaxis={'categoryorder': 'total ascending'}
                )
                visualizations.append(
                    html.Div([
                        dcc.Graph(figure=fig_factors)
                    ], style={
                        'marginBottom': '30px',
                        'backgroundColor': 'white',
                        'padding': '20px',
                        'borderRadius': '10px',
                        'boxShadow': '0 2px 10px rgba(0,0,0,0.1)'
                    })
                )
        except Exception as e:
            print(f"Error creating contributing factors chart: {e}")
    
    # 8. Monthly Pattern Chart
    if 'CRASH_MONTH' in filtered_df.columns and len(filtered_df['CRASH_MONTH'].dropna()) > 0:
        try:
            month_counts = filtered_df.groupby('CRASH_MONTH').size().reset_index()
            month_counts.columns = ['Month', 'Count']
            month_order = ['January', 'February', 'March', 'April', 'May', 'June',
                          'July', 'August', 'September', 'October', 'November', 'December']
            # If month is numeric, map to names
            if month_counts['Month'].dtype in ['int64', 'float64']:
                month_map = {i+1: name for i, name in enumerate(month_order)}
                month_counts['Month'] = month_counts['Month'].map(month_map)
            month_counts = month_counts.sort_values('Month', key=lambda x: x.map(
                {name: i for i, name in enumerate(month_order)}))
            
            fig_month = px.bar(
                month_counts,
                x='Month',
                y='Count',
                title='📅 Crashes by Month',
                labels={'Count': 'Number of Crashes', 'Month': 'Month'},
                color='Count',
                color_continuous_scale='Viridis'
            )
            fig_month.update_layout(
                template='plotly_white',
                height=400,
                margin=dict(l=20, r=20, t=60, b=20),
                xaxis={'tickangle': -45}
            )
            visualizations.append(
                html.Div([
                    dcc.Graph(figure=fig_month)
                ], style={
                    'marginBottom': '30px',
                    'backgroundColor': 'white',
                    'padding': '20px',
                    'borderRadius': '10px',
                    'boxShadow': '0 2px 10px rgba(0,0,0,0.1)'
                })
            )
        except Exception as e:
            print(f"Error creating monthly chart: {e}")
    
    # If no visualizations were created, show message
    if not visualizations:
        return html.Div([
            html.Div([
                html.H3("⚠️ Unable to Create Visualizations", style={'color': '#e74c3c'}),
                html.P("The data may be missing required columns or there may be an issue with the dataset.",
                      style={'color': '#7f8c8d'})
            ], style={
                'textAlign': 'center',
                'padding': '50px',
                'backgroundColor': 'white',
                'borderRadius': '10px',
                'boxShadow': '0 2px 10px rgba(0,0,0,0.1)'
            })
        ])
    
    return visualizations

# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == '__main__':
    app.run_server(debug=True, host='0.0.0.0', port=8080)
