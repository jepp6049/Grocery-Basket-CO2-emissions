import pandas as pd
import streamlit as st
from bs4 import BeautifulSoup
import requests
import altair as alt
import random
from datetime import datetime, timedelta

# Set page configuration
st.set_page_config(page_title="Grocery Basket CO2 Emission", page_icon=':bar_chart:', initial_sidebar_state='expanded')

# Cache the data loading function
@st.cache_data()
def get_concito_data():
    url = 'https://denstoreklimadatabase.dk/en'
    r = requests.get(url).text

    soup = BeautifulSoup(r, 'html.parser')

    # Find the table by its class
    table = soup.find('table', class_='cols-9 responsive-enabled sticky-enabled')

    if table:
        # Extract table headers
        headers = [header.text.strip() for header in table.find_all('th')]

        rows = []
        for row in table.find_all('tr')[1:]:  # Skip the header row
            cells = row.find_all('td')
            row_data = [cell.text.strip() for cell in cells]
            rows.append(row_data)

        # Convert to a pandas DataFrame
        df = pd.DataFrame(rows, columns=headers)
        # Clean and convert numeric columns
        numeric_columns = ["CO2e pr kg", "Agriculture", "ILUC", "Processing", "Packaging", "Transport", "Retail"]
        for col in numeric_columns:
            if col in df.columns:  # Ensure column exists
                # Replace ',' with '.' and convert to numeric
                df[col] = df[col].str.replace(',', '.', regex=False)
                df[col] = pd.to_numeric(df[col], errors="coerce")  # Convert to numeric, setting invalid entries to NaN
        return df
    else:
        return None

# Function to create Altair charts
def create_chart(data, x_col, y_col, title, color_col=None, color_title="Category", color_scheme="tableau10", width=800, height=400):
    chart = alt.Chart(data).mark_bar().encode(
        x=alt.X(f"{x_col}:N", sort=None, title=x_col),
        y=alt.Y(f"{y_col}:Q", title=y_col),
        tooltip=[x_col, y_col] + ([color_col] if color_col else [])
    )
    
    if color_col:
        chart = chart.encode(
            color=alt.Color(f"{color_col}:N", legend=alt.Legend(title=color_title, orient='top'), scale=alt.Scale(scheme=color_scheme))
        )
    
    chart = chart.properties(
        title=title,
        width=width,
        height=height
    )
    
    return chart

# Load the data once and store it in session state
if "emission_data" not in st.session_state:
    st.session_state.emission_data = get_concito_data()

# Sidebar navigation
page_navigation = st.sidebar.radio("Select function:", ["Introduction", "Calculate emissions of last basket", "See the database", "See your trends over time"])

if page_navigation == "Introduction":
    st.title("Welcome to the Grocery Basket CO2 Emissions App :apple:")
    st.header("Introduction to Climate Data and Food Choices")

    st.markdown("""

    ### **About the Climate Database**
    The data used in this app comes from **Den Store Klimadatabase**, developed by CONCITO, Denmark's green think tank, in collaboration with 2.-0 LCA Consultants. The database provides lifecycle assessments of the climate impact of over **500 common food items**. 🌍

    **Key Information:**
    - The climate impact is measured in **kg CO2-equivalents (CO2e) per kg of product** (net weight).
    - It includes greenhouse gases like CO2, methane, and nitrous oxide, as well as the indirect impact of land use changes caused by food production.
    - The database is freely accessible and supports general information and education about the climate impact of food.

    ### **What Can You Do with This App?**
    This app allows you to:
    1. **Calculate Emissions of Your Grocery Basket** 🛒  
    Input the products you purchased and get an overview of their climate impact.
    2. **Explore the Climate Database** 📊  
    Visualize average emissions by category and discover the most and least polluting food items.
    3. **Track Your Trends Over Time** 📈  
    Analyze your grocery basket trends to make more climate-conscious choices.

    ### **Limitations of the Data**
    While the database is one of the most detailed and accurate tools available, it's important to note:
    - The data reflects **average climate impact** and does not account for variability within each product type.
    - It is not suitable for **climate labeling, marketing, or taxation** of specific products.
    - It does not consider other sustainability factors, such as social or economic impacts, nor does it provide dietary advice.

    ---

    ### **Learn More**
    This app is built on data from version 1.2 of Den Store Klimadatabase. To explore the full dataset and methodology, visit [thebigclimatedatabase.com](https://thebigclimatedatabase.com) or [CONCITO's website](https://denstoreklimadatabase.dk).

    Together, we can make informed choices and contribute to a sustainable future! 🌿
    """)
elif page_navigation == "Calculate emissions of last basket":
    st.title("Input the products of your last grocery basket, and the app will calculate the emission of the products in the basket")
    
    # Initialize the basket DataFrame
    if "last_basket" not in st.session_state:
        st.session_state.last_basket = pd.DataFrame(columns=['Category', 'Food', 'CO2e pr kg', 'Agriculture', 
                                                             'ILUC', 'Processing', 'Packaging', 'Transport', 'Retail'])
    
    st.header('Select Category of Product: ')
    cat_basket = st.selectbox("Category: ", st.session_state.emission_data["Category"].unique())

    st.subheader('Product Name: ')
    product_basket = st.selectbox("Product: ", st.session_state.emission_data[st.session_state.emission_data["Category"] == cat_basket]["Food"].unique())

    # Add the selected product to the last_basket DataFrame
    if st.button("Add to Basket"):
        selected_row = st.session_state.emission_data[st.session_state.emission_data["Food"] == product_basket]
        st.session_state.last_basket = pd.concat([st.session_state.last_basket, selected_row], ignore_index=True)
        st.success(f"Added {product_basket} to your basket!")

    if not st.session_state.last_basket.empty:
        numeric_columns = ['CO2e pr kg', 'Agriculture', 'ILUC', 'Processing', 'Packaging', 'Transport', 'Retail']
        totals = st.session_state.last_basket[numeric_columns].sum()
            
        total_row = pd.DataFrame({
                "Category": ["Total"],
                "Food": [""],
                "CO2e pr kg": [totals['CO2e pr kg']],
                "Agriculture": [totals['Agriculture']],
                "ILUC": [totals['ILUC']],
                "Processing": [totals['Processing']],
                "Packaging": [totals['Packaging']],
                "Transport": [totals['Transport']],
                "Retail": [totals['Retail']]
        })

        # Add total row to the basket
        basket_with_total = pd.concat([st.session_state.last_basket, total_row], ignore_index=True)
    else:
        basket_with_total = st.session_state.last_basket
    st.subheader("Your Basket:")
    st.dataframe(basket_with_total)
    if not st.session_state.last_basket.empty:
        st.header("📊 Basket Dashboard")
        
        # Total CO2 emissions
        col1, col2, col3 = st.columns(3)
        with col1:
            total_emissions = st.session_state.last_basket["CO2e pr kg"].sum()
            st.metric("Total CO2 Emissions (kg CO2e)", f"{total_emissions:.2f}")
        with col2:
            total_items = st.session_state.last_basket.Food.nunique()
            st.metric("Total items in basket: ", total_items)
        with col3:
            avg_emissions = st.session_state.last_basket["CO2e pr kg"].mean()
            st.metric("Average CO2 Emissions (kg CO2e per item)", f"{avg_emissions:.2f}")

        # Most polluting item
        most_polluting = st.session_state.last_basket.loc[
            st.session_state.last_basket["CO2e pr kg"].idxmax()
        ]
        st.subheader("🌟 Most Polluting Item")
        st.write(f"**{most_polluting['Food']}** from category **{most_polluting['Category']}** with {most_polluting['CO2e pr kg']} kg CO2e.")

        # Emission breakdown by category
        st.subheader("📂 Emission Breakdown by Category")
        emissions_by_category = (
            st.session_state.last_basket.groupby("Category")["CO2e pr kg"].sum().reset_index()
        )
        emissions_chart = alt.Chart(emissions_by_category).mark_bar().encode(
            x=alt.X("Category:N", sort="-y", title="Category"),
            y=alt.Y("CO2e pr kg:Q", title="Total CO2e Emissions"),
            tooltip=["Category", "CO2e pr kg"]
        ).properties(
            title="Total Emissions by Product Category",
            width=800,
            height=400
        )
        st.altair_chart(emissions_chart, use_container_width=True)

        # Breakdown of individual contributions
        st.subheader("📊 Breakdown of Emissions by Items")
        chart = create_chart(st.session_state.last_basket, "Food", "CO2e pr kg", "Breakdown of Emission", 
                             color_col="Category")
        st.altair_chart(chart, use_container_width=True)
       

elif page_navigation == "See the database":
    st.header("Breakdown of CO2e for different Categories of Products")
    # Show the cached data
    if st.session_state.emission_data is not None:
        st.header("See the data")
        specific_cats = st.radio("Do you want to look at specific categories?", ["Yes", "No"])
        if specific_cats == "Yes":
            categories = st.multiselect("Choose the categorie(s) you want to assess: ", st.session_state.emission_data.Category.unique())
            st.data_editor(st.session_state.emission_data[st.session_state.emission_data.Category.isin(categories)])
        elif specific_cats == "No":
            st.data_editor(st.session_state.emission_data)
        grouped_data = st.session_state.emission_data.groupby('Category')['CO2e pr kg'].mean().reset_index()
        sorted_data = grouped_data.sort_values(by='CO2e pr kg', ascending=False)

        st.header("CO2e pr kg pr. category")
        # Use the function to create and display a chart
        chart = create_chart(
            data=sorted_data,
            x_col="Category",
            y_col="CO2e pr kg",
            title="Average Emissions by Category",
            color_col=None
        )
        st.altair_chart(chart, use_container_width=True)

        st.header("Individual Products")
        choice = st.radio("Do you want to see the most or least polluting products?", ["Most", "Least"])

        st.subheader(f"The 20 {choice} polluting products in the database")
        if choice == "Most":
            selected_data = st.session_state.emission_data.sort_values(by='CO2e pr kg', ascending=False)[:20]
        elif choice == "Least":
            selected_data = st.session_state.emission_data.sort_values(by='CO2e pr kg', ascending=True)[:20]

        # Use the function to create and display a chart for most/least polluting products
        chart_title = f"Top 20 {choice} Polluting Products"
        product_chart = create_chart(
            data=selected_data,
            x_col="Food",
            y_col="CO2e pr kg",
            title=chart_title,
            color_col="Category"
        )
        st.altair_chart(product_chart, use_container_width=True)



    else:
        st.warning("No data found. Please check the database URL or table structure.")

elif page_navigation == "See your trends over time":
    st.title("Your basket emissions over time")
    st.header("You can either upload a dataset of your own, or generate random data: ")
    upload_random = st.selectbox("Upload or generate data: ", ["Upload", "Generate"])

    if upload_random=="Upload":
        st.session_state.historical_data = st.file_uploader("Upload your csv data here: ", type='csv')

    elif upload_random=="Generate":
        st.session_state.historical_data=pd.DataFrame(columns=["Date of Purchase", "Product", "Category", "C02e pr kg",
                                                               "Agriculture", "ILUC","Processing", "Packaging","Transport","Retail"])
        start_date = st.date_input("Select start date: ", datetime.today())
        end_date = st.date_input("Select end date: ", datetime.today())
        observations = st.slider("How many baskets should the dataset include?", 1, 50)

        max_items_basket = st.slider("Max items in basket: ", 1, 30)
        if start_date is not None and end_date is not None:
            if start_date > end_date:
                st.warning("Start date is after end date. Try again.")
            else:
                used_dates = set()  # Keep track of used dates

                for _ in range(observations):
                    # Generate a unique random date within the range
                    delta = end_date - start_date
                    random_date = None
                    while random_date is None or random_date in used_dates:
                        random_days = random.randint(0, delta.days)
                        random_date = start_date + timedelta(days=random_days)

                    used_dates.add(random_date)  # Mark the date as used

                    # Generate a random number of items for the basket
                    items_in_basket = random.randint(1, max_items_basket)

                    for _ in range(items_in_basket):
                        # Select a random row from the emission_data
                        random_index = random.randint(0, len(st.session_state.emission_data) - 1)
                        random_item = st.session_state.emission_data.iloc[random_index]

                        # Append the item as a new row
                        new_row = {
                            "Date of Purchase": random_date,
                            "Product": random_item["Food"],
                            "Category": random_item["Category"],
                            "C02e pr kg": random_item["CO2e pr kg"],
                            "Agriculture": random_item["Agriculture"],
                            "ILUC": random_item["ILUC"],
                            "Processing": random_item["Processing"],
                            "Packaging": random_item["Packaging"],
                            "Transport": random_item["Transport"],
                            "Retail": random_item["Retail"],
                        }
                        st.session_state.historical_data = pd.concat(
                            [st.session_state.historical_data, pd.DataFrame([new_row])],
                            ignore_index=True
                        )

                st.success("Successfully generated data.")
                basket_wise_metrics = (
                        st.session_state.historical_data.groupby("Date of Purchase").agg(
                            no_of_items=("Product", "count"),  
                            avg_co2e=("C02e pr kg", "mean"),  
                            total_co2e=("C02e pr kg", "sum")  
                        ).reset_index()
                    )
                basket_wise_metrics["Date of Purchase"] = pd.to_datetime(basket_wise_metrics["Date of Purchase"])
                basket_or_dataset = st.radio("See basket summary or all datapoints", ["Basket", "All data"])
                if basket_or_dataset == "All data":
                    st.data_editor(st.session_state.historical_data)
                elif basket_or_dataset == "Basket":
                    st.data_editor(basket_wise_metrics)

                if st.button("Show dashboard"):
                    # Get the latest basket
                    last_observation = st.session_state.historical_data["Date of Purchase"].max()
                    last_basket_data = st.session_state.historical_data[
                        st.session_state.historical_data["Date of Purchase"] == last_observation]

                    # Display metrics
                    latest_total_co2e = last_basket_data["C02e pr kg"].sum()
                    average_total_co2e = basket_wise_metrics["total_co2e"].mean()

                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total CO2e (kg) of Latest Basket", f"{latest_total_co2e:.2f}", f"{average_total_co2e - latest_total_co2e:.2f}")
                    with col2:
                        st.metric("Average Total CO2e (kg) Across All Baskets", f"{average_total_co2e:.2f}")

                    # Display basket-wise metrics table
                    st.subheader("Average CO2e per Basket Over Time")
                    line_chart = alt.Chart(basket_wise_metrics).mark_line(point=True).encode(
                        x=alt.X("Date of Purchase:T", title="Date of Purchase"),
                        y=alt.Y("avg_co2e:Q", title="Avg. CO2e of Basket"),
                        tooltip=["Date of Purchase:T", "avg_co2e:Q"]
                    ).properties(
                        title="Trend of CO2e Over Time",
                        width=800, 
                        height=600
                    )
                    st.altair_chart(line_chart, use_container_width=True)

                    st.subheader("Total CO2e Contribution by Category (as Percentages)")
                    category_emissions = (
                        st.session_state.historical_data.groupby("Category")["C02e pr kg"]
                        .sum()
                        .reset_index()
                    )
                    category_emissions["percentage"] = (
                        category_emissions["C02e pr kg"] / category_emissions["C02e pr kg"].sum() * 100
                    )

                    bar_chart = alt.Chart(category_emissions).mark_bar().encode(
                        x=alt.X("percentage:Q", title="Percentage Contribution (%)"),
                        y=alt.Y("Category:N", sort="-x", title="Category"),
                        tooltip=["Category:N", "percentage:Q", "C02e pr kg:Q"]  # Include percentage and total CO2e in tooltip
                    ).properties(
                        title="Total CO2e Contribution by Category (as Percentages)",
                        width=800,
                        height=400
                    )

                    # Display the chart
                    st.altair_chart(bar_chart, use_container_width=True)

                    # Scatter Plot: Basket Size vs Total CO2e
                    st.subheader("Basket Size vs Total CO2e")
                    scatter_chart = alt.Chart(basket_wise_metrics).mark_circle(size=60).encode(
                        x=alt.X("no_of_items:Q", title="Number of Items in Basket"),
                        y=alt.Y("total_co2e:Q", title="Total CO2e (kg)"),
                        tooltip=["Date of Purchase", "no_of_items", "total_co2e"]
                    ).properties(
                        title="Basket Size vs Total CO2e",
                        width=800,
                        height=400
                    )
                    st.altair_chart(scatter_chart, use_container_width=True)

                    st.subheader("Top 10 Most Polluting Products")
                    top_products = (
                        st.session_state.historical_data.groupby("Product")
                        .agg(
                            total_co2e=("C02e pr kg", "sum"),
                            frequency=("Product", "count")
                        )
                        .reset_index()
                        .sort_values(by="total_co2e", ascending=False)
                        .head(10)
                    )
                    opacity_values = list(range(1, top_products["frequency"].max() + 1))
                    top_products_chart = alt.Chart(top_products).mark_bar().encode(
                        x=alt.X("total_co2e:Q", title="Total CO2e (kg)"),
                        y=alt.Y("Product:N", sort="-x", title="Product"),
                        tooltip=["Product:N", "total_co2e:Q", "frequency:Q"], 
                            opacity=alt.Opacity("frequency:Q", scale=alt.Scale(domain=[1, top_products["frequency"].max()],
                                                                            type="ordinal",nice=False), title="Frequency")).properties(
                        title="Top 10 Most Polluting Products",
                        width=800,
                        height=400
                    )
                    st.altair_chart(top_products_chart, use_container_width=True)

                    # Lifecycle Emissions Breakdown
                    st.subheader("Lifecycle Emissions Breakdown")
                    lifecycle_emissions = st.session_state.historical_data[["Agriculture", "ILUC", "Processing", "Packaging", "Transport", "Retail"]].sum().reset_index()
                    lifecycle_emissions.columns = ["Stage", "Emissions"]
                    lifecycle_chart = alt.Chart(lifecycle_emissions).mark_bar().encode(
                        x=alt.X("Stage:N", title="Lifecycle Stage"),
                        y=alt.Y("Emissions:Q", title="Total CO2e (kg)"),
                        tooltip=["Stage", "Emissions"]
                    ).properties(
                        title="Lifecycle Emissions Breakdown",
                        width=800,
                        height=400
                    )
                    st.altair_chart(lifecycle_chart, use_container_width=True)

            
