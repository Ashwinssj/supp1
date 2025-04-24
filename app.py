# app.py - Main Flask application

import os
import pandas as pd
import numpy as np
import json
from flask import Flask, request, render_template, jsonify, session
from werkzeug.utils import secure_filename
import uuid
import plotly
import plotly.express as px
import plotly.graph_objects as go
import google.generativeai as genai
from dotenv import load_dotenv
import data_processor

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Update Flask initialization to specify static folder
app = Flask(__name__, static_folder='styles', static_url_path='/static')
app.secret_key = os.getenv('SECRET_KEY', 'development-key')
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['ALLOWED_EXTENSIONS'] = {'csv'}

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

# Add session configuration
app.config.update(
    SESSION_COOKIE_SECURE=True,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax'
)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file and allowed_file(file.filename):
        # Generate unique filename
        filename = str(uuid.uuid4()) + secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Process the uploaded file
            processed_data = data_processor.process_csv(filepath)
            
            # Store processed data in session
            session['processed_data_path'] = processed_data['processed_file']
            session['data_summary'] = processed_data['summary']
            
            return jsonify({
                'success': True,
                'summary': processed_data['summary'],
                'message': 'File successfully uploaded and processed'
            })
        except Exception as e:
            return jsonify({'error': str(e)}), 500
    
    return jsonify({'error': 'File type not allowed'}), 400

@app.route('/dashboard')
def dashboard():
    if 'processed_data_path' not in session:
        return render_template('index.html', error="Please upload data first")
    
    return render_template('dashboard.html', summary=session.get('data_summary', {}))

@app.route('/get_route_map')
def get_route_map():
    if 'processed_data_path' not in session:
        return jsonify({'error': 'No data available'}), 400
        
    try:
        df = pd.read_csv(session['processed_data_path'])
        
        # Create route map using processed data
        map_data = data_processor.generate_route_map(df)
        
        return jsonify(map_data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_analytics_charts')
def get_analytics_charts():
    if 'processed_data_path' not in session:
        return jsonify({'error': 'No data available'}), 400
        
    try:
        df = pd.read_csv(session['processed_data_path'])
        
        # Generate various supply chain analytics charts
        inventory_chart = create_inventory_chart(df)
        delivery_time_chart = create_delivery_time_chart(df)
        cost_analysis_chart = create_cost_analysis_chart(df)
        supplier_performance_chart = create_supplier_performance_chart(df)
        
        return jsonify({
            'inventory_chart': inventory_chart,
            'delivery_time_chart': delivery_time_chart,
            'cost_analysis_chart': cost_analysis_chart,
            'supplier_performance_chart': supplier_performance_chart
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/ask_ai', methods=['POST'])
def ask_ai():
    if 'processed_data_path' not in session:
        return jsonify({'error': 'No data available'}), 400
    
    try:
        query = request.json.get('query', '')
        if not query:
            return jsonify({'error': 'Empty query'}), 400
            
        df = pd.read_csv(session['processed_data_path'])
        
        # Prepare context about the data for the AI
        data_summary = session.get('data_summary', {})
        context = f"""
        Analyzing supply chain data with the following characteristics:
        - Number of records: {data_summary.get('record_count', 'Unknown')}
        - Date range: {data_summary.get('date_range', 'Unknown')}
        - Suppliers: {', '.join(data_summary.get('suppliers', ['Unknown']))}
        - Products: {', '.join(data_summary.get('products', ['Unknown']))}
        
        The data contains columns: {', '.join(df.columns.tolist())}
        
        Here's a sample of the data:
        {df.head(5).to_string()}
        
        Statistical summary:
        {df.describe().to_string()}
        """
        
        # Get response from Gemini API
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(f"{context}\n\nUser query: {query}")
        
        return jsonify({'response': response.text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/get_details/<chart_type>/<item_id>')
def get_details(chart_type, item_id):
    if 'processed_data_path' not in session:
        return jsonify({'error': 'No data available'}), 400
        
    try:
        df = pd.read_csv(session['processed_data_path'])
        
        # Generate detailed analysis based on what was clicked
        if chart_type == 'supplier':
            details = data_processor.get_supplier_details(df, item_id)
        elif chart_type == 'product':
            details = data_processor.get_product_details(df, item_id)
        elif chart_type == 'route':
            details = data_processor.get_route_details(df, item_id)
        elif chart_type == 'warehouse':
            details = data_processor.get_warehouse_details(df, item_id)
        else:
            return jsonify({'error': 'Invalid chart type'}), 400
            
        return jsonify(details)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Helper functions for creating charts
def create_inventory_chart(df):
    try:
        # Group data by product and location
        inventory_df = df.groupby(['product', 'warehouse'])['quantity'].sum().reset_index()
        
        # Create stacked bar chart for inventory levels
        fig = px.bar(
            inventory_df, 
            x='product', 
            y='quantity', 
            color='warehouse',
            title='Inventory Levels by Product and Warehouse',
            labels={'product': 'Product', 'quantity': 'Quantity', 'warehouse': 'Warehouse'}
        )
        
        return json.loads(plotly.io.to_json(fig))
    except Exception as e:
        print(f"Error creating inventory chart: {str(e)}")
        return {}

def create_delivery_time_chart(df):
    try:
        # Check if necessary columns exist
        if 'order_date' in df.columns and 'delivery_date' in df.columns:
            # Convert date columns to datetime
            df['order_date'] = pd.to_datetime(df['order_date'])
            df['delivery_date'] = pd.to_datetime(df['delivery_date'])
            
            # Calculate delivery time in days
            df['delivery_time'] = (df['delivery_date'] - df['order_date']).dt.days
            
            # Group by route or supplier
            delivery_df = df.groupby('supplier')['delivery_time'].mean().reset_index()
            
            # Create bar chart for average delivery times
            fig = px.bar(
                delivery_df,
                x='supplier',
                y='delivery_time',
                title='Average Delivery Time by Supplier',
                labels={'supplier': 'Supplier', 'delivery_time': 'Average Delivery Time (days)'}
            )
            
            return json.loads(plotly.io.to_json(fig))
    except Exception as e:
        print(f"Error creating delivery time chart: {str(e)}")
    
    # Return empty if columns don't exist or there's an error
    return {}

def create_cost_analysis_chart(df):
    try:
        # Determine which cost column to use (cost or price)
        cost_column = 'cost' if 'cost' in df.columns else 'price' if 'price' in df.columns else None
        
        if cost_column and 'product' in df.columns:
            # Check if we have category/label information
            category_column = None
            if 'category' in df.columns:
                category_column = 'category'
            elif 'label' in df.columns:
                category_column = 'label'
            
            # If we have category information, create a more detailed chart
            if category_column:
                # Group by category and product
                cost_df = df.groupby([category_column, 'product'])[cost_column].sum().reset_index()
                
                # Create a sunburst chart for hierarchical cost distribution
                fig = px.sunburst(
                    cost_df,
                    path=[category_column, 'product'],
                    values=cost_column,
                    title=f'{cost_column.title()} Distribution by Category and Product',
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                
                fig.update_layout(
                    margin=dict(t=30, b=10, l=10, r=10),
                    uniformtext=dict(minsize=10, mode='hide')
                )
            else:
                # Group by product only
                cost_df = df.groupby('product')[cost_column].sum().reset_index()
                
                # Sort by cost for better visualization
                cost_df = cost_df.sort_values(by=cost_column, ascending=False)
                
                # Create pie chart for cost distribution
                fig = px.pie(
                    cost_df,
                    values=cost_column,
                    names='product',
                    title=f'{cost_column.title()} Distribution by Product',
                    hole=0.4,  # Create a donut chart for better visualization
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                
                # Add total cost in the center
                total_cost = cost_df[cost_column].sum()
                fig.update_layout(
                    annotations=[dict(
                        text=f'Total<br>${total_cost:,.2f}',
                        x=0.5, y=0.5,
                        font_size=15,
                        showarrow=False
                    )]
                )
            
            # Add warehouse filter if warehouse column exists
            if 'warehouse' in df.columns:
                warehouses = df['warehouse'].unique()
                buttons = []
                
                # Add button for all warehouses
                buttons.append(dict(
                    method='update',
                    label='All Warehouses',
                    args=[{'visible': [True] * len(fig.data)}]
                ))
                
                # This is a placeholder for warehouse filtering functionality
                # In a real implementation, we would need to create separate traces for each warehouse
                # and toggle their visibility with these buttons
                
                fig.update_layout(
                    updatemenus=[dict(
                        type='dropdown',
                        showactive=True,
                        buttons=buttons,
                        x=0.1,
                        y=1.15,
                        xanchor='left',
                        yanchor='top'
                    )]
                )
            
            return json.loads(plotly.io.to_json(fig))
    except Exception as e:
        print(f"Error creating cost analysis chart: {str(e)}")
    
    # Return empty if columns don't exist or there's an error
    return {}

def create_supplier_performance_chart(df):
    try:
        # Create a composite performance score
        if all(col in df.columns for col in ['supplier', 'on_time_delivery', 'quality_score']):
            supplier_df = df.groupby('supplier').agg({
                'on_time_delivery': 'mean',
                'quality_score': 'mean'
            }).reset_index()
            
            # Create radar chart for supplier performance
            fig = go.Figure()
            
            for idx, row in supplier_df.iterrows():
                fig.add_trace(go.Scatterpolar(
                    r=[row['on_time_delivery'], row['quality_score'], 
                       (row['on_time_delivery'] + row['quality_score'])/2],
                    theta=['On-time Delivery', 'Quality Score', 'Overall Score'],
                    fill='toself',
                    name=row['supplier']
                ))
            
            fig.update_layout(
                polar=dict(
                    radialaxis=dict(visible=True, range=[0, 1])
                ),
                title='Supplier Performance Analysis'
            )
            
            return json.loads(plotly.io.to_json(fig))
    except Exception as e:
        print(f"Error creating supplier performance chart: {str(e)}")
    
    # Return empty if columns don't exist or there's an error
    return {}

# Add this error handler at the bottom of the file
@app.errorhandler(404)
def not_found(error):
    return render_template('error.html'), 404

if __name__ == '__main__':
    app.run(debug=True)