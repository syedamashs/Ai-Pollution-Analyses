#!/usr/bin/env python3
"""AQI Forecasting using LSTM, ARIMA, and Prophet models"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_squared_error, mean_absolute_error
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam

try:
    from statsmodels.tsa.arima.model import ARIMA
except ImportError:
    ARIMA = None

try:
    from prophet import Prophet
except ImportError:
    Prophet = None


class AQIForcaster:
    """Multi-model AQI forecasting system"""
    
    def __init__(self, historical_data=None):
        """
        Initialize forecaster with historical AQI data
        
        Args:
            historical_data: List of AQI values (14+ days minimum)
        """
        self.historical_data = historical_data or []
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.predictions = {}
        self.forecast_dates = []
        
    def generate_synthetic_data(self, days=30):
        """Generate realistic synthetic AQI data for testing"""
        np.random.seed(42)
        # Simulate realistic AQI with trend and seasonality
        t = np.arange(days)
        trend = 50 + 0.2 * t
        seasonality = 15 * np.sin(2 * np.pi * t / 7)
        noise = np.random.normal(0, 5, days)
        data = trend + seasonality + noise
        self.historical_data = np.clip(data, 10, 300).tolist()
        return self.historical_data
    
    def prepare_forecast_dates(self, forecast_days=7):
        """Generate forecast dates"""
        last_date = datetime.now()
        self.forecast_dates = [
            (last_date + timedelta(days=i)).strftime('%Y-%m-%d')
            for i in range(1, forecast_days + 1)
        ]
        return self.forecast_dates
    
    # ==================== LSTM FORECASTING ====================
    def forecast_lstm(self, forecast_days=7, lookback=14):
        """
        LSTM-based AQI forecasting
        
        Args:
            forecast_days: Number of days to forecast
            lookback: Number of historical days to use for training
            
        Returns:
            List of predicted AQI values
        """
        if len(self.historical_data) < lookback:
            return [self.historical_data[-1]] * forecast_days
        
        try:
            data = np.array(self.historical_data).reshape(-1, 1)
            scaled_data = self.scaler.fit_transform(data)
            
            # Prepare training data
            X_train, y_train = [], []
            for i in range(len(scaled_data) - lookback):
                X_train.append(scaled_data[i:i+lookback])
                y_train.append(scaled_data[i+lookback])
            
            X_train = np.array(X_train)
            y_train = np.array(y_train)
            
            if len(X_train) == 0:
                return [self.historical_data[-1]] * forecast_days
            
            # Build LSTM model
            model = Sequential([
                LSTM(50, activation='relu', input_shape=(lookback, 1)),
                Dropout(0.2),
                Dense(25, activation='relu'),
                Dense(1)
            ])
            model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
            
            # Train with minimal epochs for speed
            model.fit(X_train, y_train, epochs=50, batch_size=4, verbose=0)
            
            # Generate forecast
            last_sequence = scaled_data[-lookback:].reshape(1, lookback, 1)
            predictions = []
            
            for _ in range(forecast_days):
                pred = model.predict(last_sequence, verbose=0)
                predictions.append(pred[0, 0])
                # Update sequence for next prediction
                last_sequence = np.append(last_sequence[:, 1:, :], 
                                        np.array([[[pred[0, 0]]]]), axis=1)
            
            # Inverse scaling
            predictions = np.array(predictions).reshape(-1, 1)
            final_predictions = self.scaler.inverse_transform(predictions).flatten()
            
            self.predictions['lstm'] = np.clip(final_predictions, 0, 500).tolist()
            return self.predictions['lstm']
            
        except Exception as e:
            print(f"⚠️ LSTM Error: {e}")
            return [self.historical_data[-1]] * forecast_days
    
    # ==================== ARIMA FORECASTING ====================
    def forecast_arima(self, forecast_days=7, order=(1, 1, 1)):
        """
        ARIMA-based AQI forecasting
        
        Args:
            forecast_days: Number of days to forecast
            order: (p, d, q) ARIMA parameters
            
        Returns:
            List of predicted AQI values
        """
        if ARIMA is None:
            print("⚠️ statsmodels not installed, using fallback")
            return [self.historical_data[-1]] * forecast_days
        
        try:
            # Fit ARIMA model
            model = ARIMA(self.historical_data, order=order)
            result = model.fit()
            
            # Forecast
            forecast = result.get_forecast(steps=forecast_days)
            predictions = forecast.predicted_mean.values
            
            self.predictions['arima'] = np.clip(predictions, 0, 500).tolist()
            return self.predictions['arima']
            
        except Exception as e:
            print(f"⚠️ ARIMA Error: {e}")
            return [self.historical_data[-1]] * forecast_days
    
    # ==================== PROPHET FORECASTING ====================
    def forecast_prophet(self, forecast_days=7):
        """
        Facebook Prophet-based AQI forecasting
        
        Args:
            forecast_days: Number of days to forecast
            
        Returns:
            List of predicted AQI values
        """
        if Prophet is None:
            print("⚠️ Prophet not installed, using fallback")
            return [self.historical_data[-1]] * forecast_days
        
        try:
            # Prepare data for Prophet
            dates = pd.date_range(end=datetime.now(), periods=len(self.historical_data), freq='D')
            df = pd.DataFrame({
                'ds': dates,
                'y': self.historical_data
            })
            
            # Fit Prophet model
            model = Prophet(
                yearly_seasonality=False,
                weekly_seasonality=True,
                daily_seasonality=False,
                interval_width=0.95,
                changepoint_prior_scale=0.05
            )
            model.fit(df)
            
            # Create future dataframe
            future = model.make_future_dataframe(periods=forecast_days)
            forecast = model.predict(future)
            
            # Extract predictions
            predictions = forecast[-forecast_days:]['yhat'].values
            
            self.predictions['prophet'] = np.clip(predictions, 0, 500).tolist()
            return self.predictions['prophet']
            
        except Exception as e:
            print(f"⚠️ Prophet Error: {e}")
            return [self.historical_data[-1]] * forecast_days
    
    # ==================== ENSEMBLE FORECAST ====================
    def ensemble_forecast(self, forecast_days=7):
        """
        Generate all three forecasts
        
        Returns:
            Dict with all predictions
        """
        self.prepare_forecast_dates(forecast_days)
        
        predictions = {
            'dates': self.forecast_dates,
            'lstm': self.forecast_lstm(forecast_days),
            'arima': self.forecast_arima(forecast_days),
            'prophet': self.forecast_prophet(forecast_days),
        }
        
        # Calculate ensemble (average of all models)
        ensemble = np.mean([
            predictions['lstm'],
            predictions['arima'],
            predictions['prophet']
        ], axis=0)
        
        predictions['ensemble'] = np.clip(ensemble, 0, 500).tolist()
        
        return predictions
    
    def get_forecast_summary(self, forecast_days=7):
        """Get detailed forecast summary with confidence intervals"""
        predictions = self.ensemble_forecast(forecast_days)
        
        summary = {
            'forecast_dates': predictions['dates'],
            'models': {
                'lstm': {
                    'name': 'LSTM (Neural Network)',
                    'values': predictions['lstm'],
                    'color': '#3b82f6'
                },
                'arima': {
                    'name': 'ARIMA (Statistical)',
                    'values': predictions['arima'],
                    'color': '#ef4444'
                },
                'prophet': {
                    'name': 'Prophet (Meta)',
                    'values': predictions['prophet'],
                    'color': '#10b981'
                },
                'ensemble': {
                    'name': 'Ensemble Average',
                    'values': predictions['ensemble'],
                    'color': '#f59e0b',
                    'lineStyle': 'dashed'
                }
            },
            'statistics': {
                'current_aqi': round(self.historical_data[-1], 1) if self.historical_data else 0,
                'forecast_avg': round(np.mean(predictions['ensemble']), 1),
                'forecast_min': round(np.min(predictions['ensemble']), 1),
                'forecast_max': round(np.max(predictions['ensemble']), 1),
                'trend': 'up' if predictions['ensemble'][-1] > self.historical_data[-1] else 'down'
            }
        }
        
        return summary


def get_aqi_forecaster():
    """Factory function to get AQI forecaster instance"""
    return AQIForcaster()


if __name__ == '__main__':
    # Test the forecaster
    print("🔮 Testing AQI Forecaster...")
    
    forecaster = AQIForcaster()
    forecaster.generate_synthetic_data(30)
    
    summary = forecaster.get_forecast_summary(forecast_days=7)
    
    print("\n📊 Forecast Summary:")
    print(f"  Current AQI: {summary['statistics']['current_aqi']}")
    print(f"  Forecast Average: {summary['statistics']['forecast_avg']}")
    print(f"  Range: {summary['statistics']['forecast_min']} - {summary['statistics']['forecast_max']}")
    print(f"  Trend: {summary['statistics']['trend']}")
    
    print("\n📈 Model Predictions:")
    for date, lstm, arima, prophet in zip(
        summary['forecast_dates'],
        summary['models']['lstm']['values'],
        summary['models']['arima']['values'],
        summary['models']['prophet']['values']
    ):
        print(f"  {date}: LSTM={lstm:.1f} | ARIMA={arima:.1f} | Prophet={prophet:.1f}")
