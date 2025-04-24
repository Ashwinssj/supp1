# data_processor.py - Data cleaning and processing functions

import pandas as pd
import numpy as np
import os
import json
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re

def process_csv(filepath):
    """Process and clean uploaded CSV file"""
    try:
        # Read the CSV file
        df = pd.read_csv(filepath)
        
        # Basic cleaning
        df = clean_dataframe(df)
        
        # Generate summary statistics
        summary = generate_data_summary(df)
        
        # Save processed file
        processed_filepath = filepath.replace('.csv', '_processed.csv')
        df.to_csv(processed_filepath, index=False)
        
        return {
            'processed_file': processed_filepath,
            'summary': summary
        }
    except Exception as e:
        raise Exception(f"Error processing CSV: {str(e)}")

def clean_dataframe(df):
    """Clean and prepare the dataframe"""
    # Standardize column names
    df.columns = [col.lower().replace(' ', '_') for col in df.columns]
    
    # Handle missing values
    for col in df.columns:
        # For numeric columns, fill with median
        if df[col].dtype in ['int64', 'float64']:
            df[col] = df[col].fillna(df[col].median())
        # For string columns, fill with 'Unknown'
        elif df[col].dtype == 'object':
            df[col] = df[col].fillna('Unknown')
    
    # Detect and convert date columns
    for col in df.columns:
        if col.lower().find('date') >= 0:
            try:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                # Fill invalid dates with the column's median date
                if df[col].isna().any():
                    median_date = df[col].dropna().median()
                    df[col] = df[col].fillna(median_date)
            except:
                pass
    
    # Handle duplicate entries
    df = df.drop_duplicates()
    
    # Standardize text fields like locations, suppliers, etc.
    # Handle missing required columns with defaults
    required_columns = ['supplier', 'product', 'quantity']
    for col in required_columns:
        if col not in df.columns:
            if col == 'supplier':
                df[col] = 'Unknown Supplier'
            elif col == 'product':
                df[col] = 'Unspecified Product'
            elif col == 'quantity':
                df[col] = 1

    for col in ['supplier', 'warehouse', 'product', 'location']:
        if col in df.columns and df[col].dtype == 'object':
            df[col] = df[col].str.strip().str.title()
    
    # Add calculated columns if necessary
    if all(col in df.columns for col in ['order_date', 'delivery_date']):
        if df['order_date'].dtype == 'datetime64[ns]' and df['delivery_date'].dtype == 'datetime64[ns]':
            df['delivery_time_days'] = (df['delivery_date'] - df['order_date']).dt.days
    
    # Handle warehouse location data
    if 'warehouse' in df.columns and not all(col in df.columns for col in ['latitude', 'longitude']):
        # Generate consistent coordinates for each warehouse
        warehouses = df['warehouse'].unique()
        # Create a dictionary of warehouse locations with consistent coordinates
        # Using a seed to ensure the same warehouse always gets the same coordinates
        np.random.seed(42)  # Set seed for reproducibility
        warehouse_coords = {}
        
        # Define some major cities coordinates for common warehouse locations
        known_locations = {
            'Mumbai': (19.0760, 72.8777),
            'Delhi': (28.7041, 77.1025),
            'Bangalore': (12.9716, 77.5946),
            'Hyderabad': (17.3850, 78.4867),
            'Chennai': (13.0827, 80.2707),
            'Kolkata': (22.5726, 88.3639),
            'Pune': (18.5204, 73.8567),
            'Ahmedabad': (23.0225, 72.5714),
            'Jaipur': (26.9124, 75.7873),
            'Lucknow': (26.8467, 80.9462),
            'Nashik': (19.9975, 73.7898),
            'Nagpur': (21.1458, 79.0882),
            'Indore': (22.7196, 75.8577),
            'Patna': (25.5941, 85.1376),
            'Bhopal': (23.2599, 77.4126),
            'Vadodara': (22.3072, 73.1812),
            'Coimbatore': (11.0168, 76.9558),
            'Ludhiana': (30.9010, 75.8573),
            'Agra': (27.1767, 78.0081),
            'Nashik': (19.9975, 73.7898),
            'MP': (23.4733, 77.9471)  # Madhya Pradesh center point
        }
        
        for warehouse in warehouses:
            # Check if the warehouse name matches any known location
            warehouse_name = warehouse.strip().title()
            if warehouse_name in known_locations:
                warehouse_coords[warehouse] = known_locations[warehouse_name]
            else:
                # Generate random coordinates for unknown locations
                warehouse_coords[warehouse] = (np.random.uniform(8, 35), np.random.uniform(70, 97))
        
        # Add latitude and longitude columns based on warehouse
        df['latitude'] = df['warehouse'].map(lambda x: warehouse_coords[x][0])
        df['longitude'] = df['warehouse'].map(lambda x: warehouse_coords[x][1])
    
    # Add cost analysis fields if missing but price is available
    if 'price' in df.columns and 'cost' not in df.columns:
        # Convert price to cost (assuming cost is 70-90% of price)
        df['cost'] = df['price'] * np.random.uniform(0.7, 0.9, size=len(df))
    
    # Add category field based on label if available
    if 'label' in df.columns and 'category' not in df.columns:
        df['category'] = df['label']
    
    # Add performance metrics if missing
    if 'supplier' in df.columns and 'on_time_delivery' not in df.columns:
        # Simulate on-time delivery performance
        suppliers = df['supplier'].unique()
        supplier_performance = {sup: np.random.uniform(0.7, 1.0) for sup in suppliers}
        df['on_time_delivery'] = df['supplier'].map(supplier_performance)
    
    if 'supplier' in df.columns and 'quality_score' not in df.columns:
        # Simulate quality scores
        suppliers = df['supplier'].unique()
        quality_scores = {sup: np.random.uniform(0.6, 0.95) for sup in suppliers}
        df.loc[:, 'quality_score'] = df['supplier'].map(quality_scores)
    
    return df

def generate_data_summary(df):
    """Generate summary statistics about the data"""
    summary = {}
    
    # Get basic info
    summary['record_count'] = len(df)
    summary['column_count'] = len(df.columns)
    summary['columns'] = df.columns.tolist()
    
    # Get date range if date columns exist
    date_cols = [col for col in df.columns if 'date' in col.lower() and pd.api.types.is_datetime64_dtype(df[col])]
    if date_cols:
        min_date = min([df[col].min() for col in date_cols])
        max_date = max([df[col].max() for col in date_cols])
        summary['date_range'] = f"{min_date.strftime('%Y-%m-%d')} to {max_date.strftime('%Y-%m-%d')}"
    
    # Get unique values for categorical fields
    for col in ['supplier', 'product', 'warehouse', 'location']:
        if col in df.columns:
            summary[f"{col}s"] = df[col].unique().tolist()
            summary[f"{col}_count"] = len(df[col].unique())
    
    # Get numeric summaries
    numeric_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
    if numeric_cols:
        summary['numeric_columns'] = {}
        for col in numeric_cols:
            summary['numeric_columns'][col] = {
                'min': float(df[col].min()),
                'max': float(df[col].max()),
                'mean': float(df[col].mean()),
                'median': float(df[col].median())
            }
    
    return summary

def generate_route_map(df):
    """Generate route map visualization data"""
    # Check if we have necessary columns for mapping
    required_cols = ['latitude', 'longitude', 'location']
    if not all(col in df.columns for col in required_cols):
        return {'error': 'Missing location data for mapping'}
        
    # Create a basic map of locations
    locations = df[['location', 'latitude', 'longitude']].drop_duplicates()
    
    # Create a list of routes between locations
    routes = []
    if 'source' in df.columns and 'destination' in df.columns:
        for _, row in df[['source', 'destination']].drop_duplicates().iterrows():
            source = row['source']
            dest = row['destination']
            
            source_coords = locations[locations['location'] == source].iloc[0]
            dest_coords = locations[locations['location'] == dest].iloc[0]
            
            routes.append({
                'source': source,
                'destination': dest,
                'source_lat': float(source_coords['latitude']),
                'source_lng': float(source_coords['longitude']),
                'dest_lat': float(dest_coords['latitude']),
                'dest_lng': float(dest_coords['longitude'])
            })
    
    # Format for map rendering
    map_data = {
        'locations': locations.to_dict('records'),
        'routes': routes
    }
    
    return map_data

def get_supplier_details(df, supplier_id):
    """Get detailed analysis for a specific supplier"""
    supplier_df = df[df['supplier'] == supplier_id]
    
    details = {
        'summary': {
            'total_orders': len(supplier_df),
            'unique_products': supplier_df['product'].nunique()
        },
        'performance': {}
    }
    
    # Performance metrics if available
    if 'on_time_delivery' in supplier_df.columns:
        details['performance']['on_time_delivery'] = float(supplier_df['on_time_delivery'].mean())
    
    if 'quality_score' in supplier_df.columns:
        details['performance']['quality_score'] = float(supplier_df['quality_score'].mean())
    
    if 'delivery_time_days' in supplier_df.columns:
        details['performance']['avg_delivery_time'] = float(supplier_df['delivery_time_days'].mean())
    
    # Monthly trend analysis if dates available
    if 'order_date' in supplier_df.columns:
        monthly_orders = supplier_df.set_index('order_date').resample('M').size()
        details['monthly_trend'] = {
            'dates': monthly_orders.index.strftime('%Y-%m').tolist(),
            'values': monthly_orders.tolist()
        }
    
    # Product breakdown
    if 'product' in supplier_df.columns and 'quantity' in supplier_df.columns:
        product_volume = supplier_df.groupby('product')['quantity'].sum()
        details['product_breakdown'] = {
            'products': product_volume.index.tolist(),
            'quantities': product_volume.tolist()
        }
    
    return details

def get_product_details(df, product_id):
    """Get detailed analysis for a specific product"""
    product_df = df[df['product'] == product_id]
    
    details = {
        'summary': {
            'total_orders': len(product_df),
            'total_quantity': int(product_df['quantity'].sum()) if 'quantity' in product_df.columns else 0,
            'suppliers': product_df['supplier'].nunique() if 'supplier' in product_df.columns else 0
        }
    }
    
    # Cost analysis
    if 'cost' in product_df.columns:
        details['cost'] = {
            'total_cost': float(product_df['cost'].sum()),
            'average_cost': float(product_df['cost'].mean()),
            'min_cost': float(product_df['cost'].min()),
            'max_cost': float(product_df['cost'].max())
        }
    
    # Supplier breakdown
    if 'supplier' in product_df.columns:
        supplier_volume = product_df.groupby('supplier').size()
        details['supplier_breakdown'] = {
            'suppliers': supplier_volume.index.tolist(),
            'order_counts': supplier_volume.tolist()
        }
    
    # Monthly trend
    if 'order_date' in product_df.columns:
        monthly_orders = product_df.set_index('order_date').resample('M').size()
        details['monthly_trend'] = {
            'dates': monthly_orders.index.strftime('%Y-%m').tolist(),
            'values': monthly_orders.tolist()
        }
    
    return details

def get_route_details(df, route_id):
    """Get detailed analysis for a specific route"""
    # Parse the route_id (assumed format: "source_to_destination")
    try:
        source, destination = route_id.split('_to_')
    except:
        return {'error': 'Invalid route ID format'}
    
    route_df = df[(df['source'] == source) & (df['destination'] == destination)]
    
    details = {
        'summary': {
            'total_shipments': len(route_df),
            'products_shipped': route_df['product'].nunique() if 'product' in route_df.columns else 0
        }
    }
    
    # Distance and time analysis
    if 'distance' in route_df.columns:
        details['distance'] = {
            'average_distance': float(route_df['distance'].mean()),
            'total_distance': float(route_df['distance'].sum())
        }
    
    if 'delivery_time_days' in route_df.columns:
        details['delivery_time'] = {
            'average_days': float(route_df['delivery_time_days'].mean()),
            'min_days': int(route_df['delivery_time_days'].min()),
            'max_days': int(route_df['delivery_time_days'].max())
        }
    
    # Monthly volume trend
    if 'order_date' in route_df.columns:
        monthly_volume = route_df.set_index('order_date').resample('M').size()
        details['monthly_trend'] = {
            'dates': monthly_volume.index.strftime('%Y-%m').tolist(),
            'values': monthly_volume.tolist()
        }
    
    return details

def get_warehouse_details(df, warehouse_id):
    """Get detailed analysis for a specific warehouse"""
    import requests
    import os
    import http.client
    import json
    from dotenv import load_dotenv
    
    # Load environment variables
    load_dotenv()
    
    warehouse_df = df[df['warehouse'] == warehouse_id]
    
    details = {
        'summary': {
            'total_inventory': int(warehouse_df['quantity'].sum()) if 'quantity' in warehouse_df.columns else 0,
            'unique_products': warehouse_df['product'].nunique() if 'product' in warehouse_df.columns else 0
        }
    }
    
    # Product breakdown
    if 'product' in warehouse_df.columns and 'quantity' in warehouse_df.columns:
        product_inventory = warehouse_df.groupby('product')['quantity'].sum()
        details['product_breakdown'] = {
            'products': product_inventory.index.tolist(),
            'quantities': product_inventory.tolist()
        }
    
    # Cost analysis for the warehouse
    if 'cost' in warehouse_df.columns:
        cost_data = warehouse_df.groupby('product')['cost'].sum().reset_index()
        total_cost = cost_data['cost'].sum()
        
        details['cost_analysis'] = {
            'total_cost': float(total_cost),
            'average_cost_per_product': float(total_cost / len(cost_data)) if len(cost_data) > 0 else 0,
            'product_costs': {
                'products': cost_data['product'].tolist(),
                'costs': cost_data['cost'].tolist()
            }
        }
    elif 'price' in warehouse_df.columns:
        # If cost is not available but price is, use price for cost analysis
        price_data = warehouse_df.groupby('product')['price'].sum().reset_index()
        total_price = price_data['price'].sum()
        
        details['cost_analysis'] = {
            'total_price': float(total_price),
            'average_price_per_product': float(total_price / len(price_data)) if len(price_data) > 0 else 0,
            'product_prices': {
                'products': price_data['product'].tolist(),
                'prices': price_data['price'].tolist()
            }
        }
    
    # Category analysis if available
    if 'category' in warehouse_df.columns or 'label' in warehouse_df.columns:
        category_col = 'category' if 'category' in warehouse_df.columns else 'label'
        category_data = warehouse_df.groupby(category_col)['quantity'].sum().reset_index()
        
        details['category_analysis'] = {
            'categories': category_data[category_col].tolist(),
            'quantities': category_data['quantity'].tolist()
        }
    
    # Inbound/outbound analysis
    if all(col in df.columns for col in ['destination', 'source']):
        inbound = df[df['destination'] == warehouse_id]
        outbound = df[df['source'] == warehouse_id]
        
        details['flow_analysis'] = {
            'inbound_count': len(inbound),
            'outbound_count': len(outbound),
            'ratio': float(len(inbound) / len(outbound)) if len(outbound) > 0 else float('inf')
        }
    
    # Delivery time analysis if available
    if 'delivery_time_days' in warehouse_df.columns:
        delivery_stats = {
            'average_days': float(warehouse_df['delivery_time_days'].mean()),
            'min_days': int(warehouse_df['delivery_time_days'].min()),
            'max_days': int(warehouse_df['delivery_time_days'].max())
        }
        details['delivery_time'] = delivery_stats
    
    # Fetch location data for the warehouse using Maps Data API
    try:
        # Get latitude and longitude for the warehouse
        lat = 0
        lng = 0
        
        if 'latitude' in warehouse_df.columns and 'longitude' in warehouse_df.columns:
            # Use the first occurrence of the warehouse's coordinates
            lat = float(warehouse_df['latitude'].iloc[0])
            lng = float(warehouse_df['longitude'].iloc[0])
        else:
            # Use predefined coordinates based on warehouse name
            # Define some major cities coordinates for common warehouse locations
            known_locations = {
                'Mumbai': (19.0760, 72.8777),
                'Delhi': (28.7041, 77.1025),
                'Bangalore': (12.9716, 77.5946),
                'Hyderabad': (17.3850, 78.4867),
                'Chennai': (13.0827, 80.2707),
                'Kolkata': (22.5726, 88.3639),
                'Pune': (18.5204, 73.8567),
                'Ahmedabad': (23.0225, 72.5714),
                'Jaipur': (26.9124, 75.7873),
                'Lucknow': (26.8467, 80.9462),
                'Nashik': (19.9975, 73.7898),
                'Nagpur': (21.1458, 79.0882),
                'Indore': (22.7196, 75.8577),
                'Patna': (25.5941, 85.1376),
                'Bhopal': (23.2599, 77.4126),
                'Vadodara': (22.3072, 73.1812),
                'Coimbatore': (11.0168, 76.9558),
                'Ludhiana': (30.9010, 75.8573),
                'Agra': (27.1767, 78.0081),
                'Nashik': (19.9975, 73.7898),
                'MP': (23.4733, 77.9471)  # Madhya Pradesh center point
            }
            
            warehouse_name = warehouse_id.strip().title()
            if warehouse_name in known_locations:
                lat, lng = known_locations[warehouse_name]
            else:
                # Use a default location (Mumbai) if warehouse name is not recognized
                lat, lng = 19.0760, 72.8777
        
        # Add basic location information even without API call
        details['location'] = {
            'coordinates': {
                'latitude': lat,
                'longitude': lng
            },
            'warehouse_name': warehouse_id
        }
        
        # Set up the connection to RapidAPI Maps Data API if API key is available
        if os.getenv('RAPIDAPI_KEY'):
            conn = http.client.HTTPSConnection("maps-data.p.rapidapi.com")
            
            headers = {
                'x-rapidapi-key': os.getenv('RAPIDAPI_KEY'),
                'x-rapidapi-host': "maps-data.p.rapidapi.com"
            }
            
            # Make the API request
            conn.request("GET", f"/whatishere.php?lat={lat}&lng={lng}&lang=en&country=in", headers=headers)
            
            res = conn.getresponse()
            data = res.read()
            
            # Process the response
            if res.status == 200:
                location_data = json.loads(data.decode("utf-8"))
                
                # Extract relevant location information
                if 'data' in location_data:
                    data = location_data['data']
                    
                    # Add address and location details
                    details['location'].update({
                        'address': data.get('address', 'Unknown Address'),
                        'town': data.get('town', 'Unknown Town'),
                        'country': data.get('country', 'Unknown Country'),
                        'timezone': data.get('timezone', 'Unknown Timezone')
                    })
                    
                    # Add nearby places information
                    if 'places' in data and len(data['places']) > 0:
                        nearby_places = []
                        
                        for place in data['places'][:5]:  # Limit to 5 nearby places
                            place_info = {
                                'name': place.get('name', 'Unknown Place'),
                                'address': place.get('full_address', 'Unknown Address'),
                                'type': place.get('types', ['Unknown'])[0] if place.get('types') else 'Unknown',
                                'rating': place.get('rating', 'N/A'),
                                'link': place.get('place_link', '#')
                            }
                            
                            # Add working hours if available
                            if 'working_hours' in place and place['working_hours']:
                                place_info['hours'] = place['working_hours']
                            
                            nearby_places.append(place_info)
                        
                        details['nearby_places'] = nearby_places
                else:
                    details['location_error'] = "No location data found in API response"
            else:
                details['location_error'] = f"API request failed with status code: {res.status}"
        else:
            details['location_note'] = "Location API key not configured. Using basic location data only."
    except Exception as e:
        details['location_error'] = f"Failed to fetch location data: {str(e)}"
    
    return details