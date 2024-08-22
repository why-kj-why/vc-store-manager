import streamlit as st
import pandas as pd
import pymysql
import plotly.express as px
import time

DB_HOST = "tellmoredb.cd24ogmcy170.us-east-1.rds.amazonaws.com"
DB_USER = "admin"
DB_PASS = "2yYKKH8lUzaBvc92JUxW"
DB_PORT = "3306"
DB_NAME = "retail_panopticon"
CONVO_DB_NAME = "store_questions"

if 'history' not in st.session_state:
    st.session_state['history'] = []

if 'display_df_and_nlr' not in st.session_state:
    st.session_state['display_df_and_nlr'] = False

if 'user_input' not in st.session_state:
    st.session_state['user_input'] = ""

personas = [
    "Select a Persona",
    "INVENTORY OPS",
    "LOSS PREVENTION OPS",
    "MARKETING OPS",
    "STORE OPS",
    "MERCHANDISING OPS",
    "WAREHOUSE OPS"
]


def connect_to_db(db_name):
    return pymysql.connect(
        host=DB_HOST,
        port=int(DB_PORT),
        user=DB_USER,
        password=DB_PASS,
        db=db_name
    )


def execute_query(query, connection):
    # try:
    with connection.cursor() as cursor:
        cursor.execute(query)
        getResult = cursor.fetchall()
        columns = [column[0] for column in cursor.description]
    return pd.DataFrame(getResult, columns=columns)
    # finally:
    #     connection.close()


def get_queries_from_db(persona):
    connection = connect_to_db(CONVO_DB_NAME)
    query = f"SELECT DISTINCT question, sql_query FROM {persona}_questions;"
    df = execute_query(query, connection)
    questions = {"Select a query": None}
    questions.update(dict(zip(df['question'], df['sql_query'])))
    return questions


def set_custom_css():
    custom_css = """
    <style>
        .st-emotion-cache-9aoz2h.e1vs0wn30 {
            display: flex;
            justify-content: center; /* Center-align the DataFrame */
        }
        .st-emotion-cache-9aoz2h.e1vs0wn30 table {
            margin: 0 auto; /* Center-align the table itself */
        }
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)


def create_figures(data, query):
    if query == "Give a daily breakdown UPT for all product categories for each store during May":
        pie_fig = px.pie(
            data,
            values='UPT',
            names='Product_Category',
            title='Sum of UPT by Product Category'
        )

        bar_fig = px.bar(
            data,
            x='UPT',
            y='Store_ID',
            orientation='h',  # Horizontal bar chart
            title='Sum of UPT by Store_ID'
        )
        bar_fig.update_layout(yaxis={'categoryorder': 'total ascending'})  # Sort bars by UPT

        filtered_data = data[data['Product_Category'].isin(['Clothing', 'Toys'])]
        line_fig = px.line(
            filtered_data,
            x='Sale_Date',
            y='UPT',
            color='Product_Category',
            title='Product Category Sales report'
        )
        line_fig.update_layout(
            xaxis_title='Sale_Date',
            yaxis_title='Sum of UPT',
            legend_title='Product Category'
        )

        figures = [pie_fig, bar_fig, line_fig]
        return figures

    if query == "What was the impact of the promotional discounts offered in May on the weekend vs. weekday sales for all product categories?":
        total_sales_per_category = data.groupby('Category')['total_sales'].sum().reset_index()
        df = data.merge(total_sales_per_category, on='Category', suffixes=('', '_total'))
        fig2 = px.bar(
            df,
            y='Category',
            x='total_sales',
            color='day_type',
            title='Total Sales for Each Product Category',
            labels={'total_sales': 'Total Sales', 'Category': 'Product Category'},
            barmode='group',
            orientation='h',
            color_discrete_map={'Weekday': 'goldenrod', 'Weekend': 'dodgerblue'}
        )

        fig3 = px.bar(
            df,
            x='Category',
            y='avg_transaction_value',
            color='day_type',
            title='Average Transaction Value for Each Product Category',
            labels={'avg_transaction_value': 'Average Transaction Value', 'Category': 'Product Category'},
            barmode='stack',
            text_auto=True,
            color_discrete_map={'Weekday': 'orange', 'Weekend': 'purple'}
        )

        total_sales_per_category = data.groupby('Category')['total_sales'].sum().reset_index()
        df = data.merge(total_sales_per_category, on='Category', suffixes=('', '_total'))
        df['sales_percentage'] = df['total_sales'] / df['total_sales_total'] * 100
        fig = px.bar(
            df,
            x='Category',
            y='sales_percentage',
            color='day_type',
            title='Total Sales Percentage for Each Product Category',
            labels={'sales_percentage': 'Percentage of Total Sales', 'Category': 'Product Category'},
            text_auto=True,
            barmode='stack'
        )

        fig1 = px.bar(
            df,
            y='Category',
            x='total_transactions',
            color='day_type',
            title='Total Transactions for Each Product Category',
            labels={'total_transactions': 'Total Transactions', 'Category': 'Product Category'},
            barmode='group',
            orientation='h',
            color_discrete_map={'Weekday': 'mediumseagreen', 'Weekend': 'tomato'}
        )

        figures = [fig2, fig3, fig, fig1]
        return figures

    if query == "Give the total shipments delivered late and the reason for the delay for each product category":
        fig_pie = px.sunburst(
            data,
            path=['Category', 'Reason_Late_Shipment'],
            values='Total_Late_Shipments',
            title='Reasons for Late Shipments by Product Category',
            color='Reason_Late_Shipment',
            color_discrete_sequence=px.colors.qualitative.Set3
        )

        total_shipments_by_category = data.groupby('Category')['Total_Late_Shipments'].sum().reset_index()
        fig_bar = px.bar(
            total_shipments_by_category,
            y='Category',
            x='Total_Late_Shipments',
            title='Total Late Shipments by Product Category',
            labels={'Total_Late_Shipments': 'Total Late Shipments'},
            color='Category',
            color_discrete_sequence=px.colors.qualitative.Pastel  # Different color scheme for categories
        )

        figures = [fig_pie, fig_bar]
        return figures


def dynamic_figure_populate(list_of_figs):
    # Num plots:5
    # remaining_cols = [2,2,1]

    num_plots = len(list_of_figs)
    num_containers = num_plots // 2 + num_plots % 2
    print(f"Number of plots:{num_containers}")
    print(f"Number of containers:{num_containers}")
    remaining_cols = [2] * (num_plots // 2)
    if num_plots % 2 == 1:
        remaining_cols.append(num_plots % 2)
    print(f"column split:{remaining_cols}")
    # with streamlit_column:
    current_idx = 0
    for i in range(1, num_containers + 1):
        print(f"i: {i}")

        globals()[f'container_{i}'] = st.container()
        container = globals()[f'container_{i}']
        with container:
            cols = st.columns(remaining_cols[i - 1])
            for col_idx in range(len(cols)):
                print(f"current container column index: {col_idx}")
                with cols[col_idx]:
                    print(f"current_idx: {current_idx}")
                    if current_idx == num_plots:
                        break
                    st.plotly_chart(list_of_figs[current_idx])
                    current_idx += 1
    return


def management_app(persona, options):
    queries = get_queries_from_db(persona)
    st.markdown("""
            <style>
            div.stButton {
                display: flex;
                justify-content: flex-end; /* Align button to the right */
                margin-top: 10px;
            }
                
            /* Custom CSS for the dropdowns to align right and be smaller */
            div.streamlit-expander {
                width: 100%; /* Make sure it fills the container */
            }

            div.streamlit-expander > div {
                width: 30%; /* Set the width of the selectbox */
                margin-left: auto; /* Push it to the right */
            }
            
            /* Smaller font size for selectbox options */
            .stSelectbox div {
                font-size: 12px; /* Smaller font size */
            }

            </style>
            """, unsafe_allow_html=True)
    col1, col2 = st.columns([4, 1])  
    with col2:
        drop_down = st.selectbox("", options)
    unpin_button_pressed = st.button("DELETE", key='unpin_button')
    selected_query = st.selectbox("Select a query", queries if queries else ["Select a query"])
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    col = st.columns((1, 1), gap='medium')
    conn = connect_to_db(DB_NAME)

    with col[0]:
        #     st.markdown("""
        # <style>
        # div.stButton {
        #     display: flex;
        #     justify-content: flex-end; /* Align button to the right */
        #     margin-top: 10px;
        # }
        #
        # div.stButton > button:first-child {
        #     border-radius: 50%;
        #     background-color: #553D94; /* Button color */
        #     color: white;
        #     border: none;
        #     padding: 10px 15px; /* Adjust size as needed */
        #     cursor: pointer;
        # }
        # </style>
        # """, unsafe_allow_html=True)
        #     unpin_button_pressed = st.button("DELETE", key='unpin_button')
        #     st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        # drop_down = st.selectbox("Select", options)
        # selected_query = st.selectbox("Select a query", queries if queries else ["Select a query"])
        if unpin_button_pressed:
            if selected_query != "Select a query":
                queries.pop(selected_query, None)
                st.success(f"Query '{selected_query}' has been removed.")
            else:
                st.warning("Select a query to unpin.")

        if drop_down and selected_query and selected_query != "Select a query" and not unpin_button_pressed and drop_down != "SELECT STORE":
            # result = execute_query(queries[selected_query], conn)
            if selected_query == "Give a daily breakdown UPT for all product categories for each store during May":
                if drop_down == "WATER TOWER PLACE":
                    time.sleep(1)
                    st.markdown("""
                    Clothing:\tWATER TOWER PLACE has a UPT of 5.38 as compared to the average of 5.48\n
                    Electronics:\tWATER TOWER PLACE does not sell Electronics items\n
                    Food:\t\tWATER TOWER PLACE has a UPT of 5.64 as compared to the average of 5.51\n
                    Furniture:\tWATER TOWER PLACE has a UPT of 5.55 as compared to the average of 5.5\n
                    Toys:\t\tWATER TOWER PLACE does not sell Toys items\n
                    """)

                elif drop_down == "RIVERFRONT PLAZA":
                    time.sleep(1)
                    st.markdown("""
                    Clothing:\tRIVERFRONT PLAZA does not sell Clothing items\n
                    Electronics:\tRIVERFRONT PLAZA does not sell Electronics items\n
                    Food:\t\tRIVERFRONT PLAZA does not sell Food items\n
                    Furniture:\tRIVERFRONT PLAZA has a UPT of 5.46 as compared to the average of 5.5\n
                    Toys:\t\tRIVERFRONT PLAZA has a UPT of 5.58 as compared to the average of 5.48\n
                    """)

                elif drop_down == "WESTFIELD WHEATON":
                    time.sleep(1)
                    st.markdown("""
                    Clothing:\tWESTFIELD WHEATON has a UPT of 5.5 as compared to the average of 5.49\n
                    Electronics:\tWESTFIELD WHEATON does not sell Electronics items\n
                    Food:\t\tWESTFIELD WHEATON has a UPT of 5.55 as compared to the average of 5.51\n
                    Furniture:\tWESTFIELD WHEATON has a UPT of 5.47 as compared to the average of 5.5\n
                    Toys:\t\tWESTFIELD WHEATON has a UPT of 5.45 as compared to the average of 5.48\n
                    """)

            elif selected_query == "What was the impact of the promotional discounts offered in May on the weekend vs. weekday sales for all product categories?":
                if drop_down == "WATER TOWER PLACE":
                    time.sleep(1)
                    st.markdown("""
                    Clothing:\tWATER TOWER PLACE saw a 288% increase in sales during the weekdays following the weekends the promotions were launched\n
                    Electronics:\tWATER TOWER PLACE saw a 235% increase in sales during the weekdays following the weekends the promotions were launched\n
                    Food:\t\tWATER TOWER PLACE saw a 236% increase in sales during the weekdays following the weekends the promotions were launched\n
                    Furniture:\tWATER TOWER PLACE saw a 287% increase in sales during the weekdays following the weekends the promotions were launched\n
                    Toys:\t\tWATER TOWER PLACE saw a 272% increase in sales during the weekdays following the weekends the promotions were launched\n
                    """)

                elif drop_down == "RIVERFRONT PLAZA":
                    time.sleep(1)
                    st.markdown("""
                    Clothing:\tRIVERFRONT PLAZA saw a 230% increase in sales during the weekdays following the weekends the promotions were launched\n
                    Electronics:\tRIVERFRONT PLAZA saw a 300% increase in sales during the weekdays following the weekends the promotions were launched\n
                    Food:\t\tRIVERFRONT PLAZA saw a 256% increase in sales during the weekdays following the weekends the promotions were launched\n
                    Furniture:\tRIVERFRONT PLAZA saw a 255% increase in sales during the weekdays following the weekends the promotions were launched\n
                    Toys:\t\tRIVERFRONT PLAZA saw a 255% increase in sales during the weekdays following the weekends the promotions were launched\n
                    """)

                elif drop_down == "WESTFIELD WHEATON":
                    time.sleep(1)
                    st.markdown("""
                    Clothing:\tWESTFIELD WHEATON saw a 242% increase in sales during the weekdays following the weekends the promotions were launched\n
                    Electronics:\tWESTFIELD WHEATON saw a 332% increase in sales during the weekdays following the weekends the promotions were launched\n
                    Food:\t\tWESTFIELD WHEATON saw a 275% increase in sales during the weekdays following the weekends the promotions were launched\n
                    Furniture:\tWESTFIELD WHEATON saw a 231% increase in sales during the weekdays following the weekends the promotions were launched\n
                    Toys:\t\tWESTFIELD WHEATON saw a 298% increase in sales during the weekdays following the weekends the promotions were launched\n
                    """)

            elif selected_query == "Give the total shipments delivered late and the reason for the delay for each product category":
                if drop_down == "WATER TOWER PLACE":
                    time.sleep(1)
                    st.markdown("""
                    Clothing:\tWATER TOWER PLACE has no Delayed Shipments\n
                    Electronics:\tWATER TOWER PLACE has no Delayed Shipments\n
                    Food:\t\tWATER TOWER PLACE has no Delayed Shipments\n
                    Furniture:\tWATER TOWER PLACE has no Delayed Shipments\n
                    Toys:\t\tWATER TOWER PLACE has no Delayed Shipments\n
                    """)

                elif drop_down == "RIVERFRONT PLAZA":
                    time.sleep(1)
                    st.markdown("""
                    Clothing:\tRIVERFRONT PLAZA has no Delayed Shipments\n
                    Electronics:\tRIVERFRONT PLAZA has no Delayed Shipments\n
                    Food:\t\tRIVERFRONT PLAZA has no Delayed Shipments\n
                    Furniture:\tRIVERFRONT PLAZA has no Delayed Shipments\n
                    Toys:\t\tRIVERFRONT PLAZA has no Delayed Shipments\n
                    """)

                elif drop_down == "WESTFIELD WHEATON":
                    time.sleep(1)
                    st.markdown("""
                    Clothing:\tWESTFIELD WHEATON has no Delayed Shipments\n
                    Electronics:\tWESTFIELD WHEATON has no Delayed Shipments\n
                    Food:\t\tWESTFIELD WHEATON has no Delayed Shipments\n
                    Furniture:\tWESTFIELD WHEATON had 7055 delayed shipments, mostly due to Weather Conditions. On average, there were 7472 shipments delayed due to Weather Conditions in the same time frame.\n
                    Toys:\t\tWESTFIELD WHEATON has no Delayed Shipments\n
                    """)

    with col[1]:
        if selected_query and drop_down:
            if selected_query == "Give a daily breakdown UPT for all product categories for each store during May":
                if drop_down == "WATER TOWER PLACE":
                    result = execute_query(
                        "SELECT DATE(t.Date) AS Sale_Date, p.Category AS Product_Category, t.Store_ID, ROUND(SUM(t.Quantity) / COUNT(t.Transaction_ID), 2) AS UPT\nFROM retail_panopticon.transactions t\nJOIN retail_panopticon.productInformation p ON t.Product_ID = p.Product_ID\nWHERE t.Store_ID = 'STORE01' AND  t.Date BETWEEN '2024-05-01' AND '2024-05-31'\nGROUP BY DATE(t.Date), p.Category\nORDER BY DATE(t.Date), p.Category;",
                        conn)
                    l_figures = create_figures2(selected_query, drop_down)
                    dynamic_figure_populate(l_figures)

                elif drop_down == "RIVERFRONT PLAZA":
                    result = execute_query(
                        "SELECT DATE(t.Date) AS Sale_Date, p.Category AS Product_Category, t.Store_ID, ROUND(SUM(t.Quantity) / COUNT(t.Transaction_ID), 2) AS UPT\nFROM retail_panopticon.transactions t\nJOIN retail_panopticon.productInformation p ON t.Product_ID = p.Product_ID\nWHERE t.Store_ID = 'STORE28' AND  t.Date BETWEEN '2024-05-01' AND '2024-05-31'\nGROUP BY DATE(t.Date), p.Category\nORDER BY DATE(t.Date), p.Category;",
                        conn)
                    l_figures = create_figures2(selected_query, drop_down)
                    dynamic_figure_populate(l_figures)

                elif drop_down == "WESTFIELD WHEATON":
                    result = execute_query(
                        "SELECT DATE(t.Date) AS Sale_Date, p.Category AS Product_Category, t.Store_ID, ROUND(SUM(t.Quantity) / COUNT(t.Transaction_ID), 2) AS UPT\nFROM retail_panopticon.transactions t\nJOIN retail_panopticon.productInformation p ON t.Product_ID = p.Product_ID\nWHERE t.Store_ID = 'STORE49' AND  t.Date BETWEEN '2024-05-01' AND '2024-05-31'\nGROUP BY DATE(t.Date), p.Category\nORDER BY DATE(t.Date), p.Category;",
                        conn)
                    l_figures = create_figures2(selected_query, drop_down)
                    dynamic_figure_populate(l_figures)

            elif selected_query == "What was the impact of the promotional discounts offered in May on the weekend vs. weekday sales for all product categories?":
                if drop_down == "WATER TOWER PLACE":
                    result = execute_query(
                        "SELECT CASE WHEN DAYOFWEEK(S.date) IN (1, 7) THEN 'Weekend' ELSE 'Weekday' END AS day_type, P.Category,SUM(S.Total_Amount) AS total_sales, COUNT(DISTINCT S.Transaction_ID) AS total_transactions, AVG(S.Total_Amount) AS avg_transaction_value FROM transactions S JOIN productInformation P ON S.Product_ID = P.Product_ID WHERE S.Store_ID = 'STORE01' AND DATE_FORMAT(S.date, '%Y-%m') = '2024-05' GROUP BY day_type, P.Category ORDER BY day_type DESC, total_sales DESC;",
                        conn)
                    l_figures = create_figures2(selected_query, drop_down)
                    dynamic_figure_populate(l_figures)

                elif drop_down == "RIVERFRONT PLAZA":
                    result = execute_query(
                        "SELECT CASE WHEN DAYOFWEEK(S.date) IN (1, 7) THEN 'Weekend' ELSE 'Weekday' END AS day_type, P.Category,SUM(S.Total_Amount) AS total_sales, COUNT(DISTINCT S.Transaction_ID) AS total_transactions, AVG(S.Total_Amount) AS avg_transaction_value FROM transactions S JOIN productInformation P ON S.Product_ID = P.Product_ID WHERE S.Store_ID = 'STORE28' AND DATE_FORMAT(S.date, '%Y-%m') = '2024-05' GROUP BY day_type, P.Category ORDER BY day_type DESC, total_sales DESC;",
                        conn)
                    l_figures = create_figures2(selected_query, drop_down)
                    dynamic_figure_populate(l_figures)

                elif drop_down == "WESTFIELD WHEATON":
                    result = execute_query(
                        "SELECT CASE WHEN DAYOFWEEK(S.date) IN (1, 7) THEN 'Weekend' ELSE 'Weekday' END AS day_type, P.Category,SUM(S.Total_Amount) AS total_sales, COUNT(DISTINCT S.Transaction_ID) AS total_transactions, AVG(S.Total_Amount) AS avg_transaction_value FROM transactions S JOIN productInformation P ON S.Product_ID = P.Product_ID WHERE S.Store_ID = 'STORE49' AND DATE_FORMAT(S.date, '%Y-%m') = '2024-05' GROUP BY day_type, P.Category ORDER BY day_type DESC, total_sales DESC;",
                        conn)
                    l_figures = create_figures2(selected_query, drop_down)
                    dynamic_figure_populate(l_figures)

            elif selected_query == "Give the total shipments delivered late and the reason for the delay for each product category":
                if drop_down == "WATER TOWER PLACE":
                    result = execute_query(
                        "SELECT t.Store_ID, p.Category,s.Reason_Late_Shipment, COUNT(CASE WHEN s.Late_Shipment_Rate > 0 THEN t.Transaction_ID END) AS Total_Late_Shipments FROM transactions t JOIN productInformation p ON t.Product_ID = p.Product_ID JOIN shipmentPerformance s ON t.Transaction_ID = s.Transaction_ID WHERE t.Store_ID = 'STORE01' GROUP BY p.Category, s.Reason_Late_Shipment HAVING COUNT(CASE WHEN s.Late_Shipment_Rate > 0 THEN t.Transaction_ID END) > 0 ORDER BY Total_Late_Shipments DESC;",
                        conn)
                    l_figures = create_figures2(selected_query, drop_down)
                    dynamic_figure_populate(l_figures)

                elif drop_down == "RIVERFRONT PLAZA":
                    result = execute_query(
                        "SELECT t.Store_ID, p.Category,s.Reason_Late_Shipment, COUNT(CASE WHEN s.Late_Shipment_Rate > 0 THEN t.Transaction_ID END) AS Total_Late_Shipments FROM transactions t JOIN productInformation p ON t.Product_ID = p.Product_ID JOIN shipmentPerformance s ON t.Transaction_ID = s.Transaction_ID WHERE t.Store_ID = 'STORE28' GROUP BY p.Category, s.Reason_Late_Shipment HAVING COUNT(CASE WHEN s.Late_Shipment_Rate > 0 THEN t.Transaction_ID END) > 0 ORDER BY Total_Late_Shipments DESC;",
                        conn)
                    l_figures = create_figures2(selected_query, drop_down)
                    dynamic_figure_populate(l_figures)

                elif drop_down == "WESTFIELD WHEATON":
                    result = execute_query(
                        "SELECT t.Store_ID, p.Category,s.Reason_Late_Shipment, COUNT(CASE WHEN s.Late_Shipment_Rate > 0 THEN t.Transaction_ID END) AS Total_Late_Shipments FROM transactions t JOIN productInformation p ON t.Product_ID = p.Product_ID JOIN shipmentPerformance s ON t.Transaction_ID = s.Transaction_ID WHERE t.Store_ID = 'STORE49' GROUP BY p.Category, s.Reason_Late_Shipment HAVING COUNT(CASE WHEN s.Late_Shipment_Rate > 0 THEN t.Transaction_ID END) > 0 ORDER BY Total_Late_Shipments DESC;",
                        conn)
                    l_figures = create_figures2(selected_query, drop_down)
                    dynamic_figure_populate(l_figures)


def create_figures2(query, drop):
    conn = connect_to_db(DB_NAME)
    if query and drop:
        if query == "Give a daily breakdown UPT for all product categories for each store during May":
            if drop == "WATER TOWER PLACE":
                result = execute_query(
                    "SELECT DATE(t.Date) AS Sale_Date, p.Category AS Product_Category, t.Store_ID, ROUND(SUM(t.Quantity) / COUNT(t.Transaction_ID), 2) AS UPT\nFROM retail_panopticon.transactions t\nJOIN retail_panopticon.productInformation p ON t.Product_ID = p.Product_ID\nWHERE t.Store_ID = 'STORE01' AND  t.Date BETWEEN '2024-05-01' AND '2024-05-31'\nGROUP BY DATE(t.Date), p.Category\nORDER BY DATE(t.Date), p.Category;",
                    conn)

                pie_fig = px.pie(
                    result,
                    values='UPT',
                    names='Product_Category',
                    title='Sum of UPT by Product Category'
                )

                filtered_data = result[result['Product_Category'].isin(['Clothing', 'Toys'])]
                line_fig = px.line(
                    filtered_data,
                    x='Sale_Date',
                    y='UPT',
                    color='Product_Category',
                    title='Product Category Sales report'
                )
                line_fig.update_layout(
                    xaxis_title='Sale_Date',
                    yaxis_title='Sum of UPT',
                    legend_title='Product Category'
                )

                bar_fig = px.bar(
                    result,
                    x='UPT',
                    y='Store_ID',
                    orientation='h',  # Horizontal bar chart
                    title='Sum of UPT by Store_ID'
                )
                bar_fig.update_layout(yaxis={'categoryorder': 'total ascending'})

                figures = [pie_fig, bar_fig, line_fig]
                return figures

            elif drop == "RIVERFRONT PLAZA":
                result = execute_query(
                    "SELECT DATE(t.Date) AS Sale_Date, p.Category AS Product_Category, t.Store_ID, ROUND(SUM(t.Quantity) / COUNT(t.Transaction_ID), 2) AS UPT\nFROM retail_panopticon.transactions t\nJOIN retail_panopticon.productInformation p ON t.Product_ID = p.Product_ID\nWHERE t.Store_ID = 'STORE28' AND  t.Date BETWEEN '2024-05-01' AND '2024-05-31'\nGROUP BY DATE(t.Date), p.Category\nORDER BY DATE(t.Date), p.Category;",
                    conn)
                pie_fig = px.pie(
                    result,
                    values='UPT',
                    names='Product_Category',
                    title='Sum of UPT by Product Category'
                )

                filtered_data = result[result['Product_Category'].isin(['Clothing', 'Toys'])]
                line_fig = px.line(
                    filtered_data,
                    x='Sale_Date',
                    y='UPT',
                    color='Product_Category',
                    title='Product Category Sales report'
                )
                line_fig.update_layout(
                    xaxis_title='Sale_Date',
                    yaxis_title='Sum of UPT',
                    legend_title='Product Category'
                )

                bar_fig = px.bar(
                    result,
                    x='UPT',
                    y='Store_ID',
                    orientation='h',  # Horizontal bar chart
                    title='Sum of UPT by Store_ID'
                )
                bar_fig.update_layout(yaxis={'categoryorder': 'total ascending'})

                figures = [pie_fig, bar_fig, line_fig]
                return figures

            elif drop == "WESTFIELD WHEATON":
                result = execute_query(
                    "SELECT DATE(t.Date) AS Sale_Date, p.Category AS Product_Category, t.Store_ID, ROUND(SUM(t.Quantity) / COUNT(t.Transaction_ID), 2) AS UPT\nFROM retail_panopticon.transactions t\nJOIN retail_panopticon.productInformation p ON t.Product_ID = p.Product_ID\nWHERE t.Store_ID = 'STORE49' AND  t.Date BETWEEN '2024-05-01' AND '2024-05-31'\nGROUP BY DATE(t.Date), p.Category\nORDER BY DATE(t.Date), p.Category;",
                    conn)
                pie_fig = px.pie(
                    result,
                    values='UPT',
                    names='Product_Category',
                    title='Sum of UPT by Product Category'
                )

                filtered_data = result[result['Product_Category'].isin(['Clothing', 'Toys'])]
                line_fig = px.line(
                    filtered_data,
                    x='Sale_Date',
                    y='UPT',
                    color='Product_Category',
                    title='Product Category Sales report'
                )
                line_fig.update_layout(
                    xaxis_title='Sale_Date',
                    yaxis_title='Sum of UPT',
                    legend_title='Product Category'
                )

                bar_fig = px.bar(
                    result,
                    x='UPT',
                    y='Store_ID',
                    orientation='h',  # Horizontal bar chart
                    title='Sum of UPT by Store_ID'
                )
                bar_fig.update_layout(yaxis={'categoryorder': 'total ascending'})

                figures = [pie_fig, bar_fig, line_fig]
                return figures

        elif query == "What was the impact of the promotional discounts offered in May on the weekend vs. weekday sales for all product categories?":
            if drop == "WATER TOWER PLACE":
                result = execute_query(
                    "SELECT CASE WHEN DAYOFWEEK(S.date) IN (1, 7) THEN 'Weekend' ELSE 'Weekday' END AS day_type, P.Category,SUM(S.Total_Amount) AS total_sales, COUNT(DISTINCT S.Transaction_ID) AS total_transactions, AVG(S.Total_Amount) AS avg_transaction_value FROM transactions S JOIN productInformation P ON S.Product_ID = P.Product_ID WHERE S.Store_ID = 'STORE01' AND DATE_FORMAT(S.date, '%Y-%m') = '2024-05' GROUP BY day_type, P.Category ORDER BY day_type DESC, total_sales DESC;",
                    conn)

                total_sales_per_category = result.groupby('Category')['total_sales'].sum().reset_index()
                df = result.merge(total_sales_per_category, on='Category', suffixes=('', '_total'))
                fig2 = px.bar(
                    df,
                    y='Category',
                    x='total_sales',
                    color='day_type',
                    title='Total Sales by Day Type for Each Product Category',
                    labels={'total_sales': 'Total Sales', 'Category': 'Product Category'},
                    barmode='group',
                    orientation='h',
                    color_discrete_map={'Weekday': 'goldenrod', 'Weekend': 'dodgerblue'}
                )

                fig3 = px.bar(
                    df,
                    x='Category',
                    y='avg_transaction_value',
                    color='day_type',
                    title='Average Transaction Value by Day Type for Each Product Category',
                    labels={'avg_transaction_value': 'Average Transaction Value', 'Category': 'Product Category'},
                    barmode='stack',
                    text_auto=True,
                    color_discrete_map={'Weekday': 'orange', 'Weekend': 'purple'}
                )

                total_sales_per_category = result.groupby('Category')['total_sales'].sum().reset_index()
                df = result.merge(total_sales_per_category, on='Category', suffixes=('', '_total'))
                df['sales_percentage'] = df['total_sales'] / df['total_sales_total'] * 100
                fig = px.bar(
                    df,
                    x='Category',
                    y='sales_percentage',
                    color='day_type',
                    title='Percentage of Total Sales by Day Type for Each Product Category',
                    labels={'sales_percentage': 'Percentage of Total Sales', 'Category': 'Product Category'},
                    text_auto=True,
                    barmode='stack'
                )

                fig1 = px.bar(
                    df,
                    y='Category',
                    x='total_transactions',
                    color='day_type',
                    title='Total Transactions by Day Type for Each Product Category',
                    labels={'total_transactions': 'Total Transactions', 'Category': 'Product Category'},
                    barmode='group',
                    orientation='h',
                    color_discrete_map={'Weekday': 'mediumseagreen', 'Weekend': 'tomato'}
                )
                figures = [fig2, fig3, fig, fig1]
                return figures

            elif drop == "RIVERFRONT PLAZA":
                result = execute_query(
                    "SELECT CASE WHEN DAYOFWEEK(S.date) IN (1, 7) THEN 'Weekend' ELSE 'Weekday' END AS day_type, P.Category,SUM(S.Total_Amount) AS total_sales, COUNT(DISTINCT S.Transaction_ID) AS total_transactions, AVG(S.Total_Amount) AS avg_transaction_value FROM transactions S JOIN productInformation P ON S.Product_ID = P.Product_ID WHERE S.Store_ID = 'STORE28' AND DATE_FORMAT(S.date, '%Y-%m') = '2024-05' GROUP BY day_type, P.Category ORDER BY day_type DESC, total_sales DESC;",
                    conn)
                total_sales_per_category = result.groupby('Category')['total_sales'].sum().reset_index()
                df = result.merge(total_sales_per_category, on='Category', suffixes=('', '_total'))
                fig2 = px.bar(
                    df,
                    y='Category',
                    x='total_sales',
                    color='day_type',
                    title='Total Sales by Day Type for Each Product Category',
                    labels={'total_sales': 'Total Sales', 'Category': 'Product Category'},
                    barmode='group',
                    orientation='h',
                    color_discrete_map={'Weekday': 'goldenrod', 'Weekend': 'dodgerblue'}
                )

                fig3 = px.bar(
                    df,
                    x='Category',
                    y='avg_transaction_value',
                    color='day_type',
                    title='Average Transaction Value by Day Type for Each Product Category',
                    labels={'avg_transaction_value': 'Average Transaction Value', 'Category': 'Product Category'},
                    barmode='stack',
                    text_auto=True,
                    color_discrete_map={'Weekday': 'orange', 'Weekend': 'purple'}
                )

                total_sales_per_category = result.groupby('Category')['total_sales'].sum().reset_index()
                df = result.merge(total_sales_per_category, on='Category', suffixes=('', '_total'))
                df['sales_percentage'] = df['total_sales'] / df['total_sales_total'] * 100
                fig = px.bar(
                    df,
                    x='Category',
                    y='sales_percentage',
                    color='day_type',
                    title='Percentage of Total Sales by Day Type for Each Product Category',
                    labels={'sales_percentage': 'Percentage of Total Sales', 'Category': 'Product Category'},
                    text_auto=True,
                    barmode='stack'
                )

                fig1 = px.bar(
                    df,
                    y='Category',
                    x='total_transactions',
                    color='day_type',
                    title='Total Transactions by Day Type for Each Product Category',
                    labels={'total_transactions': 'Total Transactions', 'Category': 'Product Category'},
                    barmode='group',
                    orientation='h',
                    color_discrete_map={'Weekday': 'mediumseagreen', 'Weekend': 'tomato'}
                )
                figures = [fig2, fig3, fig, fig1]
                return figures

            elif drop == "WESTFIELD WHEATON":
                result = execute_query(
                    "SELECT CASE WHEN DAYOFWEEK(S.date) IN (1, 7) THEN 'Weekend' ELSE 'Weekday' END AS day_type, P.Category,SUM(S.Total_Amount) AS total_sales, COUNT(DISTINCT S.Transaction_ID) AS total_transactions, AVG(S.Total_Amount) AS avg_transaction_value FROM transactions S JOIN productInformation P ON S.Product_ID = P.Product_ID WHERE S.Store_ID = 'STORE49' AND DATE_FORMAT(S.date, '%Y-%m') = '2024-05' GROUP BY day_type, P.Category ORDER BY day_type DESC, total_sales DESC;",
                    conn)
                total_sales_per_category = result.groupby('Category')['total_sales'].sum().reset_index()
                df = result.merge(total_sales_per_category, on='Category', suffixes=('', '_total'))
                fig2 = px.bar(
                    df,
                    y='Category',
                    x='total_sales',
                    color='day_type',
                    title='Total Sales by Day Type for Each Product Category',
                    labels={'total_sales': 'Total Sales', 'Category': 'Product Category'},
                    barmode='group',
                    orientation='h',
                    color_discrete_map={'Weekday': 'goldenrod', 'Weekend': 'dodgerblue'}
                )

                fig3 = px.bar(
                    df,
                    x='Category',
                    y='avg_transaction_value',
                    color='day_type',
                    title='Average Transaction Value by Day Type for Each Product Category',
                    labels={'avg_transaction_value': 'Average Transaction Value', 'Category': 'Product Category'},
                    barmode='stack',
                    text_auto=True,
                    color_discrete_map={'Weekday': 'orange', 'Weekend': 'purple'}
                )

                total_sales_per_category = result.groupby('Category')['total_sales'].sum().reset_index()
                df = result.merge(total_sales_per_category, on='Category', suffixes=('', '_total'))
                df['sales_percentage'] = df['total_sales'] / df['total_sales_total'] * 100
                fig = px.bar(
                    df,
                    x='Category',
                    y='sales_percentage',
                    color='day_type',
                    title='Percentage of Total Sales by Day Type for Each Product Category',
                    labels={'sales_percentage': 'Percentage of Total Sales', 'Category': 'Product Category'},
                    text_auto=True,
                    barmode='stack'
                )

                fig1 = px.bar(
                    df,
                    y='Category',
                    x='total_transactions',
                    color='day_type',
                    title='Total Transactions by Day Type for Each Product Category',
                    labels={'total_transactions': 'Total Transactions', 'Category': 'Product Category'},
                    barmode='group',
                    orientation='h',
                    color_discrete_map={'Weekday': 'mediumseagreen', 'Weekend': 'tomato'}
                )
                figures = [fig2, fig3, fig, fig1]
                return figures

        elif query == "Give the total shipments delivered late and the reason for the delay for each product category":
            if drop == "WATER TOWER PLACE":
                result = execute_query(
                    "SELECT t.Store_ID, p.Category,s.Reason_Late_Shipment, COUNT(CASE WHEN s.Late_Shipment_Rate > 0 THEN t.Transaction_ID END) AS Total_Late_Shipments FROM transactions t JOIN productInformation p ON t.Product_ID = p.Product_ID JOIN shipmentPerformance s ON t.Transaction_ID = s.Transaction_ID WHERE t.Store_ID = 'STORE01' GROUP BY p.Category, s.Reason_Late_Shipment HAVING COUNT(CASE WHEN s.Late_Shipment_Rate > 0 THEN t.Transaction_ID END) > 0 ORDER BY Total_Late_Shipments DESC;",
                    conn)
                fig_pie = px.sunburst(
                    result,
                    path=['Category', 'Reason_Late_Shipment'],
                    values='Total_Late_Shipments',
                    title='Reasons for Late Shipments by Product Category',
                    color='Reason_Late_Shipment',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )

                total_shipments_by_category = result.groupby('Category')['Total_Late_Shipments'].sum().reset_index()
                fig_bar = px.bar(
                    total_shipments_by_category,
                    y='Category',
                    x='Total_Late_Shipments',
                    title='Total Late Shipments by Product Category',
                    labels={'Total_Late_Shipments': 'Total Late Shipments'},
                    color='Category',
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                figures = [fig_pie, fig_bar]
                return figures

            elif drop == "RIVERFRONT PLAZA":
                result = execute_query(
                    "SELECT t.Store_ID, p.Category,s.Reason_Late_Shipment, COUNT(CASE WHEN s.Late_Shipment_Rate > 0 THEN t.Transaction_ID END) AS Total_Late_Shipments FROM transactions t JOIN productInformation p ON t.Product_ID = p.Product_ID JOIN shipmentPerformance s ON t.Transaction_ID = s.Transaction_ID WHERE t.Store_ID = 'STORE28' GROUP BY p.Category, s.Reason_Late_Shipment HAVING COUNT(CASE WHEN s.Late_Shipment_Rate > 0 THEN t.Transaction_ID END) > 0 ORDER BY Total_Late_Shipments DESC;",
                    conn)
                fig_pie = px.sunburst(
                    result,
                    path=['Category', 'Reason_Late_Shipment'],
                    values='Total_Late_Shipments',
                    title='Reasons for Late Shipments by Product Category',
                    color='Reason_Late_Shipment',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )

                total_shipments_by_category = result.groupby('Category')['Total_Late_Shipments'].sum().reset_index()
                fig_bar = px.bar(
                    total_shipments_by_category,
                    y='Category',
                    x='Total_Late_Shipments',
                    title='Total Late Shipments by Product Category',
                    labels={'Total_Late_Shipments': 'Total Late Shipments'},
                    color='Category',
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                figures = [fig_pie, fig_bar]
                return figures

            elif drop == "WESTFIELD WHEATON":
                result = execute_query(
                    "SELECT t.Store_ID, p.Category,s.Reason_Late_Shipment, COUNT(CASE WHEN s.Late_Shipment_Rate > 0 THEN t.Transaction_ID END) AS Total_Late_Shipments FROM transactions t JOIN productInformation p ON t.Product_ID = p.Product_ID JOIN shipmentPerformance s ON t.Transaction_ID = s.Transaction_ID WHERE t.Store_ID = 'STORE49' GROUP BY p.Category, s.Reason_Late_Shipment HAVING COUNT(CASE WHEN s.Late_Shipment_Rate > 0 THEN t.Transaction_ID END) > 0 ORDER BY Total_Late_Shipments DESC;",
                    conn)
                fig_pie = px.sunburst(
                    result,
                    path=['Category', 'Reason_Late_Shipment'],
                    values='Total_Late_Shipments',
                    title='Reasons for Late Shipments by Product Category',
                    color='Reason_Late_Shipment',
                    color_discrete_sequence=px.colors.qualitative.Set3
                )

                total_shipments_by_category = result.groupby('Category')['Total_Late_Shipments'].sum().reset_index()
                fig_bar = px.bar(
                    total_shipments_by_category,
                    y='Category',
                    x='Total_Late_Shipments',
                    title='Total Late Shipments by Product Category',
                    labels={'Total_Late_Shipments': 'Total Late Shipments'},
                    color='Category',
                    color_discrete_sequence=px.colors.qualitative.Pastel
                )
                figures = [fig_pie, fig_bar]
                return figures


st.set_page_config(layout='wide', initial_sidebar_state='collapsed')

set_custom_css()

# with open(r'tellmore_logo.svg', 'r') as image:
#     image_data = image.read()
# st.logo(image=image_data)

col1, col2 = st.columns([4, 1])
stores = [
    "SELECT STORE",
    "WATER TOWER PLACE",
    "RIVERFRONT PLAZA",
    "WESTFIELD WHEATON"
]
st.title("SIMULATE STORE MANAGER")
st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
management_app("store", stores)
