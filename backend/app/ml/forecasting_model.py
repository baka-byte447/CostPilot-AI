from prophet import Prophet
from app.ml.data_loader import load_metrics_dataframe

def train_cpu_forecast_model(db):
    df = load_metrics_dataframe(db)
    if len(df) <20:
        return {"error": "Data collected is not enough yet"}
    
    prophet_df = df.rename(columns={
        "timestamp":"ds",
        "cpu_usage" : "y"
    })

    model = Prophet()
    model.fit(prophet_df)
    
    future= model.make_future_dataframe(
        periods = 6,
        freq="5min"
    )

    forecast = model.predict(future)
    predictions = forecast[["ds", "yhat"]].tail(6)

    results = []

    for i, row in predictions.iterrows():
        results.append({
            "timestamp": str(row["ds"]),
            "predicted_cpu": float(row["yhat"])
        })



    return results