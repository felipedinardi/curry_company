import pandas as pd
import numpy as np
from haversine import haversine
import plotly.express as px
import streamlit as st
from datetime import datetime
from PIL import Image
import folium
from streamlit_folium import st_folium

st.set_page_config( page_title = 'Visão Empresa', layout='wide')

df = pd.read_csv('train.csv')
#-------------------------------------------------------------------------------------------------
# Funções
#-------------------------------------------------------------------------------------------------
def clean_code( df ):

    '''Essa função tem como objetivo realizar a limpeza dos dados'''
    
    cols = ['Delivery_person_Age', 'Delivery_person_Ratings', 'multiple_deliveries']
    
    df[cols] = df[cols].apply(pd.to_numeric, errors='coerce')
    
    df['Delivery_person_Age'] = df['Delivery_person_Age'].astype('Int64')
    df['multiple_deliveries'] = df['multiple_deliveries'].astype('Int64')
    
    df['Order_Date'] = pd.to_datetime(df['Order_Date'])
    
    df['Time_Orderd'] = df['Time_Orderd'].apply(pd.to_timedelta, errors='coerce')
    
    df['Time_Order_picked'] = df['Time_Order_picked'].apply(pd.to_timedelta, errors='coerce')
    
    obj_cols = df.select_dtypes(include='object').columns
    df[obj_cols] = df[obj_cols].apply(lambda x: x.str.strip())
    df['Time_taken(min)'] = df['Time_taken(min)'].str[6:].str.strip()
    df['Time_taken(min)'] = df['Time_taken(min)'].astype(int)
    
    df['Delivery_person_Age'] = (
        df.groupby('City')['Delivery_person_Age']
          .transform(lambda x: x.fillna(x.median()))
    )
    
    df['Delivery_person_Ratings'] = (
        df.groupby('City')['Delivery_person_Ratings']
          .transform(lambda x: x.fillna(x.median()))
    )
    
    df = df.dropna(subset=['Time_Orderd', 'multiple_deliveries'])
    
    df['City'] = df['City'].replace('NaN', np.nan)
    
    
    df['City'] = df.groupby(
        ['Delivery_location_latitude', 'Delivery_location_longitude']
    )['City'].transform(
        lambda x: x.fillna(x.mode()[0] if not x.mode().empty else np.nan)
    )
    
    df['Festival'] = df['Festival'].replace('NaN',np.nan)
    df['Festival'] = df.groupby('Order_Date')['Festival'].transform(lambda x: x.fillna(x.mode()[0]))
    
    df['Time_Orderd'] = df['Time_Orderd'].astype(str).str.replace('0 days', '')
    df['Time_Order_picked'] = df['Time_Order_picked'].astype(str).str.replace('0 days', '')
    
    df['City'] = df['City'].str.replace('Metropolitian', 'Metropolitan')

    return df

def order_metric(df):
    st.markdown('# Orders by Day')
    orders_day = df.groupby('Order_Date')['ID'].count().reset_index()
    fig = px.bar(orders_day, x='Order_Date', y='ID')

    return fig

            
def traffic_order_share(df):
    orders_traffic = df.groupby('Road_traffic_density')['ID'].count().reset_index()
    fig = px.pie(orders_traffic, values='ID', names='Road_traffic_density')
                
    return fig

            
def traffic_order_city(df):
    order_citytraffic = df.groupby(['City', 'Road_traffic_density'])['ID'].count().reset_index()
    fig = px.scatter(order_citytraffic, x='City', y='Road_traffic_density', size='ID', color='City')
            
    return fig

def order_by_week(df):
    df['Week'] = df['Order_Date'].dt.strftime('%U')
    orders_week = df.groupby('Week')['ID'].count().reset_index()
    fig = px.line(orders_week, x='Week', y='ID')
            
    return fig

def order_share_week(df):
    df1 = df.groupby('Week')['ID'].count().reset_index()
    df2 = df.groupby('Week')['Delivery_person_ID'].nunique().reset_index()
    merge = pd.merge(df1,df2,how='inner')
    merge['Order_by_deliver'] = merge['ID'] / merge['Delivery_person_ID']
    fig = px.line(merge, x = 'Week', y='Order_by_deliver')

    return fig

def create_delivery_map(df):
    map_data = (
    df.loc[:, [
    'City',
    'Road_traffic_density',
    'Delivery_location_latitude',
    'Delivery_location_longitude'
    ]]
    .groupby(['City', 'Road_traffic_density'])
    .median()
    .reset_index()
    )
       
    m = folium.Map(
    location=[
    map_data['Delivery_location_latitude'].mean(),
    map_data['Delivery_location_longitude'].mean()
    ],
    zoom_start=10
    )
        
    for _, row in map_data.iterrows():
        folium.CircleMarker(
        location=[
        row['Delivery_location_latitude'],
        row['Delivery_location_longitude']
        ],
        radius=7,
        fill=True,
        fill_opacity=0.8,
        popup=f"{row['City']} - {row['Road_traffic_density']}"
        ).add_to(m)
        
    return m


#-------------------------------------------------------------------------------------------------------
# Limpando os dados
#-------------------------------------------------------------------------------------------------------

df = clean_code(df)

#-------------------------------------------------------------------------------------------------------    
# Visão empresa

orders_day = df.groupby('Order_Date')['ID'].count().reset_index()
px.bar(orders_day, x='Order_Date', y='ID', title='Bar Chart Orders by day')

#--------------------------------------------------------------------------------------------------------
#Barra Lateral

st.header('Marketplace - Visão Cliente')

#image_path = 'logo.jpg'
image = Image.open( 'logo.jpg' )
st.sidebar.image(image,width=120)

st.sidebar.markdown('# Cury Company')
st.sidebar.markdown('## Fastest Delivery in Town')
st.sidebar.markdown('''---''')

st.sidebar.markdown('## Selecione uma data limite')
data_slider = st.sidebar.slider('Até qual valor', value=datetime(2022, 4, 13), min_value=datetime(2022, 2, 11),
                 max_value=datetime(2022, 4, 6), format='DD-MM-YYYY')


st.sidebar.markdown('''---''')
traffic_options = st.sidebar.multiselect('Quais as condições do trânsito',['Low','Medium','High','Jam'], default=['Low','Medium','High','Jam'])
st.sidebar.markdown('''---''')

#Filtro de data
linhas_selecionadas = df['Order_Date'] < data_slider
df = df.loc[linhas_selecionadas, :]


#Filtro de Trânsito
linhas_selecionadas = df['Road_traffic_density'].isin( traffic_options )
df = df.loc[linhas_selecionadas, :]

#--------------------------------------------------------------------------------------------------------
# Layout Streamlit

tab1, tab2, tab3 = st.tabs(['Visão Gerencial', 'Visão Tática', 'Visão Gegráfica'])

with tab1:
    with st.container():
        fig = order_metric( df )
        st.plotly_chart(fig, use_container_width=True)

        

    with st.container():
        col1, col2 = st.columns(2)
        
        with col1:
            fig = traffic_order_share(df)
            st.header('Traffic Order Share')
            st.plotly_chart(fig, use_container_width=True)

                
        with col2:
            fig = traffic_order_city(df)
            st.header('Traffic Order City')
            st.plotly_chart(fig, use_container_width=True)

        
with tab2:
    with st.container():
        
        fig = order_by_week(df)
        st.markdown('# Orders by Week')
        st.plotly_chart(fig, use_container_width=True)    
        

    with st.container():

        fig = order_share_week(df)
        st.markdown('# Order Share by Week')
        st.plotly_chart(fig, use_container_width=True)

        
with tab3:
    with st.container():
        st.markdown('# Map')
    
        m = create_delivery_map(df)
        st_folium(m, width=700, height=500)
    