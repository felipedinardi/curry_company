import plotly.graph_objects as go
import pandas as pd
import numpy as np
from haversine import haversine
import plotly.express as px
import streamlit as st
from datetime import datetime
from PIL import Image
import folium
from streamlit_folium import st_folium

st.set_page_config( page_title = 'Visão Restaurantes', layout='wide')

df = pd.read_csv('../train.csv')

#-------------------------------------------------------------------------------------------------
# Funções
#-------------------------------------------------------------------------------------------------
def clean_code( df ):

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
    
    location_cols = ['Restaurant_latitude', 'Restaurant_longitude', 'Delivery_location_latitude', 'Delivery_location_longitude']
    df['Location'] = df[location_cols].apply(
        lambda x: haversine(
            (x.Restaurant_latitude, x.Restaurant_longitude),
            (x.Delivery_location_latitude, x.Delivery_location_longitude)
        ),
        axis=1
    )
    
    df['Festival'] = df['Festival'].replace('NaN',np.nan)
    df['Festival'] = df.groupby('Order_Date')['Festival'].transform(lambda x: x.fillna(x.mode()[0]))
    
    df['Time_Orderd'] = df['Time_Orderd'].astype(str).str.replace('0 days', '')
    df['Time_Order_picked'] = df['Time_Order_picked'].astype(str).str.replace('0 days', '')
    
    df['City'] = df['City'].str.replace('Metropolitian', 'Metropolitan')
    
    # Visão empresa
    
    orders_day = df.groupby('Order_Date')['ID'].count().reset_index()
    px.bar(orders_day, x='Order_Date', y='ID', title='Bar Chart Orders by day')
    
    return df

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

st.header('Marketplace - Visão Restaurantes')

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

        col1, col2, col3, col4, col5, col6 = st.columns(6)

        with col1:
            unique = df['Delivery_person_ID'].nunique()
            unique = int(unique)
            col1.metric('Entregadores únicos', unique)
            
        with col2:
            average_distance = np.round(df['Location'].mean(),1)
            col2.metric('Distância média das entregas', f"{average_distance:.2f} km")
            
        with col3:
            festival = df[df['Festival'] == 'Yes']
            festival_mean = festival['Time_taken(min)'].mean()
            col3.metric('Tempo médio entrega festival', festival_mean)
            
        with col4:
            festival = df[df['Festival'] == 'Yes']     
            festival_std = festival['Time_taken(min)'].std()
            col4.metric('Desvio padrão entrega festival', festival_std)
            
        with col5:    
            festival_no = df[df['Festival'] == 'No']
            festival_no_mean = festival_no['Time_taken(min)'].mean()
            col5.metric('Tempo médio entrega sem festival', festival_no_mean)
            
        with col6:
            festival_no = df[df['Festival'] == 'No'] 
            festival_no_std = festival_no['Time_taken(min)'].std()
            col6.metric('Desvio padrão entrega sem festival', festival_no_std)
    

    with st.container():
        st.markdown('''---''')
        
        col1, col2 = st.columns(2)

        with col1:
            st.markdown('#### Tempo médio de entrega por cidade' )
            delivery_std = df.groupby('City')['Time_taken(min)'].agg(['mean','std']).reset_index()
    
            fig = go.Figure()
            fig.add_trace(go.Bar(name='Control',x=delivery_std['City'], y=delivery_std['mean'], \
            error_y=dict(type='data', array=delivery_std['std'])))
            fig.update_layout(barmode='group')
            st.plotly_chart(fig)

        with col2:
            st.markdown('#### Distribuição da Distância' )
            df_vr = df.groupby(['City','Type_of_order'])['Time_taken(min)'].agg(['mean','std'])
            st.dataframe(df_vr)
        
        
    
    with st.container():
        st.markdown('''---''')
        st.title(' Distribuição do Tempo' )

        col1, col2 = st.columns(2)

        with col1:
            average_distance = (df.groupby('City')['Location'].mean().reset_index())
            fig = go.Figure (data=[go.Pie(labels=average_distance['City'], \
            values=average_distance['Location'], pull=[0,0.1,0])])
            st.plotly_chart(fig)
            
        with col2:
            
            traffic_meanstd = df.groupby(['City','Road_traffic_density'])['Time_taken(min)']. \
            agg(['mean','std']).reset_index()

            fig = px.sunburst(traffic_meanstd, path=['City', 'Road_traffic_density'], values='mean', \
            color='std',    color_continuous_scale='RdBu_r', color_continuous_midpoint=np.average(traffic_meanstd['std']))
            st.plotly_chart(fig)
            
        