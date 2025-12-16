import pandas as pd
import numpy as np
from haversine import haversine
import plotly.express as px
import streamlit as st
from datetime import datetime
from PIL import Image
import folium
from streamlit_folium import st_folium

st.set_page_config( page_title = 'Visão Entregadores', layout='wide')

df = pd.read_csv('dataset/train.csv')

#-----------------------------------------------------------------------------------------------------------------
# Funções
#-----------------------------------------------------------------------------------------------------------------

def clean_code(df):
        
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




#-------------------------------------------------------------------------------------------------------
# Limpando os dados
#-------------------------------------------------------------------------------------------------------

df = clean_code(df)

#-----------------------------------------------------------------------------------------------------------------
# Visão empresa

orders_day = df.groupby('Order_Date')['ID'].count().reset_index()
px.bar(orders_day, x='Order_Date', y='ID', title='Bar Chart Orders by day')

#--------------------------------------------------------------------------------------------------------
#Barra Lateral

st.header('Marketplace - Visão Entregadores')

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

st.sidebar.markdown('''---''')
weather_options = st.sidebar.multiselect('Quais as condições do clima',['conditions Sunny', 'conditions Stormy', 'conditions Sandstorms','conditions Cloudy', 'conditions Fog', 'conditions Windy'], default=['conditions Sunny', 'conditions Stormy', 'conditions Sandstorms','conditions Cloudy', 'conditions Fog', 'conditions Windy'])
st.sidebar.markdown('''---''')

#Filtro de data
linhas_selecionadas = df['Order_Date'] < data_slider
df = df.loc[linhas_selecionadas, :]


#Filtro de Trânsito
linhas_selecionadas = df['Road_traffic_density'].isin( traffic_options )
df = df.loc[linhas_selecionadas, :]

#Filtro de Clima
linhas_selecionadas = df['Weatherconditions'].isin( weather_options )
df = df.loc[linhas_selecionadas, :]

#--------------------------------------------------------------------------------------------------------
# Layout Streamlit

tab1, tab2, tab3 = st.tabs(['Visão Gerencial', '__', '__'])

with tab1:
    with st.container():
        st.title(' Overall Metrics' )
        
        col1, col2, col3, col4 = st.columns(4, gap='large')

        
        with col1:
            maior_idade = df['Delivery_person_Age'].max()
            col1.metric('Maior de idade', maior_idade)
            
        with col2:
            menor_idade = df['Delivery_person_Age'].min()
            col2.metric('Menor de idade', menor_idade)
            
        with col3:
            melhor_veiculo = df['Vehicle_condition'].max()
            col3.metric('Melhor condição de veículo', melhor_veiculo)
            
        with col4:
            pior_veiculo = df['Vehicle_condition'].min()
            col4.metric('Pior condição de veículo', pior_veiculo)

    with st.container():
        st.markdown( '''---''')
        st.title('Avaliações')

        col1, col2 = st.columns(2)
        with col1:
            st.markdown('##### Avaliações médias por entregador')
            average_rating = df.groupby('Delivery_person_ID')['Delivery_person_Ratings'].mean().reset_index()
            st.dataframe(average_rating)

        with col2:
            st.markdown('##### Avaliação média por trânsito')
            average_traffic = df.groupby('Road_traffic_density')['Delivery_person_Ratings'].agg(['mean','std'])
            st.dataframe(average_traffic)
            
            st.markdown('##### Avaliação média por clima')
            average_weather = df.groupby('Weatherconditions')['Delivery_person_Ratings'].agg(['mean','std'])
            st.dataframe(average_weather)

    with st.container():
        st.markdown('''---''')
        st.title('Velocidade de Entrega')

        col1, col2 = st.columns(2)

        with col1:
            st.markdown('##### Top Entregadores mais rápidos')
            top_10 = df.groupby(['City', 'Delivery_person_ID'])['Time_taken(min)'].mean().reset_index().\
            sort_values(by=['City', 'Time_taken(min)'], ascending=[True, True]).groupby('City').head(10)
            st.dataframe(top_10)


        with col2:
            st.markdown('##### Top Entregadores mais lentos')
            bottom_10 = df.groupby(['City', 'Delivery_person_ID'])['Time_taken(min)'].mean().reset_index().\
            sort_values(by=['City', 'Time_taken(min)'], ascending=[True, True]).groupby('City').tail(10)
            st.dataframe(bottom_10)


              
