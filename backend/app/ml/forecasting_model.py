from prophet import Prophet
from app.ml.data_loader import load_metrics_dataframe


def forecast_metric(df, column):
    prophet_df = df[["timestamp", column]].rename(
        columns={
            "timestamp": "ds",
            column: "y"
        })

    model =Prophet()
    model.fit(prophet_df)
    future = model.make_future_dataframe(periods=6,freq="5min")

    forecast = model.predict(future)
    predictions = forecast[["ds", "yhat"]].tail(6)
    results = []

    for i, row in predictions.iterrows():
        results.append({
            "timestamp": str(row["ds"]),
            "prediction": float(row["yhat"])
        })

    return results




def forecast_system_metrics(db):

    df = load_metrics_dataframe(db)

    if len(df)<20:
        return {"error": "Not enough data collected yet"}

    cpu_forecast = forecast_metric(df, "cpu_usage")
    memory_forecast = forecast_metric(df, "memory_usage")
    request_forecast = forecast_metric(df, "request_load")
    return {
        "cpu_forecast": cpu_forecast,
        "memory_forecast": memory_forecast,
        "request_forecast": request_forecast}