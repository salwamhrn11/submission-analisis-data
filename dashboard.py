import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
import folium
from folium.plugins import MarkerCluster
from streamlit_folium import folium_static

# Load datasets
customers = pd.read_csv('data/customers_dataset.csv')
geolocation = pd.read_csv('data/geolocation_dataset.csv')
order_items = pd.read_csv('data/order_items_dataset.csv')
order_payments = pd.read_csv('data/order_payments_dataset.csv')
order_reviews = pd.read_csv('data/order_reviews_dataset.csv')
orders = pd.read_csv('data/orders_dataset.csv')
products = pd.read_csv('data/products_dataset.csv')

# Store datasets in a dictionary
data = {
    'customers': customers,
    'geo': geolocation,
    'items': order_items,
    'payments': order_payments,
    'reviews': order_reviews,
    'orders': orders,
    'products': products
}

# Handle missing values and duplicates
for df_name, df in data.items():
    data[df_name] = df.drop_duplicates()
    if df_name == 'customers':
        data[df_name] = df.dropna(subset=['customer_id', 'customer_unique_id'])
    elif df_name == 'orders':
        data[df_name] = df.dropna(subset=['order_id', 'customer_id', 'order_purchase_timestamp'])
    elif df_name == 'order_items':
        data[df_name] = df.dropna(subset=['order_id', 'product_id', 'seller_id'])
    else:
        data[df_name] = df.ffill()

# Define date columns
date_columns = ['order_purchase_timestamp', 'order_approved_at', 
                'order_delivered_carrier_date', 'order_delivered_customer_date', 
                'order_estimated_delivery_date', 'review_creation_date', 
                'review_answer_timestamp']

# Convert date columns to datetime type
for df_name, df in data.items():
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

# Streamlit app
st.title("E-commerce Data Analysis Dashboard")

# Sidebar for question selection
st.sidebar.header("Select Analysis Question")
question = st.sidebar.selectbox("Choose a question:", [
    "Average Delivery Time by Zip Code and State",
    "Average Review Scores by Payment Method",
    "Correlation Between Number of Reviews and Revenue by Product Category",
    "Top Selling Product Categories",
    "Customer Distribution by Geolocation"
])

# Question 1: Average Delivery Time by Zip Code and State
if question == "Average Delivery Time by Zip Code and State":
    order_geo = orders.merge(customers, on='customer_id').merge(geolocation, left_on='customer_zip_code_prefix', right_on='geolocation_zip_code_prefix')
    order_geo['delivery_time'] = (pd.to_datetime(order_geo['order_delivered_customer_date']) - pd.to_datetime(order_geo['order_purchase_timestamp'])).dt.days
    delivery_time_by_zip = order_geo.groupby(['customer_zip_code_prefix', 'customer_state'])['delivery_time'].mean().reset_index()

    # Interactive slider for selecting zip code range
    zip_range = st.slider("Select Zip Code Range", min_value=int(delivery_time_by_zip['customer_zip_code_prefix'].min()), max_value=int(delivery_time_by_zip['customer_zip_code_prefix'].max()), value=(10000, 99999))
    filtered_data = delivery_time_by_zip[(delivery_time_by_zip['customer_zip_code_prefix'] >= zip_range[0]) & (delivery_time_by_zip['customer_zip_code_prefix'] <= zip_range[1])]

    # Visualization
    plt.figure(figsize=(12, 6))
    sns.barplot(data=filtered_data, x='customer_zip_code_prefix', y='delivery_time', hue='customer_state', palette='viridis')
    plt.title('Average Delivery Time by Zip Code and State')
    plt.xlabel('Zip Code')
    plt.ylabel('Average Delivery Time (days)')
    plt.xticks(rotation=45)
    plt.ylim(0, filtered_data['delivery_time'].max() + 1) 
    plt.grid(axis='y', linestyle='--', alpha=0.7) 
    plt.legend(title='State')
    plt.tight_layout()
    st.pyplot(plt)
    st.write("""
        The graph shows that average delivery times vary significantly by zip code and state. Consider optimizing routes and investing in infrastructure 
        to reduce delivery times in remote areas.
    """)

# Question 2: Average Review Scores by Payment Method
elif question == "Average Review Scores by Payment Method":
    payment_review = orders.merge(order_reviews, on='order_id').merge(order_payments, on='order_id')
    avg_review_by_payment = payment_review.groupby('payment_type')['review_score'].mean().reset_index()

    # Interactive slider for selecting review score range
    score_range = st.slider("Select Review Score Range", min_value=int(avg_review_by_payment['review_score'].min()), max_value=int(avg_review_by_payment['review_score'].max()), value=(0, 5))
    filtered_data = avg_review_by_payment[(avg_review_by_payment['review_score'] >= score_range[0]) & (avg_review_by_payment['review_score'] <= score_range[1])]

    # Visualization
    plt.figure(figsize=(10, 6))
    sns.barplot(data=filtered_data, x='payment_type', y='review_score', palette='coolwarm')
    plt.title('Average Review Scores by Payment Method')
    plt.xlabel('Payment Method')
    plt.ylabel('Average Review Score')
    plt.xticks(rotation=45)
    st.pyplot(plt)
    st.write("""
        Credit cards and vouchers lead to higher review scores, indicating a smoother experience. Analyze lower-rated payment methods for potential improvements.
    """)

# Question 3: Correlation Between Number of Reviews and Revenue by Product Category
elif question == "Correlation Between Number of Reviews and Revenue by Product Category":
    revenue_reviews = order_items.merge(products, on='product_id').merge(order_reviews, on='order_id')
    category_revenue = revenue_reviews.groupby('product_category_name')['price'].sum().reset_index()
    category_reviews = revenue_reviews.groupby('product_category_name')['review_id'].count().reset_index()
    category_summary = category_revenue.merge(category_reviews, on='product_category_name')
    category_summary.columns = ['product_category_name', 'total_revenue', 'total_reviews']

    # Interactive sliders for selecting ranges
    revenue_range = st.slider("Select Revenue Range", min_value=int(category_summary['total_revenue'].min()), max_value=int(category_summary['total_revenue'].max()), value=(0, int(category_summary['total_revenue'].max())))
    reviews_range = st.slider("Select Reviews Range", min_value=int(category_summary['total_reviews'].min()), max_value=int(category_summary['total_reviews'].max()), value=(0, int(category_summary['total_reviews'].max())))
    
    filtered_data = category_summary[(category_summary['total_revenue'] >= revenue_range[0]) & 
                                     (category_summary['total_revenue'] <= revenue_range[1]) & 
                                     (category_summary['total_reviews'] >= reviews_range[0]) & 
                                     (category_summary['total_reviews'] <= reviews_range[1])]

    # Visualization
    plt.figure(figsize=(12, 6))
    sns.scatterplot(data=filtered_data, x='total_reviews', y='total_revenue', hue='product_category_name', palette='Set1', s=100)
    plt.title('Correlation Between Number of Reviews and Revenue by Product Category')
    plt.xlabel('Number of Reviews')
    plt.ylabel('Total Revenue')
    st.pyplot(plt)
    st.write("""
        The scatterplot reveals the correlation between the number of reviews and revenue for various product categories.
    """)

# Question 4: Top Selling Product Categories
elif question == "Top Selling Product Categories":
    top_categories = order_items.merge(products, on='product_id')['product_category_name'].value_counts().head(10)

    # Visualization
    plt.figure(figsize=(10, 6))
    sns.barplot(x=top_categories.index, y=top_categories.values, palette="magma")
    plt.title("Top Selling Product Categories")
    plt.ylabel('Number of Items Sold')
    plt.xlabel('Product Category')
    plt.xticks(rotation=45)
    st.pyplot(plt)
    st.write("""
        The chart shows the top-selling product categories based on the number of items sold.
    """)

# Question 5: Customer Distribution by Geolocation
elif question == "Customer Distribution by Geolocation":
    customers_silver = customers.merge(geolocation, left_on='customer_zip_code_prefix', right_on='geolocation_zip_code_prefix')

    # Create a folium map to visualize geolocation data
    m = folium.Map(location=[-14.2350, -51.9253], zoom_start=4)
    marker_cluster = MarkerCluster().add_to(m)
    for idx, row in customers_silver.iterrows():
        folium.Marker([row['geolocation_lat'], row['geolocation_lng']], 
                      popup=f"Zip Code: {row['geolocation_zip_code_prefix']}<br>City: {row['geolocation_city']}").add_to(marker_cluster)

    # Display the map
    folium_static(m)
    st.write("""
        The map shows customer distribution across geolocations. This can help in optimizing logistics and targeted marketing.
    """)