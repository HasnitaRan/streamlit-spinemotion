from pymongo import MongoClient
import streamlit as st
import pandas as pd
from collections import Counter
import matplotlib.pyplot as plt
import numpy as np
import plotly.express as px
import seaborn as sns

# Set page config
st.set_page_config(page_title="Visualisasi SpineMotion", page_icon="🍒", layout="wide")

# Fungsi untuk menghubungkan ke MongoDB dan mendapatkan data
def get_data_from_mongodb():
    client = MongoClient("mongodb://localhost:27017/")
    db = client["visualisasi-mongodb"]
    collection = db["bigdata"]
    data = list(collection.find())
    return pd.DataFrame(data)

# Fungsi untuk menambahkan kolom hari dan jam serta workingday_label
def add_day_hour_columns(data):
    data['tanggal'] = pd.to_datetime(data['tanggal'])
    # Mengubah nama hari ke bahasa Indonesia
    data['day_of_week'] = data['tanggal'].dt.day_name().map({
        'Monday': 'Sen', 'Tuesday': 'Sel', 'Wednesday': 'Rab',
        'Thursday': 'Kam', 'Friday': 'Jum', 'Saturday': 'Sab', 'Sunday': 'Ming'
    })
    data['hour'] = data['tanggal'].dt.hour
    data['workingday_label'] = data['day_of_week'].apply(lambda x: 'Weekday' if x in ['Sen', 'Sel', 'Rab', 'Kam', 'Jum'] else 'Weekend')
    return data




# Fungsi untuk visualisasi aktivitas berdasarkan hari
def plot_activity_by_day(data):
    day_order = ['Sen', 'Sel', 'Rab', 'Kam', 'Jum', 'Sab', 'Ming']
    activity_by_day = data['day_of_week'].value_counts().reindex(day_order).fillna(0)

    # Visualisasi dengan line chart
    fig, ax = plt.subplots()
    ax.plot(activity_by_day.index, activity_by_day.values, marker='o', linestyle='-', color='green')
    ax.set_xlabel('Hari dalam Seminggu')
    ax.set_ylabel('Jumlah Aktivitas')
    ax.set_title('Aktivitas Pengguna Berdasarkan Hari dalam Seminggu')
    return fig, ax

# Fungsi untuk visualisasi aktivitas berdasarkan jam
def plot_activity_by_hour(data):
    activity_by_hour = data.groupby('hour').size()

    # Visualisasi dengan line chart
    fig, ax = plt.subplots()
    ax.plot(activity_by_hour.index, activity_by_hour.values, marker='o', linestyle='-')
    ax.set_xlabel('Jam (24 Jam)')
    ax.set_ylabel('Jumlah Aktivitas')
    ax.set_title('Aktivitas Pengguna Berdasarkan Jam')
    return fig, ax

# Fungsi untuk menampilkan grafik aktivitas terpopuler
def show_most_common_activities(data):
    activity_counts = dict(Counter(data['namaGerakan']))
    sorted_activities = sorted(activity_counts.items(), key=lambda x: x[1], reverse=True)
    df_sorted = pd.DataFrame(sorted_activities, columns=['namaGerakan', 'Count'])
    colors = plt.cm.cividis(np.linspace(0, 1, len(df_sorted)))  
    fig, ax = plt.subplots(figsize=(10, 6))  
    bars = ax.barh(df_sorted['namaGerakan'], df_sorted['Count'], color=colors)  
    ax.set_xlabel('Jumlah Aktivitas')  
    ax.set_ylabel('Nama Gerakan')  
    ax.set_title('Gerakan Paling Banyak Dilakukan oleh Pengguna')

    # Menambahkan label nilai di atas setiap batang
    for bar, count in zip(bars, df_sorted['Count']):
        ax.text(bar.get_width() + 0.2, bar.get_y() + bar.get_height() / 2, f'{count}', ha='center', va='bottom')

    st.pyplot(fig)  # Menampilkan grafik di Streamlit

# Fungsi untuk menampilkan grafik aktivitas terpopuler berdasarkan gender
def show_most_common_activities_by_gender(data):
    # Filter data berdasarkan jenis kelamin (laki-laki dan perempuan)
    male_data = data[data['gender'] == 'Laki-laki']
    female_data = data[data['gender'] == 'Perempuan']

    # Menghitung jumlah aktivitas untuk laki-laki
    male_activity_counts = dict(Counter(male_data['namaGerakan']))
    sorted_male_activities = sorted(male_activity_counts.items(), key=lambda x: x[1], reverse=True)

    # Menghitung jumlah aktivitas untuk perempuan
    female_activity_counts = dict(Counter(female_data['namaGerakan']))
    sorted_female_activities = sorted(female_activity_counts.items(), key=lambda x: x[1], reverse=True)

    # Data untuk pie chart laki-laki
    labels_male = [activity for activity, count in sorted_male_activities]
    sizes_male = [count for activity, count in sorted_male_activities]

    # Data untuk pie chart perempuan
    labels_female = [activity for activity, count in sorted_female_activities]
    sizes_female = [count for activity, count in sorted_female_activities]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 6))

    # Pie chart untuk laki-laki
    ax1.pie(sizes_male, labels=labels_male, autopct='%1.1f%%', startangle=90)
    ax1.axis('equal')
    ax1.set_title('Aktivitas Laki-laki')

    # Pie chart untuk perempuan
    ax2.pie(sizes_female, labels=labels_female, autopct='%1.1f%%', startangle=90)
    ax2.axis('equal')
    ax2.set_title('Aktivitas Perempuan')

    # Menampilkan subplot di Streamlit
    st.pyplot(fig)

# Fungsi untuk membuat DataFrame bulanan pengguna
def create_monthly_users_df(data):
    data['tanggal'] = pd.to_datetime(data['tanggal'])
    users_per_day = data.groupby('tanggal')['_id'].nunique()
    
    total_users = users_per_day.sum()
    
    data['gender'] = data['gender'].map({'Laki-laki': 1, 'Perempuan': 0}).fillna(1)
    total_male = (data['gender'] == 1).sum()
    total_female = (data['gender'] == 0).sum()
    
    monthly_users_df = data.resample(rule='M', on='tanggal').agg({
        '_id': 'nunique',
        'gender': 'sum'
    }).rename(columns={'_id': 'total_users', 'gender': 'total_male'})
    
    monthly_users_df['total_female'] = monthly_users_df['total_users'] - monthly_users_df['total_male']
    monthly_users_df.index = monthly_users_df.index.strftime('%b-%y')
    monthly_users_df = monthly_users_df.reset_index()
    
    return monthly_users_df, total_users, total_male, total_female

# Fungsi untuk membuat dataframe pengguna berdasarkan workingday
def create_workingday_users_df(data):
    # Convert tanggal column to datetime if it's not already
    data['tanggal'] = pd.to_datetime(data['tanggal'])
    
    # Function to determine workingday_label based on weekday
    def is_working_day(date):
        if date.weekday() < 5:  # Monday (0) to Friday (4) are weekdays
            return 'Working Day'
        else:
            return 'Weekend'
    
    # Apply the function to create workingday_label column
    data['workingday_label'] = data['tanggal'].apply(is_working_day)
    
    # Calculate activity counts based on workingday_label
    activity_counts = data.groupby('workingday_label').size().reset_index(name='total_activity')
    
    return activity_counts


# Sidebar untuk navigasi
st.sidebar.title("Dashboard Admin")
st.sidebar.image("https://res.cloudinary.com/dpm5irq1n/image/upload/v1719450750/article/Screenshot_2024-06-27_081003_qio7mx.png")
page = st.sidebar.selectbox("Pilih Halaman", ["Informasi User", "Gerakan Terpopuler", "Waktu Terpopuler"])

# Tampilkan halaman yang dipilih
if page == "Gerakan Terpopuler":
    data = get_data_from_mongodb()
    show_most_common_activities(data)
    show_most_common_activities_by_gender(data)
elif page == "Waktu Terpopuler":
    data = get_data_from_mongodb()
    data = add_day_hour_columns(data)
    # Memisahkan layout menjadi dua kolom
    col1, col2 = st.columns(2)

    # Menampilkan plot aktivitas berdasarkan hari di kolom pertama
    with col1:
        fig_day, ax_day = plot_activity_by_day(data)
        st.pyplot(fig_day)

    # Menampilkan plot aktivitas berdasarkan jam di kolom kedua
    with col2:
        fig_hour, ax_hour = plot_activity_by_hour(data)
        st.pyplot(fig_hour)
        
    
    st.subheader("Aktivitas Berdasarkan WorkingDay dan Weekend")
    activity_user_result = create_workingday_users_df(data)   
    #Menampilkan hasil dengan seaborn dan matplotlib
    fig, ax = plt.subplots()
    ax = sns.barplot(x='workingday_label', y='total_activity', data=activity_user_result, palette='plasma')
    ax.set_title('Aktivitas User di Hari Kerja dan Weekend')
    ax.set_xlabel('Hari Kerja / Weekend')
    ax.set_ylabel('Jumlah Aktivitas User')
    st.pyplot(fig)
        
elif page == "Informasi User":
    data = get_data_from_mongodb()
    monthly_users_df, total_users, total_male, total_female = create_monthly_users_df(data)
    
    st.markdown("## Informasi User")
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Users", value=total_users, delta=f"{total_users} total users", delta_color="off")
        st.markdown("<h5 style='color: green;'>👥 Total Users</h5>", unsafe_allow_html=True)
    
    with col2:
        st.metric("Total Male Users", value=total_male, delta=f"{total_male} male users", delta_color="off")
        st.markdown("<h5 style='color: blue;'>👨 Total Male Users</h5>", unsafe_allow_html=True)
    
    with col3:
        st.metric("Total Female Users", value=total_female, delta=f"{total_female} female users", delta_color="off")
        st.markdown("<h5 style='color: pink;'>👩 Total Female Users</h5>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    fig = px.line(monthly_users_df,
                  x='tanggal',
                  y=['total_users', 'total_male', 'total_female'],
                  color_discrete_sequence=["red", "blue", "orange"],
                  markers=True,
                  title="Monthly Count of Users").update_layout(xaxis_title='Month-Year', yaxis_title='Total Users')

    st.plotly_chart(fig, use_container_width=True)
        
    

            
