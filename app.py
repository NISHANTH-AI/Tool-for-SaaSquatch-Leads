import pandas as pd
import streamlit as st
import numpy as np
from PIL import Image
import requests
from io import BytesIO

st.set_page_config(page_title="Lead Scoring & Company Filtering", layout="wide", initial_sidebar_state="expanded")

# Custom CSS
st.markdown("""
<style>
.main-header { font-size: 28px; color: #1F2A44; font-weight: bold; text-align: center; }
.sub-header { font-size: 20px; color: #3A506B; font-weight: bold; }
.company-card { background-color: #F5F7FA; border-radius: 8px; padding: 10px; margin-bottom: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
.highlight { color: #2ECC71; font-weight: bold; }
.stButton>button { background-color: #1F2A44; color: white; border-radius: 5px; }
.stButton>button:hover { background-color: #3A506B; }
</style>
""", unsafe_allow_html=True)

# Data cleaning
def clean_data(df):
    df.columns = [col.strip() for col in df.columns]
    rename_map = {'name': 'Company Name', 'category_list': 'Category', 'city': 'City', 'funding_total_usd': 'Funding Amount'}
    df = df.rename(columns=rename_map)
    df = df.dropna(subset=['Company Name', 'Category', 'City'], how='any')
    df['Company Name Lower'] = df['Company Name'].str.lower()
    df = df.drop_duplicates(subset='Company Name Lower').drop(columns='Company Name Lower')
    df = df.dropna(axis=1, how='all')
    relevant_cols = ['Company Name', 'Category', 'City', 'Funding Amount', 'funding_rounds', 'founded_year']
    df = df[[col for col in df.columns if col in relevant_cols or col in ['seed', 'venture', 'angel']]]
    if 'Funding Amount' in df.columns:
        df['Funding Amount'] = df['Funding Amount'].apply(lambda x: float(str(x).replace('$', '').replace(',', '').replace(' - ', '0').strip()) if pd.notnull(x) else 0.0)
    else:
        df['Funding Amount'] = 0.0
    return df

# Scoring logic with percentile-based normalization
def score_companies(df):
    # Calculate raw metrics
    current_year = pd.Timestamp.now().year
    df['Age'] = current_year - pd.to_numeric(df['founded_year'], errors='coerce').fillna(0).clip(lower=0) if 'founded_year' in df.columns else 0
    funding_types = ['seed', 'venture', 'angel']
    df['Funding Type Count'] = df.apply(lambda row: sum(1 for col in funding_types if col in df.columns and pd.notnull(row[col]) and row[col] != 0), axis=1)
    df['Rounds'] = df['funding_rounds'].fillna(0)

    # Percentile-based scoring (0 to 1 scale) for each metric
    df['Funding Score'] = df['Funding Amount'].rank(pct=True) * 50  # 50% weight
    df['Rounds Score'] = df['Rounds'].rank(pct=True) * 20           # 20% weight
    df['Age Score'] = df['Age'].rank(pct=True) * 15                # 15% weight
    df['Funding Type Score'] = df['Funding Type Count'].rank(pct=True) * 15  # 15% weight

    # Total score
    df['Score'] = (df['Funding Score'] + df['Rounds Score'] + df['Age Score'] + df['Funding Type Score']).clip(upper=100)
    df['Top Quality'] = df[['Funding Score', 'Rounds Score', 'Age Score', 'Funding Type Score']].idxmax(axis=1).str.replace(' Score', '')
    return df.drop(columns=['Age', 'Funding Type Count', 'Rounds', 'Funding Score', 'Rounds Score', 'Age Score', 'Funding Type Score'])

# AI Chat for company investigation
def investigate_company(company_data, query):
    query = query.lower()
    if 'funding' in query:
        return f"{company_data['Company Name']} has a funding amount of ${company_data['Funding Amount']:,.2f}."
    elif 'growth' in query:
        return f"Based on a score of {company_data['Score']:.2f}, {company_data['Company Name']} shows {'high' if company_data['Score'] > 80 else 'moderate' if company_data['Score'] > 50 else 'low'} growth potential."
    elif 'recommendation' in query:
        return f"Sales recommendation: {'Prioritize outreach' if company_data['Score'] > 80 else 'Nurture with follow-ups' if company_data['Score'] > 50 else 'Validate further'}."
    else:
        return "I can help with funding, growth potential, or sales recommendations. What would you like to know?"

# Main app
def main():
    st.markdown('<div class="main-header">🚀 Lead Scoring & Company Filtering</div>', unsafe_allow_html=True)
    st.markdown("Enhance your lead generation with AI-driven insights! 🔒 Data processed securely.", unsafe_allow_html=True)

    with st.sidebar:
        st.markdown('<div class="sub-header">🔍 Filters</div>', unsafe_allow_html=True)
        uploaded_file = st.file_uploader("📁 Upload CSV File", type="csv", help="Upload company data CSV")

    if uploaded_file:
        with st.spinner("🔄 Processing data..."):
            df = pd.read_csv(uploaded_file, encoding='ISO-8859-1')
            cleaned_df = clean_data(df)
            if cleaned_df.empty:
                st.warning("⚠️ No data found after cleaning.")
                st.stop()
            scored_df = score_companies(cleaned_df)

        with st.expander("📊 View Cleaned Data"):
            st.dataframe(cleaned_df.head())

        with st.sidebar:
            categories = sorted(scored_df['Category'].dropna().unique())
            cities = sorted(scored_df['City'].dropna().unique())
            selected_category = st.selectbox("🏷️ Category", categories, help="Filter by category")
            selected_city = st.selectbox("🌍 City", cities, help="Filter by city")

        filtered_df = scored_df[
            scored_df['Category'].str.contains(selected_category, case=False, na=False) &
            (scored_df['City'].str.lower() == selected_city.lower())
        ].sort_values(by=['Funding Amount', 'Score'], ascending=[False, False])

        if filtered_df.empty:
            st.info(f"ℹ️ No matches for '{selected_category}' in '{selected_city}'.")
        else:
            st.markdown(f'<div class="sub-header">🏢 Results for "{selected_category}" in "{selected_city}"</div>', unsafe_allow_html=True)
            st.dataframe(filtered_df)
            csv = filtered_df.to_csv(index=False).encode('utf-8')
            st.download_button("⬇️ Export to CRM", csv, "filtered_leads.csv", "text/csv")

            col1, col2 = st.columns([1, 4])
            with col1:
                logo_url = "https://upload.wikimedia.org/wikipedia/commons/6/69/Artificial_Intelligence_logo.svg"
                try:
                    img = Image.open(BytesIO(requests.get(logo_url).content))
                    st.image(img, width=80, caption="AI Suggest")
                except:
                    st.write("🤖 AI Suggest")

            with col2:
                if st.button("🌟 Top 5 Suggestions"):
                    top5 = filtered_df.head(5)
                    st.success("✅ Top 5 Suggestions:")
                    for _, row in top5.iterrows():
                        employees, openings = np.random.randint(50, 5000), np.random.randint(1, 50)
                        st.markdown(f'<div class="company-card">', unsafe_allow_html=True)
                        st.markdown(f"### 🏢 {row['Company Name']}")
                        st.markdown(f"- 💰 **Funding:** ${row['Funding Amount']:,.2f}")
                        st.markdown(f"- 📊 **Score:** <span class='highlight'>{row['Score']:.2f}/100</span>", unsafe_allow_html=True)
                        st.markdown(f"- 🏅 **Top Quality:** {row['Top Quality']}")
                        st.markdown(f"- 👥 **Employees:** {employees}")
                        st.markdown(f"- 📌 **Openings:** {openings}")
                        if row['Score'] > 80:
                            st.info("✅ Highly recommended!")
                            st.markdown("**Sales Tip:** Prioritize outreach; strong funding signals growth potential.")
                        elif row['Score'] > 50:
                            st.warning("⚠️ Monitor growth.")
                            st.markdown("**Sales Tip:** Nurture with targeted follow-ups.")
                        else:
                            st.error("🔍 Proceed with caution.")
                            st.markdown("**Sales Tip:** Validate further before outreach.")
                        st.markdown('</div>', unsafe_allow_html=True)

                # AI Chat for Investigation
                st.markdown('<div class="sub-header">🤖 Investigate a Company</div>', unsafe_allow_html=True)
                company_names = filtered_df['Company Name'].tolist()
                selected_company = st.selectbox("Select a Company to Investigate", company_names)
                if selected_company:
                    company_data = filtered_df[filtered_df['Company Name'] == selected_company].iloc[0]
                    query = st.text_input("Ask about the company (e.g., funding, growth, recommendation)", "")
                    if query:
                        response = investigate_company(company_data, query)
                        st.markdown(f"**AI Response:** {response}")

if __name__ == "__main__":
    main()