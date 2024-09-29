import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

# Load datasets
customers = pd.read_csv('data/customers_dataset.csv')
geolocation = pd.read_csv('data/geolocation_dataset.csv')
order_items = pd.read_csv('data/order_items_dataset.csv')
order_payments = pd.read_csv('data/order_payments_dataset.csv')
order_reviews = pd.read_csv('data/order_reviews_dataset.csv')
orders = pd.read_csv('data/orders_dataset.csv')
products = pd.read_csv('data/products_dataset.csv')
sellers = pd.read_csv('data/sellers_dataset.csv')
category = pd.read_csv('data/product_category_name_translation.csv')

# Store datasets in a dictionary
data = {
    'customers': customers,
    'geo': geolocation,
    'items': order_items,
    'payments': order_payments,
    'reviews': order_reviews,
    'orders': orders,
    'products': products,
    'sellers': sellers,
    'category': category
}

# Handle missing values and duplicates
for df_name, df in data.items():
    if df_name == 'customers':
        data[df_name] = df.dropna(subset=['customer_id', 'customer_unique_id'])
    elif df_name == 'orders':
        data[df_name] = df.dropna(subset=['order_id', 'customer_id', 'order_purchase_timestamp'])
    elif df_name == 'order_items':
        data[df_name] = df.dropna(subset=['order_id', 'product_id', 'seller_id'])
    else:
        data[df_name] = df.ffill()
    data[df_name] = df.drop_duplicates()

# Define date columns based on your datasets
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

# Sidebar for date selection
st.sidebar.header("Date Range Selection")
min_date = data['orders']['order_purchase_timestamp'].min()
max_date = data['orders']['order_purchase_timestamp'].max()
start_date = st.sidebar.date_input("Start Date", min_value=min_date, max_value=max_date, value=min_date)
end_date = st.sidebar.date_input("End Date", min_value=min_date, max_value=max_date, value=max_date)

# Sidebar for question selection
st.sidebar.header("Select Analysis Question")
question = st.sidebar.selectbox("Choose a question:", [
    "Average Delivery Time by Zip Code and State",
    "Average Review Scores by Payment Method",
    "Top Selling Product Categories",
    "Customer Distribution by Geolocation"
])

# Filter data based on selected date range
filtered_orders = data['orders'][
    (data['orders']['order_purchase_timestamp'] >= pd.to_datetime(start_date)) &
    (data['orders']['order_purchase_timestamp'] <= pd.to_datetime(end_date))
]

# Question 1
if question == "Average Delivery Time by Zip Code and State":
    order_geo = filtered_orders.merge(customers, on='customer_id').merge(geolocation, left_on='customer_zip_code_prefix', right_on='geolocation_zip_code_prefix')
    order_geo['delivery_time'] = (pd.to_datetime(order_geo['order_delivered_customer_date']) - pd.to_datetime(order_geo['order_purchase_timestamp'])).dt.days
    delivery_time_by_zip = order_geo.groupby(['customer_zip_code_prefix', 'customer_state'])['delivery_time'].mean().reset_index()

    # Get top 10 zip codes based on average delivery time
    top_delivery_time = delivery_time_by_zip.nlargest(10, 'delivery_time')

    # visualization
    plt.figure(figsize=(12, 6))
    sns.barplot(data=top_delivery_time, x='customer_zip_code_prefix', y='delivery_time', hue='customer_state', palette='viridis')
    plt.title('Top 10 Average Delivery Time by Zip Code and State')
    plt.xlabel('Zip Code')
    plt.ylabel('Average Delivery Time (days)')
    plt.xticks(rotation=45)
    plt.ylim(0, top_delivery_time['delivery_time'].max() + 1) 
    plt.grid(axis='y', linestyle='--', alpha=0.7) 
    plt.legend(title='State')
    plt.tight_layout()
    st.pyplot(plt)
    st.write(""" 
        The graph shows the average delivery times for the top 10 zip codes within the selected date range. Areas with longer delivery times indicate regions that may require improved logistics solutions.
    """)

# Question 2
elif question == "Average Review Scores by Payment Method":
    payment_review = filtered_orders.merge(order_reviews, on='order_id').merge(order_payments, on='order_id')
    avg_review_by_payment = payment_review.groupby('payment_type')['review_score'].mean().reset_index()

    # Get top 10 payment types by average review score
    top_payment_reviews = avg_review_by_payment.nlargest(10, 'review_score')

    # Visualization
    plt.figure(figsize=(10, 6))
    sns.barplot(data=top_payment_reviews, x='payment_type', y='review_score', palette='coolwarm')
    plt.title('Average Review Scores by Payment Method (Top 10)')
    plt.xlabel('Payment Method')
    plt.ylabel('Average Review Score')
    plt.xticks(rotation=45)
    st.pyplot(plt)
    st.write("This bar chart shows the average review scores for the top 10 payment methods within the selected date range.")

# Question 3
elif question == "Top Selling Product Categories":
    order_items_products = pd.merge(data['items'], data['products'], on='product_id')
    filtered_items = order_items_products[order_items_products['order_id'].isin(filtered_orders['order_id'])]
    top_categories = filtered_items['product_category_name'].value_counts().head(10)

    # Visualization
    plt.figure(figsize=(10, 6))
    sns.barplot(x=top_categories.index, y=top_categories.values, palette="magma")
    plt.title("Top Selling Product Categories")
    plt.ylabel('Number of Items Sold')
    plt.xlabel('Product Category')
    plt.xticks(rotation=45)
    st.pyplot(plt)
    st.write("This chart displays the top selling product categories within the selected date range.")

# Question 4
elif question == "Customer Distribution by Geolocation":
    customers_geo = data['geo'].groupby(['geolocation_zip_code_prefix', 'geolocation_state'])[['geolocation_lat', 'geolocation_lng']].mean().reset_index()
    
    # Get top 10 states by customer count
    top_states = customers_geo['geolocation_state'].value_counts().nlargest(10).index
    filtered_geo = customers_geo[customers_geo['geolocation_state'].isin(top_states)]

    # Visualization
    plt.figure(figsize=(10, 8))
    sns.scatterplot(data=filtered_geo, x='geolocation_lng', y='geolocation_lat', hue='geolocation_state', palette='coolwarm', s=100, edgecolor='k', alpha=0.6)
    plt.title('Customer Distribution by Geolocation (Top 10 States)')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    st.pyplot(plt)
    st.write("This scatter plot shows the distribution of customers across the top 10 states within the selected date range.")