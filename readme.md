# ⚡ Electric Vehicle Analytics & Prediction System

A comprehensive machine learning-powered web application for analyzing electric vehicle market trends and predicting EV specifications using real-world data.

## 🎯 Features

### 📈 Market Insights
- Interactive visualizations of EV market trends
- Comparative analysis of battery capacity, range, and pricing
- Statistical breakdowns by manufacturer and vehicle type

### 🧪 Model Training Lab
- Train custom ML models (Random Forest, Gradient Boosting)
- Predict EV range and price based on specifications
- Real-time performance metrics (R², RMSE, MAE)
- Automated data preprocessing with proper train/test splitting

### 🔮 Real-Time Prediction
- Predict range and price for any EV configuration
- Select from existing vehicles or input custom specifications
- Instant accuracy metrics comparing predictions to actual values
- Support for high-performance EVs (1-25s acceleration, 10-250 kWh batteries)
- Physics vs. AI: compares the ML prediction against theoretical physics calculations ($Range = \frac{Battery}{Efficiency}$) to highlight model intelligence.

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- pip package manager

### Installation

1. Clone the repository:
```bash
git clone https://github.com/sheikhrehanseo/ev-analytics-v2/
cd "Data Project v2"
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
streamlit run streamlit_app.py
```

4. Open your browser to `http://localhost:8501`

## 📊 Data Sources

The system uses two integrated datasets:
- `prices_data.csv` - EV pricing and specifications
- `raw_data.csv` - Raw market data

## 🛠️ Technology Stack

- **Frontend**: Streamlit
- **Data Processing**: Pandas, NumPy
- **Machine Learning**: scikit-learn (Random Forest, Gradient Boosting)
- **Visualization**: Plotly Express, Plotly Graph Object, Seaborn, Matplotlib

## 📁 Project Structure

```
Data Project v2/
├── streamlit_app.py              # Main application entry point
├── pages/
│   ├── 1_📈_Market_Insights.py   # Market analysis dashboard
│   ├── 2_🧪_Model_Training.py    # ML model training interface
│   └── 3_🔮_Real_Time_Prediction.py  # Prediction interface
├── prices_data.zip               # EV pricing dataset
├── raw_data.zip                  # Raw market data
└── requirements.txt              # Python dependencies
└── readme.md                     # file you are reading :)
```

## 🔧 Model Training

1. Navigate to **Model Training Lab**
2. Select prediction target (Range, Price, or Both)
3. Choose algorithm (Random Forest or Gradient Boosting)
4. Configure test size and random state
5. Click **Train Model**
6. Models are automatically saved for prediction use

## 🎯 Making Predictions

1. Navigate to **Real-Time Prediction**
2. Choose an existing vehicle or select "Custom Input"
3. Enter/adjust specifications:
   - Battery Capacity (10-250 kWh)
   - Efficiency (100-400 Wh/km)
   - Top Speed (80-350 km/h)
   - Acceleration 0-100 km/h (1-25 seconds)
   - Fast Charge Power (0-400 kW)
4. Click **Predict Range & Price**
5. View predictions with accuracy metrics

## 🔒 Data Quality Features

- Automatic NaN handling using training-set medians
- Data leakage prevention in train/test splits
- Input validation and constraint enforcement
- Robust error handling for missing data

## 📈 Model Performance

Models achieve strong predictive performance:
- Range Prediction: R² > 0.90
- Price Prediction: R² > 0.85
- Low RMSE and MAE across test sets

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 License

This project is open-source and available under the [MIT License](https://choosealicense.com/licenses/mit/)


## 👤 Author

- [Sheikh Rehan](https://sheikhrehan.com/)
- M. Jazib Khan
- Abdullah Amir

## 🙏 Acknowledgments

- EV market data providers
- Streamlit community
- scikit-learn contributors
