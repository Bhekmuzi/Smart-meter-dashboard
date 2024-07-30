# 2024-07-29

import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from datetime import datetime, timedelta
import dash_bootstrap_components as dbc
from pymongo import MongoClient
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv('variables.env')

# MongoDB Connection URI and Database Name from .env file
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DATABASE = os.getenv("MONGODB_DATABASE")
WATER_COLLECTION = os.getenv("MONGODB_COLLECTION")
ELECTRICITY_COLLECTION = os.getenv("MONGODB_COLLECTION_ELECTRICITY")
ELECTR_COLLECTION = os.getenv("MONGODB_COLLECTION_ELECTR")

# Connect to MongoDB using environment variables
client = MongoClient(MONGODB_URI)
db = client[MONGODB_DATABASE]
water_collection = db[WATER_COLLECTION]
electricity_collection = db[ELECTRICITY_COLLECTION]
electr_collection = db[ELECTR_COLLECTION]

# Determine the activity level based on active score and norms
def determine_activity_level(active_score, low_norm, norm_score, high_norm):
    if active_score == 0.0:
        return 'Unknown', 'gray'
    if active_score <= low_norm:
        return 'Abnormal', 'red'
    elif low_norm < active_score <= norm_score:
        return 'Low', 'yellow'
    elif norm_score < active_score <= high_norm:
        return 'Active', 'blue'
    elif active_score > high_norm:
        return 'High', 'green'
    else:
        return 'Unknown', 'gray'
    
# Determine the regularity level based on correlation coefficient
def determine_regularity_level(corr_coef):
    if corr_coef == 0.0:
        return 'Unknown', 'gray'
    elif corr_coef < 0.30:
        return 'Abnormal', 'red'
    elif 0.30 <= corr_coef < 0.50:
        return 'Low', 'yellow'
    elif 0.50 <= corr_coef < 0.70:
        return 'Normal', 'blue'
    elif corr_coef >= 0.70:
        return 'High', 'green'
    else:
        return 'Unknown', 'gray'

# Determine the overall status based on the lowest level of activity and regularity
def determine_status(activity_level, regularity_level):
    if activity_level == 'Unknown' or regularity_level == 'Unknown':
        return 'Unknown', 'gray'
        
    levels = {'Abnormal': 1, 'Low': 2, 'Normal': 3, 'Active': 4, 'High': 5}
    lowest_level = min(levels[activity_level], levels[regularity_level])

    if lowest_level == 1:
        return 'Attention', 'red'
    elif lowest_level == 2:
        return 'Normal', 'yellow'
    elif lowest_level == 3:
        return 'Normal', 'blue'
    elif lowest_level == 4:
        return 'Active', 'blue'
    elif lowest_level == 5:
        return 'High', 'green'
    else:
        return 'Unknown', 'gray'

def get_data_for_date_and_home(date, home_id):
    try:
        # Convert the date to the correct formats
        water_date = date
        electricity_date = datetime.strptime(date, '%Y-%m-%d').strftime('%Y/%m/%d')
        
        # Fetch data from MongoDB
        water_data = water_collection.find_one({'date': water_date, 'home_id': home_id})
        electricity_data = electricity_collection.find_one({'date': electricity_date, 'home_id': home_id})
        electr_data = electr_collection.find_one({'date': water_date, 'home_id': "home2127"})
        
        # Check if both water and electricity data exist
        if water_data and electricity_data:
            return {
                'water_usage': water_data.get('usage', []),
                'water_norm': water_data.get('four_week_usage_norm', []),
                'water_consumption': water_data.get('water_consumption', []),
                'water_active_score': round(water_data.get('active_score', 0.0), 3),
                'water_corr_coef': round(water_data.get('correlation_coefficient', 0.0), 3),
                'water_low_norm': round(water_data.get('low_norm', 0.0), 3),
                'water_norm_score': round(water_data.get('norm_active_score', 0.0), 3),
                'water_high_norm': round(water_data.get('high_norm', 0.0), 3),
                
                'electricity_usage': electricity_data.get('appliance_usage', []),
                'electricity_norm': electricity_data.get('four_week_active_score', []),
                'electricity_consumption': electricity_data.get('power', []),
                'electricity_active_score': round(electricity_data.get('active_score', 0.0), 3),
                'electricity_corr_coef': round(electricity_data.get('correlation_coefficient', 0.0), 3),
                'electricity_low_norm': round(electricity_data.get('low_norm', 0.0), 3),
                'electricity_norm_score': round(electricity_data.get('norm_active_score', 0.0), 3),
                'electricity_high_norm': round(electricity_data.get('high_norm', 0.0), 3)
            }
        elif water_data:
            # Handle case where only water data exists
            return {
                'water_usage': water_data.get('usage', []),
                'water_norm': water_data.get('four_week_usage_norm', []),
                'water_consumption': water_data.get('water_consumption', []),
                'water_active_score': round(water_data.get('active_score', 0.0), 3),
                'water_corr_coef': round(water_data.get('correlation_coefficient', 0.0), 3),
                'water_low_norm': round(water_data.get('low_norm', 0.0), 3),
                'water_norm_score': round(water_data.get('norm_active_score', 0.0), 3),
                'water_high_norm': round(water_data.get('high_norm', 0.0), 3),
                
                'electricity_usage': [], 'electricity_norm': [],
                'electricity_consumption': [], 'electricity_active_score': 0.0,
                'electricity_corr_coef': 0.0, 'electricity_low_norm': 0.0,
                'electricity_norm_score': 0.0, 'electricity_high_norm': 0.0
            }
        elif electricity_data:
            # Handle case where only electricity data exists
            return {
                'water_usage': [], 'water_norm': [],
                'water_consumption': [], 'water_active_score': 0.0,
                'water_corr_coef': 0.0, 'water_low_norm': 0.0,
                'water_norm_score': 0.0, 'water_high_norm': 0.0,
                
                'electricity_usage': electricity_data.get('appliance_usage', []),
                'electricity_norm': electricity_data.get('four_week_active_score', []),
                'electricity_consumption': electricity_data.get('power', []),
                'electricity_active_score': round(electricity_data.get('active_score', 0.0), 3),
                'electricity_corr_coef': round(electricity_data.get('correlation_coefficient', 0.0), 3),
                'electricity_low_norm': round(electricity_data.get('low_norm', 0.0), 3),
                'electricity_norm_score': round(electricity_data.get('norm_active_score', 0.0), 3),
                'electricity_high_norm': round(electricity_data.get('high_norm', 0.0), 3)
            }
        else:
            # Handle case where neither data exists
            return {
                'water_usage': [], 'water_norm': [],
                'water_consumption': [], 'water_active_score': 0.0,
                'water_corr_coef': 0.0, 'water_low_norm': 0.0,
                'water_norm_score': 0.0, 'water_high_norm': 0.0,
                
                'electricity_usage': [], 'electricity_norm': [],
                'electricity_consumption': [], 'electricity_active_score': 0.0,
                'electricity_corr_coef': 0.0, 'electricity_low_norm': 0.0,
                'electricity_norm_score': 0.0, 'electricity_high_norm': 0.0
            }
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

# Calculate previous day's date
previous_day = datetime.now().date() - timedelta(days=1)

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container(fluid=True, children=[
    dbc.Row(
        [
            dbc.Col(
                width=3,
                className='custom-sidebar',  # Define .custom-sidebar in your CSS file
                # style={'margin-left': '10px', 'margin-right': '10px'},  # Adjust margin-left as needed
                children=[
                    # Sidebar for date, homeID, and usage pickers
                    dbc.Button(">", id="toggle-button", color="primary", className="mb-3"),
                    dbc.Collapse(
                        id="collapse",
                        is_open=False,
                        children=[
                            html.H2('Date Picker'),
                            html.Button('<< Prev', id='prev-day-button', n_clicks=0, style={'marginRight': '10px'}),
                            dcc.DatePickerSingle(
                                id='date-picker-sidebar',
                                date=previous_day,
                                display_format='YYYY-MM-DD'
                            ),
                            html.Button('Next >>', id='next-day-button', n_clicks=0),
                            html.H2('HomeID Picker'),
                            dcc.Dropdown(
                                id='home-id-picker-sidebar',
                                options=[
                                    {'label': 'Home_2127', 'value': 'Home_2127'}#,
                                    # {'label': 'Home_2128', 'value': 'Home_2128'},
                                    # {'label': 'Home_2129', 'value': 'Home_2129'}
                                ],
                                value='Home_2127',
                                style={'width': '100%', 'marginTop': '10px'}
                            ),
                            html.H2('Usage Picker'),
                            dcc.Dropdown(
                                id='usage-picker-sidebar',
                                options=[
                                    {'label': 'Water Usage', 'value': 'water'},
                                    {'label': 'Electricity Usage', 'value': 'electricity'}
                                ],
                                value='water'
                            ),
                        ],
                    ),
                ]
            ),
            dbc.Col(
                id="right-section",
                width=9,
                children=[
                    
                    # Main section for displaying figures
                    html.H2('Smart Meter Dashboard', className='text-center mb-4'),
                        html.Div(
                            children=[
                                # Main section for displaying figures
                                html.Div(id='selected-info', className='mb-4'),
                                
                                # Selected homeID and date
                                # html.Div(id='selected-home-date', className='text-center mb-4'),

                                # Status and Shape
                                html.Div(children=[
                                    html.P(id='status', style={'fontSize': 18}),
                                    dcc.Graph(                                        
                                        id='status-rect',
                                        config={'displayModeBar': False}
                                    )
                                ], style={'display': 'inline-block', 'verticalAlign': 'middle', 'marginRight': '10px'}),

                                # Activity Level and Shape
                                html.Div(children=[
                                    html.P(id='activity-level', style={'fontSize': 18}),
                                    dcc.Graph(
                                        id='activity-circle',
                                        config={'displayModeBar': False}
                                    )
                                ], style={'display': 'inline-block', 'verticalAlign': 'middle', 'marginRight': '10px'}),
                                
                                # Regularity Level and Shape
                                html.Div(children=[
                                    html.P(id='regularity-level', style={'fontSize': 18}),
                                    dcc.Graph(
                                        id='regularity-circle',
                                        config={'displayModeBar': False}
                                    )
                                ], style={'display': 'inline-block', 'verticalAlign': 'middle', 'marginRight': '10px'}),
                            ],
                            
                            style={'textAlign': 'center', 'marginBottom': '20px'}
                        ),
                                
                    html.Div(id='usage-dashboard-water'),
                    html.Div(id='usage-dashboard-electricity'),
                    html.Div(id='usage-water-norm'),
                    html.Div(id='usage-electricity-norm'),
                    html.Div(id='water-consumption'),
                    html.Div(id='electricity-consumption')
                ]
            )
        ])
])

@app.callback(
    Output("collapse", "is_open"), Output("right-section", "width"),
    [Input("toggle-button", "n_clicks")],
    [State("collapse", "is_open"), State("right-section", "width")],
)



# def toggle_collapse(n, is_open, current_width):
#     if n:
#         is_open = not is_open
#         if is_open:
#             new_width = 9
#         else:
#             new_width = 12
#         return is_open, new_width
#     return is_open, current_width

def toggle_collapse(n, is_open, current_width):
    if n:
        if is_open:
            new_width = 12
        else:
            new_width = 9
        return not is_open, new_width
    return is_open, current_width


@app.callback(
    [Output('selected-info', 'children'), Output('selected-home-date', 'children')],
    [Input('home-id-picker-sidebar', 'value'), Input('date-picker-sidebar', 'date'), Input('usage-picker-sidebar', 'value')]
)

@app.callback(
    Output('date-picker-sidebar', 'date'),
    Input('prev-day-button', 'n_clicks'),
    Input('next-day-button', 'n_clicks'),
    State('date-picker-sidebar', 'date')
)
def update_selected_date(prev_clicks, next_clicks, selected_date):
    ctx = dash.callback_context
    if not ctx.triggered:
        button_id = None
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]

    date_obj = datetime.strptime(selected_date, '%Y-%m-%d')

    if button_id == 'prev-day-button':
        new_date = date_obj - timedelta(days=1)
    elif button_id == 'next-day-button':
        new_date = date_obj + timedelta(days=1)
    else:
        new_date = date_obj

    return new_date.strftime('%Y-%m-%d')
    

@app.callback(
    Output('date-output', 'children'),
    Input('date-picker', 'date')
)
def update_output(selected_date):
    return f"You have selected {selected_date}"
    
def update_selected_info(home_id, date, usage_picker_value):
    if home_id and date and usage_picker_value:
        selected_info = f"{home_id}     Date: {date}"
        return selected_info, html.H3(selected_info, className='text-center mb-4')
    return '', ''

# Callback to update graphs based on date and home ID selection
@app.callback(
    [Output('status', 'children'), Output('status-rect', 'figure'),
     Output('activity-level', 'children'), Output('activity-circle', 'figure'),
     Output('regularity-level', 'children'), Output('regularity-circle', 'figure'),
     Output('usage-dashboard-water', 'children'), Output('usage-dashboard-electricity', 'children'),
     Output('usage-water-norm', 'children'), Output('usage-electricity-norm', 'children'),
     Output('water-consumption', 'children'), Output('electricity-consumption', 'children')],
    [Input('usage-picker-sidebar', 'value'), Input('date-picker-sidebar', 'date'),
     Input('home-id-picker-sidebar', 'value')]
)

def update_usage_dashboard(selected_usage, selected_date, selected_home_id):
    if selected_date and selected_home_id:
        selected_date = datetime.strptime(selected_date, '%Y-%m-%d').strftime('%Y-%m-%d') 
                
        data = get_data_for_date_and_home(selected_date, selected_home_id)
        if data:
            water_usage = data['water_usage'] 
            water_usage_norm = data['water_norm']
            water_active_score = data['water_active_score']
            water_corr_coef = data['water_corr_coef']
            water_norm_score = data['water_norm_score']
            water_low_norm = data['water_low_norm']
            water_high_norm = data['water_high_norm']
            water_consumption = data['water_consumption']
            
            electricity_usage = data['electricity_usage']
            electricity_usage_norm = data['electricity_norm']
            electricity_active_score = data['electricity_active_score']
            electricity_corr_coef = data['electricity_corr_coef']
            electricity_norm_score = data['electricity_norm_score']
            electricity_low_norm = data['electricity_low_norm']
            electricity_high_norm = data['electricity_high_norm']
            electricity_consumption = data['electricity_consumption']

            # Determine water levels and status
            water_activity_level, water_activity_color = determine_activity_level(water_active_score, water_low_norm, water_norm_score, water_high_norm)
            water_regularity_level, water_regularity_color = determine_regularity_level(water_corr_coef)
            water_status, water_status_color = determine_status(water_activity_level, water_regularity_level)

            # Determine electricity levels and status
            electricity_activity_level, electricity_activity_color = determine_activity_level(electricity_active_score, electricity_low_norm, electricity_norm_score, electricity_high_norm)
            electricity_regularity_level, electricity_regularity_color = determine_regularity_level(electricity_corr_coef)
            electricity_status, electricity_status_color = determine_status(electricity_activity_level, electricity_regularity_level)

            # Generate x-axis labels for time from 00:00 to 23:45 with 15-minute intervals
            x_labels = [f"{hour:02}:{minute:02}" for hour in range(0, 24) for minute in range(0, 60, 15)]
            x_labels = x_labels[:len(water_usage)]  # Ensure labels match data length

            # Custom status, activity, and regularity figures
            water_status_text = 'Status' #f'Status: {status}'
            water_status_rect_figure = go.Figure(
                data=[go.Scatter(
                    x=[0], y=[0], text=[water_status],
                    mode='text',
                    textfont=dict(size=16, color=water_status_color)
                )],
                layout=go.Layout(
                    shapes=[
                        go.layout.Shape(
                            type="path",
                            path='M -0.5 -0.25 L 0.5 -0.25 Q 0.6 -0.25 0.6 -0.15 L 0.6 0.15 Q 0.6 0.25 0.5 0.25 L -0.5 0.25 Q -0.6 0.25 -0.6 0.15 L -0.6 -0.15 Q -0.6 -0.25 -0.5 -0.25 Z',
                            line=dict(color=water_status_color),
                            fillcolor='rgba(0,0,0,0)'
                        )
                    ],
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False),
                    height=80,
                    width=150,
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                )
            )

            water_activity_level_text = 'Activity Level' #f'Activity Level: {activity_level}'
            water_activity_circle_figure = go.Figure(
                data=[go.Scatter(
                    x=[0], y=[0], text=['AS'],
                    mode='text',
                    textfont=dict(size=16, color=water_activity_color)
                )],
                layout=go.Layout(
                    shapes=[
                        go.layout.Shape(
                            type='circle',
                            x0=-0.5, y0=-0.5,
                            x1=0.5, y1=0.5,
                            line=dict(color=water_activity_color),
                            fillcolor='rgba(0,0,0,0)'
                        )
                    ],
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False),
                    height=80,
                    width=80,
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                )
            )

            water_regularity_level_text = 'Regularity Level' # f'Regularity Level: {regularity_level}'
            water_regularity_circle_figure = go.Figure(
                data=[go.Scatter(
                    x=[0], y=[0], text=['CC'],
                    mode='text',
                    textfont=dict(size=16, color=water_regularity_color)
                )],
                layout=go.Layout(
                    shapes=[
                        go.layout.Shape(
                            type='circle',
                            x0=-0.5, y0=-0.5,
                            x1=0.5, y1=0.5,
                            line=dict(color=water_regularity_color),
                            fillcolor='rgba(0,0,0,0)'
                        )
                    ],
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False),
                    height=80,
                    width=80,
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                )
            )
          
            water_usage_graph = dcc.Graph(
                id='water-usage-graph',
                figure=go.Figure(
                    data=[go.Bar(x=x_labels, y=water_usage, name='Water Usage')],
                    layout=go.Layout(
                        title=f'Active Score: {water_active_score} | Corr Coef: {water_corr_coef}', 
                        xaxis={'title': 'Time', 'tickvals': x_labels, 'ticktext': x_labels}, 
                        yaxis={'title': 'Usage', 'range': [0, 1]},
                        # width='1200',
                        height=300
                    )
                )
            )

            water_usage_norm_graph = dcc.Graph(
                id='water-usage-norm-graph',
                figure=go.Figure(
                    data=[go.Bar(x=x_labels, y=water_usage_norm, name='Water Usage Norm')],
                    layout=go.Layout(
                        title=f'Low: {water_low_norm} | Norm: {water_norm_score} | High: {water_high_norm}',
                        xaxis={'title': 'Time'}, 
                        yaxis={
                            'title': 'Usage Norm',
                            'range': [0, 100]
                        },
                        # width=1500,
                        height=400
                    )
                )
            )

            water_consumption_graph = dcc.Graph(
                id='water-consumption-graph',
                figure=go.Figure(
                    data=[go.Bar(x=x_labels, y=water_consumption, name='Water consumption')],
                    layout=go.Layout(
                        title=f'Water consumption for Date: {selected_date}',
                        xaxis={'title': 'Time'}, 
                        yaxis={
                            'title': 'consumption',
                            'range': [0, 6]
                        },
                        # width=1500,
                        height=400
                    )
                )
            )
            
            # Custom status, activity, and regularity figures
            electricity_status_text = 'Status' #f'Status: {status}'
            electricity_status_rect_figure = go.Figure(
                data=[go.Scatter(
                    x=[0], y=[0], text=[electricity_status],
                    mode='text',
                    textfont=dict(size=16, color=electricity_status_color)
                )],
                layout=go.Layout(
                    shapes=[
                        go.layout.Shape(
                            type="path",
                            path='M -0.5 -0.25 L 0.5 -0.25 Q 0.6 -0.25 0.6 -0.15 L 0.6 0.15 Q 0.6 0.25 0.5 0.25 L -0.5 0.25 Q -0.6 0.25 -0.6 0.15 L -0.6 -0.15 Q -0.6 -0.25 -0.5 -0.25 Z',
                            line=dict(color=electricity_status_color),
                            fillcolor='rgba(0,0,0,0)'
                        )
                    ],
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False),
                    height=80,
                    width=150,
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                )
            )

            electricity_usage_graph = dcc.Graph(
                id='electricity-usage-graph',
                figure=go.Figure(
                    data=[go.Bar(x=x_labels, y=electricity_usage, name='Electricity Usage')],
                    layout=go.Layout(
                        title=f'Active Score: {electricity_active_score} | Corr Coef: {electricity_corr_coef}', 
                        xaxis={'title': 'Time'}, 
                        yaxis={
                            'title': 'Usage',
                            'range': [0, 1]
                        },
                        # width=1500,
                        height=300
                    )
                )
            )

            electricity_activity_level_text = 'Activity Level' #f'Activity Level: {activity_level}'
            electricity_activity_circle_figure = go.Figure(
                data=[go.Scatter(
                    x=[0], y=[0], text=['AS'],
                    mode='text',
                    textfont=dict(size=16, color=electricity_activity_color)
                )],
                layout=go.Layout(
                    shapes=[
                        go.layout.Shape(
                            type='circle',
                            x0=-0.5, y0=-0.5,
                            x1=0.5, y1=0.5,
                            line=dict(color=electricity_activity_color),
                            fillcolor='rgba(0,0,0,0)'
                        )
                    ],
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False),
                    height=80,
                    width=80,
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                )
            )

            electricity_regularity_level_text = 'Regularity Level' # f'Regularity Level: {regularity_level}'
            electricity_regularity_circle_figure = go.Figure(
                data=[go.Scatter(
                    x=[0], y=[0], text=['CC'],
                    mode='text',
                    textfont=dict(size=16, color=electricity_regularity_color)
                )],
                layout=go.Layout(
                    shapes=[
                        go.layout.Shape(
                            type='circle',
                            x0=-0.5, y0=-0.5,
                            x1=0.5, y1=0.5,
                            line=dict(color=electricity_regularity_color),
                            fillcolor='rgba(0,0,0,0)'
                        )
                    ],
                    xaxis=dict(visible=False),
                    yaxis=dict(visible=False),
                    height=80,
                    width=80,
                    margin=dict(l=20, r=20, t=20, b=20),
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                )
            )

            electricity_usage_norm_graph = dcc.Graph(
                id='electricity-usage-norm-graph',
                figure=go.Figure(
                    data=[go.Bar(x=x_labels, y=electricity_usage_norm, name='Electricity Usage Norm')],
                    layout=go.Layout(                            
                        title=f'Low: {electricity_low_norm} | Norm: {electricity_norm_score} | High: {electricity_high_norm}',
                        xaxis={'title': 'Time'}, 
                        yaxis={
                            'title': 'Usage Norm',
                            'range': [0, 100]
                        },
                        # width=1500,
                        height=400
                    )
                )
            )

            electricity_consumption_graph = dcc.Graph(
                id='electricity-consumption-graph',
                figure=go.Figure(
                    data=[go.Bar(x=x_labels, y=electricity_consumption, name='Electricity Consumption')],
                    layout=go.Layout(                            
                        title=f'Electricity consumption for Date: {selected_date}',
                        xaxis={'title': 'Time'}, 
                        yaxis={
                            'title': 'Consumption',
                            'range': [0, 6]
                        },
                        # width=1500,
                        height=400
                    )
                )
            )

            if selected_usage == 'water':
                return (
                    water_status_text, water_status_rect_figure,
                    water_activity_level_text, water_activity_circle_figure,
                    water_regularity_level_text, water_regularity_circle_figure,
                    html.H3('Water Usage', className='text-center mb-4'),
                    water_usage_graph,
                    html.H3('Water Usage Norm', className='text-center mb-4'),
                    water_usage_norm_graph,
                    html.H3('Water consumption', className='text-center mb-4'),
                    water_consumption_graph
                )
            elif selected_usage == 'electricity':
                return (
                    electricity_status_text, electricity_status_rect_figure,
                    electricity_activity_level_text, electricity_activity_circle_figure,
                    electricity_regularity_level_text, electricity_regularity_circle_figure,
                    html.H3('Electricity Usage', className='text-center mb-4'),
                    electricity_usage_graph,
                    html.H3('Electricity Usage Norm', className='text-center mb-4'),
                    electricity_usage_norm_graph,
                    html.H3('Electricity consumption', className='text-center mb-4'),
                    electricity_consumption_graph
                )

    return html.Div(), html.Div(), html.Div(), html.Div(), html.Div(), html.Div()

if __name__ == '__main__':
    app.run_server(debug=True)
