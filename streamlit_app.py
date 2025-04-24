import streamlit as st
import pandas as pd
import data_processor
import os
from dotenv import load_dotenv
import google.generativeai as genai
import plotly.express as px

# Load environment variables
load_dotenv()

# Configure Gemini API
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))

# Configure Streamlit page
st.set_page_config(
    page_title="Supply Chain Analytics",
    page_icon="🚚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS styling
st.markdown("""
<style>
    .stApp { background-color: #1a1d2b; color: white; }
    body { color: white !important; }
    h1, h2, h3, h4, h5, h6 { color: white !important; }
    .stTextInput input { color: white !important; background-color: rgba(255,255,255,0.1) !important; }
    .uploadedFile { padding: 20px; border-radius: 10px; background: white; }
    .plot-container { background: white; padding: 20px; border-radius: 10px; margin: 10px 0; }
</style>
""", unsafe_allow_html=True)

# Add HeyGen AI Avatar embedding with improved visibility and toggle functionality
heygen_embed_script = """
<style>
.heygen-wrapper {
    position: fixed;
    bottom: 20px;
    left: 20px;
    z-index: 9999;
    width: 80px;
    height: 80px;
    transition: all 0.3s ease;
    overflow: hidden;
}
.heygen-wrapper.expanded {
    width: 350px;
    height: 350px;
    border-radius: 10px;
}
.heygen-toggle {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 80px;
    height: 80px;
    border-radius: 50%;
    background: #1a1d2b;
    border: 2px solid white;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    z-index: 10000;
}
.heygen-toggle img {
    width: 60px;
    height: 60px;
    border-radius: 50%;
}
.heygen-iframe {
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 100%;
    border: 2px solid white;
    border-radius: 10px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    opacity: 0;
    transition: opacity 0.3s ease;
}
.expanded .heygen-iframe {
    opacity: 1;
}
</style>

<div class="heygen-wrapper" id="heygenWrapper">
    <div class="heygen-toggle" id="heygenToggle">
        <img src="https://files2.heygen.ai/avatar/v3/582ee8fe072a48fda3bc68241aeff660_45660/preview_target.webp" alt="AI Assistant">
    </div>
    <iframe 
        class="heygen-iframe"
        id="heygenIframe"
        src="https://labs.heygen.com/guest/streaming-embed?share=eyJxdWFsaXR5IjoiaGlnaCIsImF2YXRhck5hbWUiOiJTaWxhc0hSX3B1YmxpYyIsInByZXZpZXdJ%0D%0AbWciOiJodHRwczovL2ZpbGVzMi5oZXlnZW4uYWkvYXZhdGFyL3YzLzU4MmVlOGZlMDcyYTQ4ZmRh%0D%0AM2JjNjgyNDFhZWZmNjYwXzQ1NjYwL3ByZXZpZXdfdGFyZ2V0LndlYnAiLCJuZWVkUmVtb3ZlQmFj%0D%0Aa2dyb3VuZCI6ZmFsc2UsImtub3dsZWRnZUJhc2VJZCI6ImYwNmY1ZGE1YzE0MDRiMDg4MTZiNmY1%0D%0ANGQ4NjhhYzRkIiwidXNlcm5hbWUiOiI2OGRmZDQ1Nzk1Mzg0OWQyODFmNzExMmNhMWNiYTAwYSJ9&inIFrame=1" 
        allow="microphone"
        title="HeyGen AI Assistant">
    </iframe>
</div>

<script>
document.addEventListener('DOMContentLoaded', function() {
    const wrapper = document.getElementById('heygenWrapper');
    const toggle = document.getElementById('heygenToggle');
    
    toggle.addEventListener('click', function() {
        wrapper.classList.toggle('expanded');
    });
});
</script>
"""

# Session state initialization
if 'processed_data' not in st.session_state:
    st.session_state.processed_data = None
if 'data_summary' not in st.session_state:
    st.session_state.data_summary = {}
if 'ai_context' not in st.session_state:
    st.session_state.ai_context = None
if 'ai_response' not in st.session_state:
    st.session_state.ai_response = ""
if 'column_mapping' not in st.session_state:
    st.session_state.column_mapping = {}

# Main application
st.title("Supply Chain Analytics Dashboard")

# Inject HeyGen avatar script - fixed implementation using st.components.v1.html
# Fix HeyGen visibility issue by adjusting the height parameter


# File upload section
with st.sidebar:
    st.header("Data Upload")
    uploaded_file = st.file_uploader("Upload CSV File", type="csv")
    
    if uploaded_file is not None:
        with st.spinner("Processing data..."):
            try:
                # Ensure uploads directory exists - make path relative for cloud deployment
                os.makedirs("uploads", exist_ok=True)
                
                # Save uploaded file with relative path
                file_path = os.path.join("uploads", uploaded_file.name)
                with open(file_path, "wb") as f:
                    f.write(uploaded_file.getbuffer())
                
                # Process CSV
                processed_data = data_processor.process_csv(file_path)
                df = pd.read_csv(processed_data['processed_file'])
                st.session_state.processed_data = df
                st.session_state.data_summary = processed_data['summary']
                
                # Analyze columns and create intelligent mapping
                st.session_state.column_mapping = {}
                
                # Detect column types based on names and content
                for col in df.columns:
                    col_lower = col.lower()
                    # Product/item identification
                    if any(keyword in col_lower for keyword in ['product', 'item', 'sku', 'name']):
                        st.session_state.column_mapping['product'] = col
                    # Warehouse/location identification
                    elif any(keyword in col_lower for keyword in ['warehouse', 'location', 'store', 'facility']):
                        st.session_state.column_mapping['warehouse'] = col
                    # Quantity/inventory identification
                    elif any(keyword in col_lower for keyword in ['quantity', 'qty', 'inventory', 'stock', 'count']):
                        st.session_state.column_mapping['quantity'] = col
                    # Price/cost identification
                    elif any(keyword in col_lower for keyword in ['price', 'cost', 'value']):
                        st.session_state.column_mapping['price'] = col
                    # Delivery time identification
                    elif any(keyword in col_lower for keyword in ['delivery', 'time', 'lead', 'days']):
                        st.session_state.column_mapping['delivery_time'] = col
                    # Category/label identification
                    elif any(keyword in col_lower for keyword in ['category', 'type', 'label', 'group']):
                        st.session_state.column_mapping['label'] = col
                    # Brand/manufacturer identification
                    elif any(keyword in col_lower for keyword in ['brand', 'manufacturer', 'vendor', 'supplier']):
                        st.session_state.column_mapping['brand'] = col
                    # Rating/rank identification
                    elif any(keyword in col_lower for keyword in ['rating', 'rank', 'score', 'review']):
                        st.session_state.column_mapping['rank'] = col
                
                # If quantity column not found, create a dummy one for counting
                if 'quantity' not in st.session_state.column_mapping:
                    df['quantity'] = 1
                    st.session_state.column_mapping['quantity'] = 'quantity'
                    st.session_state.processed_data = df
                
                st.success("File processed successfully!")
                st.subheader("Column Mapping")
                st.json(st.session_state.column_mapping)
                st.subheader("Data Summary")
                st.json(st.session_state.data_summary)
            except Exception as e:
                st.error(f"Error processing file: {str(e)}")
    st.components.v1.html(heygen_embed_script, height=500)

# Main dashboard
if st.session_state.processed_data is not None:
    df = st.session_state.processed_data
    mapping = st.session_state.column_mapping
    
    # Data Summary
    st.sidebar.subheader("Data Summary")
    cols = st.sidebar.columns(2)
    cols[0].metric("Total Records", st.session_state.data_summary.get('record_count', 'N/A'))
    cols[1].metric("Date Range", st.session_state.data_summary.get('date_range', 'N/A'))
    
    # Visualizations - Define tabs before using them
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Inventory", "Delivery Times", "Cost Analysis", "Map View", "AI Assistant", "Data Explorer"])
    
    with tab1:
        try:
            st.subheader("Inventory Analysis")
            
            # Get product and warehouse columns (or alternatives)
            product_col = mapping.get('product', df.columns[0])  # Default to first column if not found
            warehouse_col = mapping.get('warehouse', None)
            quantity_col = mapping.get('quantity', None)
            
            if warehouse_col and quantity_col:
                inventory_df = df.groupby([product_col, warehouse_col])[quantity_col].sum().reset_index()
                fig = px.bar(inventory_df, x=product_col, y=quantity_col, color=warehouse_col, 
                            title=f"Inventory Levels by {product_col} and {warehouse_col}")
                st.plotly_chart(fig, use_container_width=True)
                
                # Add a pie chart showing product distribution
                product_totals = inventory_df.groupby(product_col)[quantity_col].sum().reset_index()
                fig_pie = px.pie(
                    product_totals, 
                    values=quantity_col, 
                    names=product_col,
                    title=f'Overall Product Distribution'
                )
                st.plotly_chart(fig_pie, use_container_width=True)
            elif quantity_col:
                # If no warehouse column, just show product quantities
                inventory_df = df.groupby([product_col])[quantity_col].sum().reset_index()
                fig = px.bar(inventory_df, x=product_col, y=quantity_col,
                            title=f"Inventory Levels by {product_col}")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("Could not generate inventory analysis. Missing required columns.")
                st.info(f"Available columns: {', '.join(df.columns)}")
        except Exception as e:
            st.error(f"Could not generate inventory chart: {str(e)}")
    
    with tab2:
        try:
            st.subheader("Delivery Time Analysis")
            
            # Get delivery time column
            delivery_col = mapping.get('delivery_time', None)
            warehouse_col = mapping.get('warehouse', None)
            brand_col = mapping.get('brand', None)
            
            if delivery_col:
                # Try to extract numeric values from delivery times
                try:
                    df['Delivery_Days'] = df[delivery_col].str.extract('(\d+)').astype(float)
                except:
                    # If extraction fails, try to use the column directly if it's numeric
                    if pd.api.types.is_numeric_dtype(df[delivery_col]):
                        df['Delivery_Days'] = df[delivery_col]
                    else:
                        st.warning(f"Could not convert {delivery_col} to numeric values.")
                        raise ValueError(f"Could not process delivery times from {delivery_col}")
                
                # Create delivery time analysis by warehouse if available
                if warehouse_col:
                    delivery_by_warehouse = df.groupby(warehouse_col)['Delivery_Days'].mean().reset_index()
                    fig1 = px.bar(delivery_by_warehouse, x=warehouse_col, y='Delivery_Days',
                                title=f"Average Delivery Time by {warehouse_col} (Days)",
                                color='Delivery_Days', color_continuous_scale='Viridis')
                    st.plotly_chart(fig1, use_container_width=True)
                
                # Create delivery time analysis by brand if available
                if brand_col:
                    delivery_by_brand = df.groupby(brand_col)['Delivery_Days'].mean().reset_index().sort_values('Delivery_Days')
                    delivery_by_brand = delivery_by_brand.head(10)  # Top 10 brands by delivery time
                    fig2 = px.bar(delivery_by_brand, x=brand_col, y='Delivery_Days',
                                title=f"Top 10 {brand_col}s by Average Delivery Time (Days)",
                                color='Delivery_Days', color_continuous_scale='Viridis')
                    st.plotly_chart(fig2, use_container_width=True)
                
                # Delivery time distribution
                fig3 = px.histogram(df, x='Delivery_Days', 
                               title="Distribution of Delivery Times",
                               nbins=10, color_discrete_sequence=['#636EFA'])
                st.plotly_chart(fig3, use_container_width=True)
            else:
                st.warning("Delivery time column not found in the dataset.")
                st.info(f"Available columns: {', '.join(df.columns)}")
        except Exception as e:
            st.error(f"Could not generate delivery time charts: {str(e)}")
    
    with tab3:
        try:
            st.subheader("Cost Analysis")
            
            # Get price/cost column
            price_col = mapping.get('price', None)
            brand_col = mapping.get('brand', None)
            label_col = mapping.get('label', None)
            rank_col = mapping.get('rank', None)
            
            if price_col:
                st.info(f"Using '{price_col}' column for cost analysis")
                
                # Create cost analysis by brand if available
                if brand_col:
                    # Group by Brand and calculate average price
                    cost_by_brand = df.groupby(brand_col)[price_col].mean().reset_index().sort_values(price_col, ascending=False)
                    cost_by_brand = cost_by_brand.head(10)  # Top 10 brands by price
                    
                    fig1 = px.bar(cost_by_brand, x=brand_col, y=price_col,
                                title=f"Top 10 {brand_col}s by Average {price_col}",
                                color=price_col, color_continuous_scale='Viridis')
                    st.plotly_chart(fig1, use_container_width=True)
                
                # Create price distribution chart
                fig2 = px.histogram(df, x=price_col, 
                               title=f"Distribution of {price_col}s",
                               nbins=20, color_discrete_sequence=['#636EFA'])
                st.plotly_chart(fig2, use_container_width=True)
                
                # Create price by product type pie chart if label column exists
                if label_col:
                    cost_by_type = df.groupby(label_col)[price_col].mean().reset_index()
                    fig3 = px.pie(cost_by_type, values=price_col, names=label_col, 
                                title=f"{price_col} Distribution by {label_col}")
                    st.plotly_chart(fig3, use_container_width=True)
                
                # Price vs. Rating scatter plot if rank column exists
                if rank_col:
                    fig4 = px.scatter(df, x=price_col, y=rank_col, color=brand_col if brand_col else None,
                                    title=f"{price_col} vs. {rank_col}",
                                    hover_data=[df.columns[0]])  # Use first column for hover data
                    st.plotly_chart(fig4, use_container_width=True)
                    
                    # Calculate correlation
                    correlation = df[[price_col, rank_col]].corr().iloc[0,1]
                    st.metric(f"{price_col}-{rank_col} Correlation", f"{correlation:.2f}")
                    if correlation > 0.5:
                        st.info(f"Strong positive correlation: Higher {price_col}s tend to have higher {rank_col}s")
                    elif correlation < -0.5:
                        st.info(f"Strong negative correlation: Lower {price_col}s tend to have higher {rank_col}s")
                    else:
                        st.info(f"Weak correlation: {price_col} doesn't strongly predict {rank_col}")
            else:
                st.warning("No price or cost column found in the dataset.")
                st.info(f"Available columns: {', '.join(df.columns)}")
        except Exception as e:
            st.error(f"Could not generate cost analysis charts: {str(e)}")

# Run with: streamlit run streamlit_app.py

# Add the Map View tab implementation
    with tab4:
        try:
            st.subheader("Geographic Distribution Analysis")
        
        # Get location column (warehouse, city, state, etc.)
            warehouse_col = mapping.get('warehouse', None)
            location_cols = [col for col in df.columns if any(loc in col.lower() for loc in ['warehouse', 'location', 'city', 'state', 'country', 'region'])]
        
            if not warehouse_col and location_cols:
                warehouse_col = location_cols[0]
                st.info(f"Using '{warehouse_col}' as location column")
        
            if warehouse_col:
            # Define known locations with coordinates
                location_coordinates = {
                'Delhi': [28.7041, 77.1025],
                'Mumbai': [19.0760, 72.8777],
                'Kolkata': [22.5726, 88.3639],
                'Nashik': [19.9975, 73.7898],
                'MP': [23.4733, 77.9471],  # Using Bhopal as representative for MP
                'Chennai': [13.0827, 80.2707],
                'Bangalore': [12.9716, 77.5946],
                'Hyderabad': [17.3850, 78.4867],
                'Pune': [18.5204, 73.8567],
                'Ahmedabad': [23.0225, 72.5714],
                'Jaipur': [26.9124, 75.7873],
                'Lucknow': [26.8467, 80.9462],
                'Kanpur': [26.4499, 80.3319],
                'Nagpur': [21.1458, 79.0882],
                'Indore': [22.7196, 75.8577],
                'Thane': [19.2183, 72.9781],
                'Bhopal': [23.2599, 77.4126],
                'Visakhapatnam': [17.6868, 83.2185],
                'Patna': [25.5941, 85.1376],
                'Vadodara': [22.3072, 73.1812]
            }
            
            # Get category/label column if available
                label_col = mapping.get('label', None)
                quantity_col = mapping.get('quantity', None)
            
            # Create a dataframe for map visualization
                if label_col and quantity_col:
                # Group by location and category
                    map_data_df = df.groupby([warehouse_col, label_col])[quantity_col].sum().reset_index()
                
                # Create a dataframe with coordinates
                    map_data = []
                    for _, row in map_data_df.iterrows():
                        location = row[warehouse_col]
                        if location in location_coordinates:
                            map_data.append({
                            'Location': location,
                            'Category': row[label_col],
                            'Count': row[quantity_col],
                            'lat': location_coordinates[location][0],
                            'lon': location_coordinates[location][1]
                        })
                
                    map_df = pd.DataFrame(map_data)
                
                    if not map_df.empty:
                    # Display filters
                        col1, col2 = st.columns(2)
                        with col1:
                            selected_locations = st.multiselect(
                            "Select Locations", 
                            options=sorted(map_df['Location'].unique()),
                            default=sorted(map_df['Location'].unique())
                        )
                    
                        with col2:
                            selected_categories = st.multiselect(
                            "Select Categories",
                            options=sorted(map_df['Category'].unique()),
                            default=sorted(map_df['Category'].unique())
                        )
                    
                    # Filter data based on selections
                        filtered_map_df = map_df[
                        (map_df['Location'].isin(selected_locations)) & 
                        (map_df['Category'].isin(selected_categories))
                    ]
                    
                        if not filtered_map_df.empty:
                        # Create map visualization
                            fig = px.scatter_mapbox(
                            filtered_map_df, 
                            lat="lat", 
                            lon="lon", 
                            color="Category",
                            size="Count",
                            hover_name="Location",
                            hover_data=["Category", "Count"],
                            zoom=4,
                            height=600,
                            size_max=25,
                            title="Product Categories by Location"
                        )
                        
                            fig.update_layout(mapbox_style="carto-positron")
                            fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})
                            st.plotly_chart(fig, use_container_width=True)
                        
                        # Add a bar chart showing category distribution by location
                            category_dist = px.bar(
                            filtered_map_df,
                            x="Location",
                            y="Count",
                            color="Category",
                            title="Product Category Distribution by Location",
                            barmode="group"
                        )
                            st.plotly_chart(category_dist, use_container_width=True)
                        
                        # Add a pie chart showing overall category distribution
                            category_totals = filtered_map_df.groupby('Category')['Count'].sum().reset_index()
                            fig_pie = px.pie(
                            category_totals, 
                            values='Count', 
                            names='Category',
                            title='Overall Product Category Distribution'
                        )
                            st.plotly_chart(fig_pie, use_container_width=True)
                        else:
                            st.warning("No data available for the selected filters.")
                    else:
                        st.warning(f"Could not find coordinates for locations in the dataset. Available locations in our database: {', '.join(location_coordinates.keys())}")
                elif quantity_col:
                # If no category column, just show location counts
                    map_data_df = df.groupby([warehouse_col])[quantity_col].sum().reset_index()
                
                # Create a dataframe with coordinates
                    map_data = []
                    for _, row in map_data_df.iterrows():
                        location = row[warehouse_col]
                        if location in location_coordinates:
                            map_data.append({
                            'Location': location,
                            'Count': row[quantity_col],
                            'lat': location_coordinates[location][0],
                            'lon': location_coordinates[location][1]
                        })
                
                    map_df = pd.DataFrame(map_data)
                
                    if not map_df.empty:
                    # Create map visualization
                        fig = px.scatter_mapbox(
                        map_df, 
                        lat="lat", 
                        lon="lon", 
                        size="Count",
                        hover_name="Location",
                        hover_data=["Count"],
                        zoom=4,
                        height=600,
                        size_max=25,
                        title="Inventory by Location"
                    )
                    
                        fig.update_layout(mapbox_style="carto-positron")
                        fig.update_layout(margin={"r":0,"t":50,"l":0,"b":0})
                        st.plotly_chart(fig, use_container_width=True)
                    
                    # Add a bar chart showing inventory by location
                        fig_bar = px.bar(
                        map_df,
                        x="Location",
                        y="Count",
                        title="Inventory by Location",
                        color="Count",
                        color_continuous_scale="Viridis"
                    )
                        st.plotly_chart(fig_bar, use_container_width=True)
                    else:
                        st.warning(f"Could not find coordinates for locations in the dataset. Available locations in our database: {', '.join(location_coordinates.keys())}")
                else:
                    st.warning("Could not generate map visualization. Missing quantity column.")
            else:
                st.warning("Could not generate map visualization. No location column found.")
                st.info(f"Available columns: {', '.join(df.columns)}")
            
        except Exception as e:
            st.error(f"Could not generate map visualization: {str(e)}")
            st.info("If you're seeing this error, please check that your data contains valid location information.")

# Add AI Assistant tab
    with tab5:
        st.subheader("AI Supply Chain Assistant")
        st.write("Ask questions about your supply chain data and get AI-powered insights.")
    
    # Create a text input for the user's question
        user_question = st.text_input("Ask a question about your data:", "")
    
        if st.button("Get Insights"):
            if user_question:
                with st.spinner("Analyzing your data..."):
                    try:
                    # Create a context for the AI with data summary
                        context = f"""
                    Data Summary:
                    - Total Records: {st.session_state.data_summary.get('record_count', 'N/A')}
                    - Date Range: {st.session_state.data_summary.get('date_range', 'N/A')}
                    - Columns: {', '.join(df.columns)}
                    
                    The data contains information about supply chain with the following key metrics:
                    """
                    
                    # Add information about key columns
                        for key, col in mapping.items():
                            if key == 'warehouse':
                                context += f"- Locations/Warehouses: {', '.join(df[col].unique()[:5])}... (total: {df[col].nunique()})\n"
                            elif key == 'product':
                                context += f"- Products: {', '.join(df[col].unique()[:5])}... (total: {df[col].nunique()})\n"
                            elif key == 'label':
                                context += f"- Categories: {', '.join(df[col].unique()[:5])}... (total: {df[col].nunique()})\n"
                            elif key == 'price':
                                context += f"- Price Range: {df[col].min()} to {df[col].max()}, Average: {df[col].mean():.2f}\n"
                            elif key == 'delivery_time':
                                if 'Delivery_Days' in df.columns:
                                    context += f"- Delivery Times: {df['Delivery_Days'].min()} to {df['Delivery_Days'].max()} days, Average: {df['Delivery_Days'].mean():.2f} days\n"
                    
                    # Generate AI response
                        model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')
                        response = model.generate_content(
                        f"""You are a supply chain analytics expert. Analyze the following data and answer the user's question.
                        
                        {context}
                        
                        User Question: {user_question}
                        
                        Provide a detailed, insightful answer with specific data points when possible.
                        """
                    )
                    
                    # Display the response
                        st.session_state.ai_response = response.text
                        st.markdown("### AI Analysis")
                        st.markdown(st.session_state.ai_response)
                    
                    except Exception as e:
                        st.error(f"Error generating AI insights: {str(e)}")
            else:
                st.warning("Please enter a question to get insights.")

# Add Data Explorer tab
    with tab6:
        st.subheader("Data Explorer")
        
        # Create two sections: Raw Data and Analyzed Data
        data_section = st.radio("Select Data View", ["Raw Data", "Analyzed Data"])
        
        if data_section == "Raw Data":
            st.write("### Original Dataset")
            
            # Add search functionality
            search_term = st.text_input("Search in data:", "")
            
            # Add column filter
            selected_columns = st.multiselect(
                "Select columns to display:",
                options=df.columns.tolist(),
                default=df.columns.tolist()[:5]  # Default to first 5 columns
            )
            
            # Filter data based on search term
            if search_term:
                filtered_df = df[df.astype(str).apply(lambda row: row.str.contains(search_term, case=False).any(), axis=1)]
            else:
                filtered_df = df
            
            # Display data with selected columns
            if selected_columns:
                st.dataframe(filtered_df[selected_columns], use_container_width=True)
            else:
                st.dataframe(filtered_df, use_container_width=True)
            
            # Show data statistics
            if st.checkbox("Show data statistics"):
                st.write("### Data Statistics")
                st.write(filtered_df.describe())
        
        else:  # Analyzed Data
            st.write("### Analyzed Data")
            
            # Create tabs for different analyses
            analysis_tabs = st.tabs(["Inventory Analysis", "Delivery Analysis", "Cost Analysis", "Location Analysis"])
            
            with analysis_tabs[0]:
                st.write("#### Inventory Analysis Results")
                
                # Get product and warehouse columns
                product_col = mapping.get('product', df.columns[0])
                warehouse_col = mapping.get('warehouse', None)
                quantity_col = mapping.get('quantity', None)
                
                if warehouse_col and quantity_col:
                    # Show inventory by product and warehouse
                    inventory_df = df.groupby([product_col, warehouse_col])[quantity_col].sum().reset_index()
                    st.dataframe(inventory_df, use_container_width=True)
                    
                    # Show inventory statistics
                    st.write("##### Inventory Statistics by Product")
                    product_stats = inventory_df.groupby(product_col)[quantity_col].agg(['sum', 'mean', 'min', 'max']).reset_index()
                    st.dataframe(product_stats, use_container_width=True)
                elif quantity_col:
                    # If no warehouse column, just show product quantities
                    inventory_df = df.groupby([product_col])[quantity_col].sum().reset_index()
                    st.dataframe(inventory_df, use_container_width=True)
            
            with analysis_tabs[1]:
                st.write("#### Delivery Time Analysis Results")
                
                # Get delivery time column
                delivery_col = mapping.get('delivery_time', None)
                
                if delivery_col and 'Delivery_Days' in df.columns:
                    # Show delivery time statistics
                    if warehouse_col:
                        delivery_by_warehouse = df.groupby(warehouse_col)['Delivery_Days'].agg(['mean', 'min', 'max', 'count']).reset_index()
                        st.write("##### Delivery Times by Location")
                        st.dataframe(delivery_by_warehouse, use_container_width=True)
                    
                    if 'brand' in mapping:
                        brand_col = mapping['brand']
                        delivery_by_brand = df.groupby(brand_col)['Delivery_Days'].agg(['mean', 'min', 'max', 'count']).reset_index().sort_values('mean')
                        st.write("##### Delivery Times by Brand")
                        st.dataframe(delivery_by_brand, use_container_width=True)
                else:
                    st.info("Delivery time data not available or not processed.")
            
            with analysis_tabs[2]:
                st.write("#### Cost Analysis Results")
                
                # Get price/cost column
                price_col = mapping.get('price', None)
                
                if price_col:
                    # Show price statistics
                    if 'brand' in mapping:
                        brand_col = mapping['brand']
                        price_by_brand = df.groupby(brand_col)[price_col].agg(['mean', 'min', 'max', 'count']).reset_index().sort_values('mean', ascending=False)
                        st.write("##### Price Statistics by Brand")
                        st.dataframe(price_by_brand, use_container_width=True)
                    
                    if 'label' in mapping:
                        label_col = mapping['label']
                        price_by_category = df.groupby(label_col)[price_col].agg(['mean', 'min', 'max', 'count']).reset_index().sort_values('mean', ascending=False)
                        st.write("##### Price Statistics by Category")
                        st.dataframe(price_by_category, use_container_width=True)
                else:
                    st.info("Price/cost data not available.")
            
            with analysis_tabs[3]:
                st.write("#### Location Analysis Results")
                
                if warehouse_col and quantity_col:
                    # Show inventory by location
                    location_inventory = df.groupby(warehouse_col)[quantity_col].sum().reset_index().sort_values(quantity_col, ascending=False)
                    st.write("##### Inventory by Location")
                    st.dataframe(location_inventory, use_container_width=True)
                    
                    # Show product count by location
                    if product_col:
                        product_count_by_location = df.groupby(warehouse_col)[product_col].nunique().reset_index()
                        product_count_by_location.columns = [warehouse_col, 'Unique Products Count']
                        st.write("##### Product Variety by Location")
                        st.dataframe(product_count_by_location, use_container_width=True)
                else:
                    st.info("Location data not available or not processed.")
            
            # Add download buttons for analyzed data
            st.write("### Download Analyzed Data")
            
            # Create a buffer to hold the Excel file
            if st.button("Generate Excel Report"):
                try:
                    import io
                    from datetime import datetime
                    
                    buffer = io.BytesIO()
                    
                    # Create a Pandas Excel writer using the buffer
                    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                        # Write each dataframe to a different worksheet
                        df.to_excel(writer, sheet_name='Raw Data', index=False)
                        
                        if 'inventory_df' in locals():
                            inventory_df.to_excel(writer, sheet_name='Inventory Analysis', index=False)
                        
                        if 'delivery_by_warehouse' in locals():
                            delivery_by_warehouse.to_excel(writer, sheet_name='Delivery by Location', index=False)
                        
                        if 'price_by_brand' in locals():
                            price_by_brand.to_excel(writer, sheet_name='Price Analysis', index=False)
                        
                        if 'location_inventory' in locals():
                            location_inventory.to_excel(writer, sheet_name='Location Analysis', index=False)
                    
                    # Set the buffer position to the beginning
                    buffer.seek(0)
                    
                    # Generate download link
                    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
                    st.download_button(
                        label="Download Excel Report",
                        data=buffer,
                        file_name=f"supply_chain_analysis_{current_time}.xlsx",
                        mime="application/vnd.ms-excel"
                    )
                    
                    st.success("Excel report generated successfully!")
                except Exception as e:
                    st.error(f"Error generating Excel report: {str(e)}")