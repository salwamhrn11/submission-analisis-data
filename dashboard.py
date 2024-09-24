import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st

# load datasets
customers = pd.read_csv('data/customers_dataset.csv')
geolocation = pd.read_csv('data/geolocation_dataset.csv')
order_items = pd.read_csv('data/order_items_dataset.csv')
order_payments = pd.read_csv('data/order_payments_dataset.csv')
order_reviews = pd.read_csv('data/order_reviews_dataset.csv')
orders = pd.read_csv('data/orders_dataset.csv')
products = pd.read_csv('data/products_dataset.csv')
sellers = pd.read_csv('data/sellers_dataset.csv')
category = pd.read_csv('data/product_category_name_translation.csv')

# store datasets in a dictionary
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

# handle missing values and duplicates
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

# define date columns based on your datasets
date_columns = ['order_purchase_timestamp', 'order_approved_at', 
                'order_delivered_carrier_date', 'order_delivered_customer_date', 
                'order_estimated_delivery_date', 'review_creation_date', 
                'review_answer_timestamp']

# convert date columns to datetime type
for df_name, df in data.items():
    for col in date_columns:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce')

# streamlit app
st.title("E-commerce Data Analysis Dashboard")

# sidebar for question selection
st.sidebar.header("Select Analysis Question")
question = st.sidebar.selectbox("Choose a question:", [
    "Average Delivery Time by Zip Code and State",
    "Average Review Scores by Payment Method",
    "Correlation Between Number of Reviews and Revenue by Product Category",
    "Top Selling Product Categories",
    "Customer Distribution by Geolocation"
])

# question 1
if question == "Average Delivery Time by Zip Code and State":
    order_geo = orders.merge(customers, on='customer_id').merge(geolocation, left_on='customer_zip_code_prefix', right_on='geolocation_zip_code_prefix')
    order_geo['delivery_time'] = (pd.to_datetime(order_geo['order_delivered_customer_date']) - pd.to_datetime(order_geo['order_purchase_timestamp'])).dt.days
    delivery_time_by_zip = order_geo.groupby(['customer_zip_code_prefix', 'customer_state'])['delivery_time'].mean().reset_index()

    # set range for zip codes
    zip_range = st.slider("Select Zip Code Range", min_value=int(delivery_time_by_zip['customer_zip_code_prefix'].min()), max_value=int(delivery_time_by_zip['customer_zip_code_prefix'].max()), value=(10000, 99999))
    filtered_data = delivery_time_by_zip[(delivery_time_by_zip['customer_zip_code_prefix'] >= zip_range[0]) & (delivery_time_by_zip['customer_zip_code_prefix'] <= zip_range[1])]

    # visualization
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
        The graph shows that average delivery times vary significantly by zip code and state. While some regions, such as São Paulo (SP) and Rio de Janeiro (RJ), 
        generally have shorter delivery times, there are outliers with longer durations.
         Other states, like Amazonas (AM) and Roraima (RR),consistently have longer delivery times due to geographical challenges. To improve 
         delivery efficiency, consider optimizing routes based on these patterns, investing in infrastructure in remote areas, and partnering with local 
         logistics providers to improve last-mile delivery.
        """)

# question 2
elif question == "Average Review Scores by Payment Method":
    payment_review = orders.merge(order_reviews, on='order_id').merge(order_payments, on='order_id')
    avg_review_by_payment = payment_review.groupby('payment_type')['review_score'].mean().reset_index()

    # set range for review scores
    score_range = st.slider("Select Review Score Range", min_value=int(avg_review_by_payment['review_score'].min()), max_value=int(avg_review_by_payment['review_score'].max()), value=(0, 5))
    filtered_data = avg_review_by_payment[(avg_review_by_payment['review_score'] >= score_range[0]) & (avg_review_by_payment['review_score'] <= score_range[1])]

    # visualization
    plt.figure(figsize=(10, 6))
    sns.barplot(data=filtered_data, x='payment_type', y='review_score', palette='coolwarm')
    plt.title('Average Review Scores by Payment Method')
    plt.xlabel('Payment Method')
    plt.ylabel('Average Review Score')
    plt.xticks(rotation=45)
    st.pyplot(plt)
    st.write("""
            The bar chart shows that customers using credit cards and vouchers tend to have higher average review scores compared to those using boleto or debit cards.
            This suggests that these payment methods may be associated with a more positive customer experience. To improve overall customer satisfaction, consider 
            analyzing the reasons for lower review scores associated with specific payment methods and taking steps to address any underlying issues. This could involve 
            improving the payment process, providing better customer support, or offering incentives for using certain payment methods.          
            """)

# question 3
elif question == "Correlation Between Number of Reviews and Revenue by Product Category":
    revenue_reviews = order_items.merge(products, on='product_id').merge(order_reviews, on='order_id')
    category_revenue = revenue_reviews.groupby('product_category_name')['price'].sum().reset_index()
    category_reviews = revenue_reviews.groupby('product_category_name')['review_id'].count().reset_index()
    category_summary = category_revenue.merge(category_reviews, on='product_category_name')
    category_summary.columns = ['product_category_name', 'total_revenue', 'total_reviews']

    # set range for total revenue and reviews
    revenue_range = st.slider("Select Revenue Range", min_value=int(category_summary['total_revenue'].min()), max_value=int(category_summary['total_revenue'].max()), value=(0, category_summary['total_revenue'].max()))
    reviews_range = st.slider("Select Reviews Range", min_value=int(category_summary['total_reviews'].min()), max_value=int(category_summary['total_reviews'].max()), value=(0, category_summary['total_reviews'].max()))
    filtered_data = category_summary[(category_summary['total_revenue'] >= revenue_range[0]) & (category_summary['total_revenue'] <= revenue_range[1]) &
                                     (category_summary['total_reviews'] >= reviews_range[0]) & (category_summary['total_reviews'] <= reviews_range[1])]

    # visualization
    plt.figure(figsize=(12, 6))
    sns.scatterplot(data=filtered_data, x='total_reviews', y='total_revenue', hue='product_category_name', palette='Set1', s=100)
    plt.title('Correlation Between Number of Reviews and Revenue by Product Category')
    plt.xlabel('Number of Reviews')
    plt.ylabel('Total Revenue')
    plt.legend(title='Product Category', bbox_to_anchor=(1.05, 1), loc='upper left')
    st.pyplot(plt)
    st.write(
        """
        The scatter plot shows a general positive correlation between the number of reviews and total revenue across most product categories. However, there are outliers with high revenue but relatively few reviews, 
        suggesting other factors may influence sales. Categories like "informatica_acessorios" (Computer and accessories) and "eletronicos" (Electronics) consistently generate high revenue, often with a 
        significant number of reviews. Analyzing these patterns can help identify product categories with potential for growth and inform marketing strategies to increase both reviews and revenue.
    """
    )

# question 4
elif question == "Top Selling Product Categories":
    order_items_products = pd.merge(data['items'], data['products'], on='product_id')
    top_categories = order_items_products['product_category_name'].value_counts().head(10)

    # visualization
    plt.figure(figsize=(10, 6))
    sns.barplot(x=top_categories.index, y=top_categories.values, palette="magma")
    plt.title("Top Selling Product Categories")
    plt.ylabel('Number of Items Sold')
    plt.xlabel('Product Category')
    plt.xticks(rotation=45)
    st.pyplot(plt)
    st.write(
        """
        Based on the chart, "cama_mesa_banho" (Beds, tables, and bathroom) is the top-selling product category. To optimize product offerings, focus on increasing inventory and variety for high-performing 
        categories, analyze and improve underperforming ones, leverage data insights, and enhance customer experience.
        """
    )

# question 5
elif question == "Customer Distribution by Geolocation":
    other_state_geolocation = data['geo'].groupby(['geolocation_zip_code_prefix'])['geolocation_state'].nunique().reset_index(name='count')
    other_state_geolocation[other_state_geolocation['count'] >= 2].shape
    max_state = data['geo'].groupby(['geolocation_zip_code_prefix', 'geolocation_state']).size().reset_index(name='count').drop_duplicates(subset='geolocation_zip_code_prefix').drop('count', axis=1)
    geolocation_silver = data['geo'].groupby(['geolocation_zip_code_prefix', 'geolocation_city', 'geolocation_state'])[['geolocation_lat', 'geolocation_lng']].median().reset_index()
    geolocation_silver = geolocation_silver.merge(max_state, on=['geolocation_zip_code_prefix', 'geolocation_state'], how='inner')
    customers_silver = data['customers'].merge(geolocation_silver, left_on='customer_zip_code_prefix', right_on='geolocation_zip_code_prefix', how='inner')

    # visualization
    plt.figure(figsize=(10, 8))
    sns.scatterplot(data=customers_silver, x='geolocation_lng', y='geolocation_lat', hue='geolocation_state', palette='coolwarm', s=100, edgecolor='k', alpha=0.6)
    plt.title('Customer Distribution by Geolocation')
    plt.xlabel('Longitude')
    plt.ylabel('Latitude')
    st.pyplot(plt)
    st.write(
        """
The scatter plot shows a concentration of customer orders in the southeastern regions of Brazil, particularly in São Paulo (SP), Minas Gerais (MG), Rio de Janeiro (RJ), Paraná (PR), and Santa Catarina (SC).
 To improve delivery efficiency, consider optimizing delivery routes within these regions, establishing regional distribution centers, and partnering with local logistics providers.
        """
    )