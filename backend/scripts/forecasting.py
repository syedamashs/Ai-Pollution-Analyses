#!/usr/bin/env python3
"""AQI forecasting using a single fast statistical model."""

from datetime import datetime, timedelta
import warnings

import numpy as np
import pandas as pd

warnings.filterwarnings('ignore')

try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
except ImportError:
    ExponentialSmoothing = None


class AQIForcaster:
    """Fast AQI forecasting based on historical trend and weekly seasonality."""

    def __init__(self, historical_data=None):
        self.historical_data = list(historical_data or [])
        self.predictions = {}
        self.forecast_dates = []
        self.model_name = 'Holt-Winters Exponential Smoothing'
        self.model_color = '#0f766e'

    def generate_synthetic_data(self, days=100):
        """Generate a realistic AQI series for testing or fallback use."""
        np.random.seed(42)
        t = np.arange(days)
        base = 95 + 12 * np.sin(2 * np.pi * t / 7) + 0.4 * t
        noise = np.random.normal(0, 6.0, days)
        data = np.clip(base + noise, 0, 500)
        self.historical_data = [round(float(value), 2) for value in data]
        return self.historical_data

    def prepare_forecast_dates(self, forecast_days=7):
        last_date = datetime.now()
        self.forecast_dates = [
            (last_date + timedelta(days=offset)).strftime('%Y-%m-%d')
            for offset in range(1, forecast_days + 1)
        ]
        return self.forecast_dates

    def _clean_history(self):
        series = pd.Series(self.historical_data, dtype='float64').dropna()
        if series.empty:
            return series
        return series.clip(lower=0, upper=500)

    def forecast(self, forecast_days=7):
        series = self._clean_history()

        if len(series) == 0:
            predictions = [2.0] * forecast_days
        elif len(series) < 4 or ExponentialSmoothing is None:
            last_value = float(series.iloc[-1])
            predictions = [last_value] * forecast_days
        else:
            try:
                use_seasonal = len(series) >= 14
                model = ExponentialSmoothing(
                    series,
                    trend='add',
                    seasonal='add' if use_seasonal else None,
                    seasonal_periods=7 if use_seasonal else None,
                    initialization_method='estimated',
                )
                fitted = model.fit(optimized=True)
                predictions = fitted.forecast(forecast_days).tolist()
            except Exception as error:
                print(f"⚠️ Forecast Error: {error}")
                last_value = float(series.iloc[-1])
                predictions = [last_value] * forecast_days

        cleaned_predictions = np.clip(np.array(predictions, dtype=float), 0, 500).round(2)
        self.predictions['holt_winters'] = cleaned_predictions.tolist()
        return self.predictions['holt_winters']

    def forecast_lstm(self, forecast_days=7, lookback=14):
        return self.forecast(forecast_days)

    def forecast_arima(self, forecast_days=7, order=(1, 1, 1)):
        return self.forecast(forecast_days)

    def forecast_prophet(self, forecast_days=7):
        return self.forecast(forecast_days)

    def ensemble_forecast(self, forecast_days=7):
        predictions = self.forecast(forecast_days)
        return {
            'dates': self.prepare_forecast_dates(forecast_days),
            'holt_winters': predictions,
        }

    def get_forecast_summary(self, forecast_days=7):
        series = self._clean_history()
        predictions = self.forecast(forecast_days)
        current_aqi = round(float(series.iloc[-1]), 1) if len(series) else 0.0
        forecast_average = round(float(np.mean(predictions)), 1) if predictions else 0.0
        forecast_min = round(float(np.min(predictions)), 1) if predictions else 0.0
        forecast_max = round(float(np.max(predictions)), 1) if predictions else 0.0

        if predictions and len(series):
            if predictions[-1] > current_aqi + 0.05:
                trend = 'up'
            elif predictions[-1] < current_aqi - 0.05:
                trend = 'down'
            else:
                trend = 'flat'
        else:
            trend = 'flat'

        return {
            'forecast_dates': self.prepare_forecast_dates(forecast_days),
            'model': {
                'name': self.model_name,
                'values': predictions,
                'color': self.model_color,
            },
            'statistics': {
                'current_aqi': current_aqi,
                'forecast_avg': forecast_average,
                'forecast_min': forecast_min,
                'forecast_max': forecast_max,
                'trend': trend,
            },
        }


def get_aqi_forecaster():
    """Factory function to get AQI forecaster instance."""
    return AQIForcaster()


if __name__ == '__main__':
    print('🔮 Testing AQI Forecaster...')
    forecaster = AQIForcaster()
    forecaster.generate_synthetic_data(50)
    summary = forecaster.get_forecast_summary(forecast_days=7)

    print('\n📊 Forecast Summary:')
    print(f"  Current AQI: {summary['statistics']['current_aqi']}")
    print(f"  Forecast Average: {summary['statistics']['forecast_avg']}")
    print(f"  Range: {summary['statistics']['forecast_min']} - {summary['statistics']['forecast_max']}")
    print(f"  Trend: {summary['statistics']['trend']}")

    print('\n📈 Model Predictions:')
    for date, value in zip(summary['forecast_dates'], summary['model']['values']):
        print(f'  {date}: {value:.1f}')
