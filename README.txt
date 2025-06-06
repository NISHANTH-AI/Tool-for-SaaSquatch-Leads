# Lead Scoring & Company Filtering Tool for SaaSquatch Leads

## Overview
This tool enhances SaaSquatch Leads by enabling user-driven filtering (by category and city) and scoring companies based on funding (50%), rounds (20%), age (15%), and funding diversity (15%) using percentile-based normalization. Built with Streamlit, it offers an intuitive UI, AI-driven suggestions, an AI chat for company investigation, and CSV export for CRM integration, streamlining lead generation for sales teams.

## Setup Instructions
1. **Set Up a Virtual Environment** (Optional but Recommended):
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```
2. **Install Dependencies**:
   ```
   pip install -r requirements.txt
   ```
3. **Run the App**:
   ```
   streamlit run app.py
   ```
   Open `http://localhost:8501` in your browser.
4. **Upload a Dataset**:
   - Use the provided `sample_leads_input.csv` or your own CSV file with columns like `name`, `category_list`, `city`, `funding_total_usd`, `funding_rounds`, `founded_year`, `seed`, `venture`, `angel`.

## File Structure
- `app.py`: Main application code.
- `requirements.txt`: Dependencies.
- `sample_leads_input.csv`: Sample dataset for testing.
- `README.md`: Project overview and setup instructions.
- `demo_walkthrough.ipynb`: Optional Jupyter Notebook demo.

## Dataset Format
The `sample_leads_input.csv` includes columns: `name`, `category_list`, `city`, `funding_total_usd`, `funding_rounds`, `founded_year`, `seed`, `venture`, `angel`. Ensure your dataset matches this format for full functionality.

## Notes
- The app processes data securely and does not store user uploads.
- For issues, contact [your email].